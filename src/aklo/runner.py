"""Common experiment runner.

A run is one ``(experiment, dataset, method, seed, overrides)`` combination.
The runner loads and shuffles the stream, trains the learner online, records
prequential ACE and optional post-task forgetting metrics, saves a JSON file,
and logs the run to Weights & Biases.

The timer used by the runtime experiment wraps only the per-sample prediction
and update loop.  Data loading, model construction, forgetting evaluation and
W&B logging are excluded from ``train_seconds``.
"""

from __future__ import annotations

import json
import math
import time
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import numpy as np
from scipy import sparse

from .data import load_dataset
from .data.base import TaskData, TaskStream
from .data.stream import prepare_stream
from .metrics import ACETracker
from .models import build_model
from .seeding import seed_everything
from .tracking import WandbLogger


# ---------------------------------------------------------------------------
# Run specification
# ---------------------------------------------------------------------------
@dataclass
class RunSpec:
    """Everything needed to execute one run."""

    experiment: str
    dataset: str
    method: str
    seed: int
    run_name: str
    group: str
    tags: list[str] = field(default_factory=list)
    data_config: dict[str, Any] = field(default_factory=dict)
    model_config: dict[str, Any] = field(default_factory=dict)
    data_overrides: dict[str, Any] = field(default_factory=dict)
    model_overrides: dict[str, Any] = field(default_factory=dict)
    test_fraction: float = 0.0
    evaluate_forgetting: bool = False
    log_selected_models: bool = False
    notes: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskMetrics:
    task_index: int
    task_id: str
    category: str | None
    n_samples: int
    ace: float
    cumulative_ace: float
    time_seconds: float
    state: dict[str, Any]
    forgetting: dict[str, float] | None = None


@dataclass
class RunResult:
    experiment: str
    dataset: str
    method: str
    seed: int
    run_name: str
    task_type: str
    n_features: int
    n_tasks: int
    tasks: list[TaskMetrics]
    sample_log: list[dict[str, float | int]]
    summary: dict[str, Any]
    config: dict[str, Any]
    selected_models: list[dict[str, Any]] | None = None
    all_models: list[dict[str, Any]] | None = None


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------
def to_jsonable(value: Any) -> Any:
    """Recursively convert NumPy and Path values to JSON/W&B-friendly types."""
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
    return value


def _row(X: Any, index: int) -> Any:
    if sparse.issparse(X):
        return X.getrow(index)
    return X[index]


def _slice_rows(X: Any, n: int) -> Any:
    return X[:n]


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------
def evaluate_tasks(
    model: Any,
    tasks: list[TaskData],
    task_type: str,
    include_current: str | None = None,
) -> dict[str, float]:
    """Evaluate a trained model on the held-out test sets of ``tasks``.

    Returns the task-averaged ACE (the paper's definition), the pooled ACE,
    and the mean over all tasks except ``include_current`` (used to separate
    old-task forgetting from the current task's test performance).
    """
    per_task: dict[str, float] = {}
    total_error = 0.0
    total_n = 0
    for task in tasks:
        if task.X_test is None or task.y_test is None:
            continue
        tracker = ACETracker(task_type)
        for index in range(len(task.y_test)):
            prediction = model.predict(_row(task.X_test, index))
            tracker.update(float(task.y_test[index]), prediction)
        per_task[task.task_id] = tracker.value
        total_error += tracker.total
        total_n += tracker.n

    if not per_task:
        return {
            "task_mean": float("nan"),
            "pooled": float("nan"),
            "old_tasks_mean": float("nan"),
            "current_task_mean": float("nan"),
            "n_test_tasks": 0,
            "n_test_samples": 0,
        }

    values = list(per_task.values())
    old_values = [
        value for task_id, value in per_task.items() if task_id != include_current
    ]
    current_value = per_task.get(include_current, float("nan")) if include_current else float("nan")
    return {
        "task_mean": float(np.mean(values)),
        "pooled": float(total_error / total_n) if total_n else float("nan"),
        "old_tasks_mean": float(np.mean(old_values)) if old_values else float("nan"),
        "current_task_mean": float(current_value),
        "n_test_tasks": len(per_task),
        "n_test_samples": int(total_n),
    }


def evaluate_train_tasks(
    model: Any,
    tasks: list[TaskData],
    task_type: str,
) -> dict[str, float]:
    """Evaluate a trained model on the training data of ``tasks``.

    This reproduces the alternative reading of Table 2 in which the paper
    re-feeds the samples of previous tasks after training. It is reported as a
    diagnostic only: the training samples were observed online, so this number
    is not a held-out estimate.
    """
    per_task: list[float] = []
    total_error = 0.0
    total_n = 0
    for task in tasks:
        tracker = ACETracker(task_type)
        for index in range(task.n_train):
            prediction = model.predict(_row(task.X_train, index))
            tracker.update(float(task.y_train[index]), prediction)
        per_task.append(tracker.value)
        total_error += tracker.total
        total_n += tracker.n
    return {
        "task_mean": float(np.mean(per_task)) if per_task else float("nan"),
        "pooled": float(total_error / total_n) if total_n else float("nan"),
        "n_tasks": len(per_task),
        "n_samples": int(total_n),
    }


# ---------------------------------------------------------------------------
# Core loop
# ---------------------------------------------------------------------------
def run_stream(
    stream: TaskStream,
    method: str,
    model_config: dict[str, Any],
    seed: int,
    model_overrides: dict[str, Any] | None = None,
    evaluate_forgetting: bool = False,
    log_every: int = 10,
    logger: WandbLogger | None = None,
    log_selected_models: bool = False,
    task_callback: Callable[[TaskMetrics], None] | None = None,
) -> tuple[
    list[TaskMetrics],
    list[dict[str, float | int]],
    dict[str, Any],
    list[dict[str, Any]] | None,
    list[dict[str, Any]] | None,
]:
    """Train one learner on one stream and return metrics."""
    model = build_model(
        method,
        stream.n_features,
        stream.task_type,
        model_config,
        seed=seed,
        overrides=model_overrides,
    )
    task_metrics: list[TaskMetrics] = []
    sample_log: list[dict[str, float | int]] = []
    total_error = 0.0
    total_n = 0
    global_sample = 0
    train_seconds = 0.0
    run_start = time.perf_counter()

    for task_index, task in enumerate(stream.tasks):
        model.start_task(
            task_index,
            task.n_train,
            task_id=task.task_id,
            category=task.category,
        )
        tracker = ACETracker(stream.task_type)
        task_start = time.perf_counter()
        for index in range(task.n_train):
            x = _row(task.X_train, index)
            y = float(task.y_train[index])
            prediction = model.predict(x)
            tracker.update(y, prediction)
            model.update(x, y)
            global_sample += 1
            if log_every > 0 and (
                global_sample % log_every == 0 or index == task.n_train - 1
            ):
                sample_log.append(
                    {
                        "sample": global_sample,
                        "task": task_index,
                        "running_ace": tracker.value,
                    }
                )
        task_time = time.perf_counter() - task_start
        train_seconds += task_time
        model.end_task()

        total_error += tracker.total
        total_n += tracker.n
        task_ace = tracker.value
        cumulative_ace = float(np.mean([m.ace for m in task_metrics] + [task_ace]))
        state = to_jsonable(model.state())

        forgetting = None
        if evaluate_forgetting:
            forgetting = evaluate_tasks(
                model,
                stream.tasks[: task_index + 1],
                stream.task_type,
                include_current=task.task_id,
            )

        metrics = TaskMetrics(
            task_index=task_index,
            task_id=task.task_id,
            category=task.category,
            n_samples=task.n_train,
            ace=float(task_ace),
            cumulative_ace=cumulative_ace,
            time_seconds=float(task_time),
            state=state,
            forgetting=forgetting,
        )
        task_metrics.append(metrics)
        if task_callback is not None:
            task_callback(metrics)
        if logger is not None:
            logger.log(_task_log_payload(metrics))

    total_seconds = time.perf_counter() - run_start
    final_state = task_metrics[-1].state if task_metrics else {}
    final_forgetting = task_metrics[-1].forgetting if task_metrics else None

    # Aggregate held-out forgetting diagnostics.  ``current_task_mean`` is the
    # test ACE of the task that was just trained, while ``old_tasks_mean`` is
    # the test ACE on all earlier tasks.  The paper's Table 2 is not explicit
    # about which of these it reports, so we keep both.
    mean_current_test_ace = None
    mean_old_test_ace = None
    if evaluate_forgetting:
        current_values = [
            metrics.forgetting["current_task_mean"]
            for metrics in task_metrics
            if metrics.forgetting is not None
            and not math.isnan(metrics.forgetting["current_task_mean"])
        ]
        old_values = [
            metrics.forgetting["old_tasks_mean"]
            for metrics in task_metrics
            if metrics.forgetting is not None
            and not math.isnan(metrics.forgetting["old_tasks_mean"])
        ]
        mean_current_test_ace = (
            float(np.mean(current_values)) if current_values else None
        )
        mean_old_test_ace = float(np.mean(old_values)) if old_values else None

    final_train = None
    if evaluate_forgetting:
        final_train = evaluate_train_tasks(model, stream.tasks, stream.task_type)

    summary = {
        "final_task_ace": task_metrics[-1].ace if task_metrics else None,
        "final_cumulative_ace": float(np.mean([m.ace for m in task_metrics]))
        if task_metrics
        else None,
        "pooled_ace": float(total_error / total_n) if total_n else None,
        "n_tasks": len(task_metrics),
        "n_samples": int(total_n),
        "n_features": int(stream.n_features),
        "train_seconds": float(train_seconds),
        "total_seconds": float(total_seconds),
        "seconds_per_task": float(train_seconds / len(task_metrics))
        if task_metrics
        else None,
        "seconds_per_sample": float(train_seconds / total_n) if total_n else None,
        "final_state": final_state,
        "forgetting_task_mean": final_forgetting["task_mean"]
        if final_forgetting
        else None,
        "forgetting_pooled": final_forgetting["pooled"]
        if final_forgetting
        else None,
        "forgetting_old_tasks_mean": final_forgetting["old_tasks_mean"]
        if final_forgetting
        else None,
        "mean_current_test_ace": mean_current_test_ace,
        "mean_old_test_ace": mean_old_test_ace,
        "final_train_ace_task_mean": final_train["task_mean"] if final_train else None,
        "final_train_ace_pooled": final_train["pooled"] if final_train else None,
    }

    selected_models = None
    all_models = None
    if log_selected_models:
        def _dump(snapshot: Any) -> dict[str, Any] | None:
            weights = np.asarray(snapshot.weights).ravel()
            if weights.size > 10_000:
                # Do not dump very high-dimensional models into JSON.
                return None
            return {
                "task_id": snapshot.task_id,
                "category": snapshot.category,
                "weights": weights.tolist(),
            }

        selected_models = [
            dumped
            for snapshot in model.selected_models()
            if (dumped := _dump(snapshot)) is not None
        ]
        all_snapshots = getattr(model, "knowledge_base", None)
        if all_snapshots is None:
            all_snapshots = getattr(model, "snapshots", [])
        all_models = [
            dumped
            for snapshot in all_snapshots
            if (dumped := _dump(snapshot)) is not None
        ]

    return task_metrics, sample_log, summary, selected_models, all_models


def _task_log_payload(metrics: TaskMetrics) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "task": metrics.task_index,
        "task/ace": metrics.ace,
        "task/cumulative_ace": metrics.cumulative_ace,
        "task/time_seconds": metrics.time_seconds,
        "task/n_samples": metrics.n_samples,
    }
    for key, value in metrics.state.items():
        payload[f"state/{key}"] = value
    if metrics.forgetting is not None:
        for key, value in metrics.forgetting.items():
            payload[f"forgetting/{key}"] = value
    return to_jsonable(payload)


# ---------------------------------------------------------------------------
# Smoke-test stream
# ---------------------------------------------------------------------------
def make_smoke_stream(stream: TaskStream, n_tasks: int, n_samples: int) -> TaskStream:
    """Truncate a stream to a few tasks and samples for a quick smoke test."""
    tasks: list[TaskData] = []
    for task in stream.tasks[:n_tasks]:
        n_train = min(n_samples, task.n_train)
        X_test = task.X_test
        y_test = task.y_test
        if X_test is not None and y_test is not None:
            n_test = min(n_samples, len(y_test))
            X_test = _slice_rows(X_test, n_test)
            y_test = y_test[:n_test]
        tasks.append(
            TaskData(
                task_id=task.task_id,
                X_train=_slice_rows(task.X_train, n_train),
                y_train=task.y_train[:n_train],
                X_test=X_test,
                y_test=y_test,
                category=task.category,
            )
        )
    return TaskStream(stream.name, stream.task_type, tasks)


# ---------------------------------------------------------------------------
# Run execution
# ---------------------------------------------------------------------------
def execute_run(
    spec: RunSpec,
    base: dict[str, Any],
    root: str | Path,
    wandb_enabled: bool = True,
    smoke: bool = False,
) -> RunResult | None:
    """Execute one run, save it locally, and log it to W&B."""
    supported = spec.model_config.get("supported_task_types")
    task_type = spec.data_config.get("task_type")
    if supported is not None and task_type not in supported:
        print(f"[skip] {spec.run_name}: {spec.method} does not support {task_type}")
        return None

    seed_everything(spec.seed)
    data_config = deepcopy(spec.data_config)
    data_config.update(spec.data_overrides)
    data_config["test_fraction"] = float(spec.test_fraction)

    stream = load_dataset(spec.dataset, data_config, spec.seed, root=root)
    stream = prepare_stream(stream, spec.seed)
    if smoke:
        runtime = base.get("runtime", {})
        stream = make_smoke_stream(
            stream,
            n_tasks=int(runtime.get("smoke_tasks", 2)),
            n_samples=int(runtime.get("smoke_samples", 5)),
        )

    run_name = _safe_name(spec.run_name + ("-smoke" if smoke else ""))
    logger = WandbLogger(
        config={
            "experiment": spec.experiment,
            "dataset": spec.dataset,
            "method": spec.method,
            "seed": spec.seed,
            "task_type": stream.task_type,
            "data_config": data_config,
            "model_config": spec.model_config,
            "data_overrides": spec.data_overrides,
            "model_overrides": spec.model_overrides,
            "test_fraction": spec.test_fraction,
            "evaluate_forgetting": spec.evaluate_forgetting,
            "smoke": smoke,
            "base": base,
        },
        run_name=run_name,
        group=spec.experiment,
        tags=[spec.dataset, spec.method, f"seed-{spec.seed}", *spec.tags],
        enabled=wandb_enabled,
    )
    logger.init()
    logger.define_metric("task/*", "task")
    logger.define_metric("sample/*", "sample")

    task_metrics, sample_log, summary, selected_models, all_models = run_stream(
        stream,
        spec.method,
        spec.model_config,
        spec.seed,
        model_overrides=spec.model_overrides,
        evaluate_forgetting=spec.evaluate_forgetting,
        log_every=int(base.get("runtime", {}).get("log_every", 10)),
        logger=logger,
        log_selected_models=spec.log_selected_models,
    )

    summary["wandb_url"] = logger.url
    result = RunResult(
        experiment=spec.experiment,
        dataset=spec.dataset,
        method=spec.method,
        seed=spec.seed,
        run_name=run_name,
        task_type=stream.task_type,
        n_features=int(stream.n_features),
        n_tasks=len(task_metrics),
        tasks=task_metrics,
        sample_log=sample_log,
        summary=to_jsonable(summary),
        config=to_jsonable(
            {
                "experiment": spec.experiment,
                "dataset": spec.dataset,
                "method": spec.method,
                "seed": spec.seed,
                "task_type": stream.task_type,
                "data_config": data_config,
                "model_config": spec.model_config,
                "data_overrides": spec.data_overrides,
                "model_overrides": spec.model_overrides,
                "test_fraction": spec.test_fraction,
                "evaluate_forgetting": spec.evaluate_forgetting,
                "smoke": smoke,
                "notes": spec.notes,
            }
        ),
        selected_models=to_jsonable(selected_models),
        all_models=to_jsonable(all_models),
    )

    # Sample-level metrics are logged after the run so that W&B overhead does
    # not contaminate the runtime measurement.
    for entry in sample_log:
        logger.log(
            {
                "sample": entry["sample"],
                "sample/running_ace": entry["running_ace"],
                "sample/task": entry["task"],
            }
        )
    logger.log_summary(result.summary)
    logger.finish()

    save_result(result, Path(root) / "results")
    return result


def _safe_name(name: str) -> str:
    """Make a run name safe for W&B and Windows file names."""
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.")
    return "".join(character if character in allowed else "-" for character in name)


def save_result(result: RunResult, results_dir: Path) -> Path:
    """Save one run as JSON under ``results/<experiment>/``."""
    directory = results_dir / result.experiment
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{result.run_name}.json"
    payload = {
        "experiment": result.experiment,
        "dataset": result.dataset,
        "method": result.method,
        "seed": result.seed,
        "run_name": result.run_name,
        "task_type": result.task_type,
        "n_features": result.n_features,
        "n_tasks": result.n_tasks,
        "summary": result.summary,
        "config": result.config,
        "tasks": [
            {
                "task_index": metrics.task_index,
                "task_id": metrics.task_id,
                "category": metrics.category,
                "n_samples": metrics.n_samples,
                "ace": metrics.ace,
                "cumulative_ace": metrics.cumulative_ace,
                "time_seconds": metrics.time_seconds,
                "state": metrics.state,
                "forgetting": metrics.forgetting,
            }
            for metrics in result.tasks
        ],
        "sample_log": result.sample_log,
        "selected_models": result.selected_models,
        "all_models": result.all_models,
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(to_jsonable(payload), handle, indent=2, ensure_ascii=False)
    return path
