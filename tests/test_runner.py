"""Tests for the common runner and local result persistence."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from aklo.config import load_yaml
from aklo.runner import (
    RunSpec,
    execute_run,
    make_smoke_stream,
    run_stream,
    to_jsonable,
)


def test_run_stream_classification(small_syn1, root) -> None:
    config = load_yaml(root / "configs" / "models" / "aklo.yaml")
    metrics, sample_log, summary, selected, all_models = run_stream(
        small_syn1, "aklo", config, seed=0, log_every=5
    )
    assert len(metrics) == len(small_syn1.tasks)
    assert sample_log
    assert summary["n_tasks"] == len(small_syn1.tasks)
    assert summary["n_samples"] == sum(task.n_train for task in small_syn1.tasks)
    assert 0.0 <= summary["final_cumulative_ace"] <= 1.0
    assert summary["train_seconds"] >= 0.0
    assert selected is None
    assert all_models is None


def test_run_stream_regression(small_syn3, root) -> None:
    config = load_yaml(root / "configs" / "models" / "aklo.yaml")
    metrics, _, summary, _, _ = run_stream(
        small_syn3, "aklo", config, seed=0, log_every=0
    )
    assert len(metrics) == len(small_syn3.tasks)
    assert summary["final_cumulative_ace"] >= 0.0


def test_run_stream_forgetting_diagnostics(root) -> None:
    from aklo.data.synthetic import make_synthetic
    from aklo.data.stream import prepare_stream

    stream = make_synthetic(
        "syn1", n_tasks=3, n_samples=30, seed=0, test_fraction=0.2
    )
    stream = prepare_stream(stream, seed=0)
    config = load_yaml(root / "configs" / "models" / "aklo.yaml")
    metrics, _, summary, _, _ = run_stream(
        stream, "aklo", config, seed=0, evaluate_forgetting=True, log_every=0
    )
    assert all(metrics_item.forgetting is not None for metrics_item in metrics)
    assert metrics[0].forgetting["current_task_mean"] >= 0.0
    assert summary["mean_current_test_ace"] is not None
    assert summary["mean_old_test_ace"] is not None
    assert summary["final_train_ace_task_mean"] is not None


def test_run_stream_training_sample_probe(small_syn1, root) -> None:
    config = load_yaml(root / "configs" / "models" / "aklo.yaml")
    metrics, _, summary, _, _ = run_stream(
        small_syn1,
        "aklo",
        config,
        seed=0,
        probe_fraction=0.2,
        log_every=0,
    )
    assert all(metrics_item.probe is not None for metrics_item in metrics)
    assert summary["probe_n_tasks"] == len(small_syn1.tasks)
    assert summary["probe_n_samples"] == sum(
        metrics_item.probe["n_samples"] for metrics_item in metrics
    )
    assert 0.0 <= summary["probe_ace_task_mean"] <= 1.0
    assert 0.0 <= summary["probe_ace_pooled"] <= 1.0


def test_task_predictor_is_available_for_all_methods(small_syn1, root) -> None:
    from aklo.models import build_model

    for method in ("itol", "tol", "unif_sum", "tranol", "otb", "aklo"):
        config = load_yaml(root / "configs" / "models" / f"{method}.yaml")
        model = build_model(
            method,
            small_syn1.n_features,
            small_syn1.task_type,
            config,
            seed=0,
        )
        for task_index, task in enumerate(small_syn1.tasks):
            model.start_task(
                task_index,
                task.n_train,
                task_id=task.task_id,
                category=task.category,
            )
            for index in range(task.n_train):
                row = task.X_train[index]
                model.update(row, float(task.y_train[index]))
            model.end_task()
            prediction = model.task_predictor().predict(task.X_train[0])
            assert np.isfinite(prediction)


def test_make_smoke_stream() -> None:
    from aklo.data.synthetic import make_synthetic

    stream = make_synthetic("syn1", n_tasks=5, n_samples=20, seed=0)
    smoke = make_smoke_stream(stream, n_tasks=2, n_samples=5)
    assert len(smoke) == 2
    assert all(task.n_train == 5 for task in smoke.tasks)


def test_execute_run_saves_json(small_syn1, root, tmp_path) -> None:
    config = load_yaml(root / "configs" / "models" / "aklo.yaml")
    data_config = {
        "kind": "synthetic",
        "task_type": "classification",
        "n_tasks": 2,
        "n_samples": 10,
    }
    spec = RunSpec(
        experiment="test_experiment",
        dataset="syn1",
        method="aklo",
        seed=0,
        run_name="test-run",
        group="test",
        data_config=data_config,
        model_config=config,
        test_fraction=0.0,
    )
    result = execute_run(
        spec,
        base={"runtime": {"log_every": 5}},
        root=tmp_path,
        wandb_enabled=False,
    )
    assert result is not None
    path = tmp_path / "results" / "test_experiment" / "test-run.json"
    assert path.exists()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["run_name"] == "test-run"
    assert payload["summary"]["n_tasks"] == 2
    assert payload["tasks"][0]["ace"] >= 0.0


def test_execute_run_skips_unsupported_task_type(root, tmp_path) -> None:
    data_config = {
        "kind": "synthetic",
        "task_type": "regression",
        "n_tasks": 2,
        "n_samples": 10,
    }
    spec = RunSpec(
        experiment="test_experiment",
        dataset="syn3",
        method="otb",
        seed=0,
        run_name="unsupported",
        group="test",
        data_config=data_config,
        model_config={"supported_task_types": ["classification"]},
    )
    assert (
        execute_run(
            spec,
            base={},
            root=tmp_path,
            wandb_enabled=False,
        )
        is None
    )


def test_to_jsonable() -> None:
    value = {
        "array": np.array([1, 2]),
        "scalar": np.float64(1.5),
        "path": Path("data"),
        "nan": float("nan"),
        "nested": [np.int64(3), {"inf": float("inf")}],
    }
    converted = to_jsonable(value)
    assert converted["array"] == [1, 2]
    assert converted["scalar"] == 1.5
    assert converted["path"] == "data"
    assert converted["nan"] is None
    assert converted["nested"] == [3, {"inf": None}]
