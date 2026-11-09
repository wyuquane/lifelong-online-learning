"""Metrics used by the reproduction."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np


def classify(raw_prediction: float) -> float:
    """Convert a real-valued prediction to a binary label.

    The paper uses ``sign(w^T x)``. We follow the convention chosen for the
    reproduction: ``sign(0) = +1``.
    """
    return 1.0 if raw_prediction >= 0.0 else -1.0


@dataclass
class ACETracker:
    """Online average cumulative error tracker.

    Classification errors are 0/1; regression errors are absolute.
    """

    task_type: str
    total: float = 0.0
    n: int = 0

    def update(self, y_true: float, y_pred: float) -> None:
        if self.task_type == "classification":
            error = 0.0 if classify(y_pred) == float(y_true) else 1.0
        elif self.task_type == "regression":
            error = abs(float(y_pred) - float(y_true))
        else:
            raise ValueError(f"Unknown task type: {self.task_type}")
        self.total += error
        self.n += 1

    @property
    def value(self) -> float:
        return self.total / self.n if self.n else 0.0


@dataclass
class ForgettingTracker:
    """Pooled ACE over the test sets of all previously seen tasks."""

    task_type: str
    total: float = 0.0
    n: int = 0
    per_task: dict[str, float] = field(default_factory=dict)

    def add_task(self, task_id: str, y_true: np.ndarray, y_pred: np.ndarray) -> None:
        tracker = ACETracker(self.task_type)
        for truth, prediction in zip(np.asarray(y_true).ravel(), np.asarray(y_pred).ravel()):
            tracker.update(float(truth), float(prediction))
        self.per_task[task_id] = tracker.value
        self.total += tracker.total
        self.n += tracker.n

    @property
    def value(self) -> float:
        return self.total / self.n if self.n else 0.0


def entropy(probabilities: np.ndarray) -> float:
    """Shannon entropy of a probability vector."""
    probabilities = np.asarray(probabilities, dtype=np.float64)
    probabilities = probabilities[probabilities > 0]
    if probabilities.size == 0:
        return 0.0
    return float(-np.sum(probabilities * np.log(probabilities)))


def macro_average(values: list[float]) -> float:
    """Unweighted mean, matching the paper's task-level ACE."""
    return float(np.mean(values)) if values else math.nan
