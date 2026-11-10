"""Tests for dataset loading and stream preparation."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

from aklo.data import load_dataset
from aklo.data.stream import prepare_stream
from aklo.data.synthetic import make_synthetic


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
