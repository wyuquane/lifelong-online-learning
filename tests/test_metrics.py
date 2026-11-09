"""Tests for the metrics used by the reproduction."""

from __future__ import annotations

import math

import numpy as np

from aklo.metrics import ACETracker, ForgettingTracker, classify, entropy, macro_average


def test_sign_convention() -> None:
    assert classify(0.0) == 1.0
    assert classify(0.1) == 1.0
    assert classify(-0.1) == -1.0


def test_classification_ace() -> None:
    tracker = ACETracker("classification")
    for truth, prediction in [(1.0, 0.5), (-1.0, 0.5), (1.0, -0.5)]:
        tracker.update(truth, prediction)
    assert tracker.n == 3
    assert tracker.total == 2.0
    assert tracker.value == 2.0 / 3.0


def test_regression_ace() -> None:
    tracker = ACETracker("regression")
    tracker.update(3.0, 1.0)
    tracker.update(-1.0, 0.0)
    assert tracker.total == 3.0
    assert tracker.value == 1.5


def test_unknown_task_type() -> None:
    tracker = ACETracker("ranking")
    try:
        tracker.update(1.0, 1.0)
    except ValueError as error:
        assert "ranking" in str(error)
    else:  # pragma: no cover
        raise AssertionError("Expected ValueError")


def test_forgetting_tracker_pools_tasks() -> None:
    tracker = ForgettingTracker("classification")
    tracker.add_task("a", np.array([1.0, 1.0]), np.array([1.0, -1.0]))
    tracker.add_task("b", np.array([-1.0]), np.array([-1.0]))
    assert tracker.per_task == {"a": 0.5, "b": 0.0}
    assert tracker.value == 1.0 / 3.0


def test_entropy_and_macro_average() -> None:
    assert entropy(np.array([1.0, 0.0])) == 0.0
    assert math.isclose(entropy(np.array([0.5, 0.5])), math.log(2.0))
    assert macro_average([1.0, 2.0, 3.0]) == 2.0
    assert math.isnan(macro_average([]))
