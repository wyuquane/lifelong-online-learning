"""Tests for dataset loading and stream preparation."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

from aklo.config import ROOT, load_config
from aklo.data import load_dataset
from aklo.data.stream import prepare_stream
from aklo.data.synthetic import make_synthetic
from aklo.experiments import build_specs


def test_prepare_stream_is_deterministic() -> None:
    stream = make_synthetic("syn1", n_tasks=8, n_samples=12, seed=0)
    first = prepare_stream(stream, seed=4)
    second = prepare_stream(stream, seed=4)
    assert [task.task_id for task in first.tasks] == [
        task.task_id for task in second.tasks
    ]
    for left, right in zip(first.tasks, second.tasks):
        np.testing.assert_array_equal(left.X_train, right.X_train)
        np.testing.assert_array_equal(left.y_train, right.y_train)


def test_prepare_stream_preserves_task_set() -> None:
    stream = make_synthetic("syn1", n_tasks=8, n_samples=12, seed=0)
    prepared = prepare_stream(stream, seed=4)
    assert sorted(task.task_id for task in prepared.tasks) == sorted(
        task.task_id for task in stream.tasks
    )
    assert [task.task_id for task in prepared.tasks] != [
        task.task_id for task in stream.tasks
    ]


def test_prepare_stream_does_not_mutate_input() -> None:
    stream = make_synthetic("syn1", n_tasks=2, n_samples=10, seed=0)
    original = stream.tasks[0].X_train.copy()
    prepare_stream(stream, seed=3)
    np.testing.assert_array_equal(stream.tasks[0].X_train, original)


def test_landmine_loader() -> None:
    path = Path("data/landmine-detection.csv")
    if not path.exists():
        pytest.skip("landmine data not available")
    config = {
        "kind": "landmine",
        "path": str(path),
        "n_samples": 150,
    }
    stream = load_dataset("landmine", config, seed=0)
    assert len(stream) == 29
    assert stream.task_type == "classification"
    assert stream.n_features == 9
    for task in stream.tasks:
        assert task.n_train == 150
        assert set(np.unique(task.y_train)) <= {-1.0, 1.0}


def test_landmine_loader_with_held_out_split() -> None:
    path = Path("data/landmine-detection.csv")
    if not path.exists():
        pytest.skip("landmine data not available")
    config = {
        "kind": "landmine",
        "path": str(path),
        "n_samples": 150,
        "test_fraction": 0.2,
    }
    stream = load_dataset("landmine", config, seed=0)
    for task in stream.tasks:
        assert task.X_train.shape[0] == task.y_train.shape[0] == 120
        assert task.X_test.shape[0] == task.y_test.shape[0] == 30


def test_spam_loader() -> None:
    path = Path("data/spam-detection.npz")
    if not path.exists():
        pytest.skip("spam data not available")
    config = {
        "kind": "spam",
        "path": str(path),
        "n_samples": 200,
        "n_users": 15,
    }
    stream = load_dataset("spam", config, seed=0)
    assert len(stream) == 15
    assert stream.task_type == "classification"
    assert stream.n_features == 152543
    for task in stream.tasks:
        assert task.n_train == 200
        assert sparse.issparse(task.X_train)


def test_spam_loader_with_held_out_split() -> None:
    path = Path("data/spam-detection.npz")
    if not path.exists():
        pytest.skip("spam data not available")
    config = {
        "kind": "spam",
        "path": str(path),
        "n_samples": 200,
        "n_users": 15,
        "test_fraction": 0.2,
    }
    stream = load_dataset("spam", config, seed=0)
    for task in stream.tasks:
        assert task.X_train.shape[0] == task.y_train.shape[0] == 160
        assert task.X_test.shape[0] == task.y_test.shape[0] == 40
        assert sparse.issparse(task.X_train)
        assert sparse.issparse(task.X_test)


def test_london_loader() -> None:
    path = Path("data/london-school/ILEA567.DAT")
    if not path.exists():
        pytest.skip("london data not available")
    config = {"kind": "london", "path": str(path)}
    stream = load_dataset("london", config, seed=0)
    assert len(stream) == 139
    assert stream.task_type == "regression"
    assert stream.n_features == 28
    assert all(task.n_train > 0 for task in stream.tasks)
    # The last feature is the bias column.
    np.testing.assert_allclose(stream.tasks[0].X_train[:, -1], 1.0)


def test_synthetic_loader_uses_config() -> None:
    config = {
        "kind": "synthetic",
        "task_type": "classification",
        "n_tasks": 5,
        "n_samples": 10,
    }
    stream = load_dataset("syn1", config, seed=0)
    assert len(stream) == 5
    assert all(task.n_train == 10 for task in stream.tasks)


def test_e3_train_and_test_sizes_match_paper() -> None:
    """E3 keeps the paper's train size and uses a separate test set."""
    config = load_config(
        ROOT / "configs" / "experiments" / "e3_catastrophic-forgetting.yaml"
    )
    specs = build_specs(config)
    expected_train = {
        "syn1": 100,
        "syn2": 100,
        "syn3": 100,
        "syn4": 100,
        "landmine": 150,
        "spam": 200,
    }
    for dataset, n_train in expected_train.items():
        spec = next(
            item for item in specs if item.dataset == dataset and item.method == "aklo"
        )
        data_config = deepcopy(config["datasets"][dataset])
        data_config.update(spec.data_overrides)
        data_config["test_fraction"] = spec.test_fraction
        stream = load_dataset(
            dataset, data_config, spec.data_seed, root=ROOT
        )
        for task in stream.tasks:
            assert task.n_train == n_train
            assert task.X_test is not None and task.y_test is not None
        if dataset.startswith("syn"):
            assert all(len(task.y_test) == 100 for task in stream.tasks)
        if dataset == "spam":
            assert all(len(task.y_test) == 200 for task in stream.tasks)


def test_e3_landmine_and_spam_test_sets_are_all_remaining_rows() -> None:
    config = load_config(
        ROOT / "configs" / "experiments" / "e3_catastrophic-forgetting.yaml"
    )
    specs = build_specs(config)

    landmine_spec = next(
        item for item in specs if item.dataset == "landmine" and item.method == "aklo"
    )
    landmine_config = deepcopy(config["datasets"]["landmine"])
    landmine_config.update(landmine_spec.data_overrides)
    landmine_config["test_fraction"] = landmine_spec.test_fraction
    landmine = load_dataset(
        "landmine", landmine_config, landmine_spec.data_seed, root=ROOT
    )
    import pandas as pd

    frame = pd.read_csv(ROOT / "data" / "landmine-detection.csv")
    group_sizes = frame.groupby("task_id").size().to_dict()
    for task in landmine.tasks:
        task_number = int(task.task_id.split("_")[-1])
        assert task.n_train + len(task.y_test) == group_sizes[task_number]

    spam_spec = next(
        item for item in specs if item.dataset == "spam" and item.method == "aklo"
    )
    spam_config = deepcopy(config["datasets"]["spam"])
    spam_config.update(spam_spec.data_overrides)
    spam_config["test_fraction"] = spam_spec.test_fraction
    spam = load_dataset("spam", spam_config, spam_spec.data_seed, root=ROOT)
    for task in spam.tasks:
        assert task.n_train == 200
        assert len(task.y_test) == 200


def test_e3_london_split_is_per_school() -> None:
    config = load_config(
        ROOT / "configs" / "experiments" / "e3_catastrophic-forgetting.yaml"
    )
    specs = build_specs(config)
    spec = next(
        item for item in specs if item.dataset == "london" and item.method == "aklo"
    )
    data_config = deepcopy(config["datasets"]["london"])
    data_config["test_fraction"] = spec.test_fraction
    stream = load_dataset("london", data_config, spec.data_seed, root=ROOT)
    assert len(stream.tasks) == 139
    for task in stream.tasks:
        assert task.n_train > 0
        assert task.X_test is not None and task.y_test is not None
        assert len(task.y_test) >= 1
        total = task.n_train + len(task.y_test)
        assert abs(len(task.y_test) / total - 0.2) <= 0.02


def test_e3_data_is_fixed_across_repetitions() -> None:
    """Only task/example order changes across the ten repetitions."""
    config = load_config(
        ROOT / "configs" / "experiments" / "e3_catastrophic-forgetting.yaml"
    )
    specs = build_specs(config)
    first = next(
        item
        for item in specs
        if item.dataset == "syn1" and item.method == "aklo" and item.seed == 0
    )
    second = next(
        item
        for item in specs
        if item.dataset == "syn1" and item.method == "aklo" and item.seed == 1
    )
    data_config = deepcopy(config["datasets"]["syn1"])
    data_config.update(first.data_overrides)
    stream_a = load_dataset(
        "syn1", data_config, first.data_seed, root=ROOT
    )
    stream_b = load_dataset(
        "syn1", data_config, second.data_seed, root=ROOT
    )
    np.testing.assert_array_equal(
        stream_a.tasks[0].X_train, stream_b.tasks[0].X_train
    )
    np.testing.assert_array_equal(
        stream_a.tasks[0].X_test, stream_b.tasks[0].X_test
    )
