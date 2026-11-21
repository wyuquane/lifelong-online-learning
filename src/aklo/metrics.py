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
        """Add one prediction to the running average cumulative error.

        Classification errors are 0/1 after thresholding at zero; regression
        errors are absolute residuals.

        Parameters
        ----------
        y_true : float
            Ground-truth label or target.
        y_pred : float
            Raw model prediction.

        Returns
        -------
        None
            The running total and count are updated in place.

        Raises
        ------
        ValueError
            If ``task_type`` is neither ``"classification"`` nor
            ``"regression"``.
        """
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
        """Return the mean error observed so far (0 when empty)."""
        return self.total / self.n if self.n else 0.0


@dataclass
class ForgettingTracker:
    """Pooled ACE over the test sets of all previously seen tasks."""

    task_type: str
    total: float = 0.0
    n: int = 0
    per_task: dict[str, float] = field(default_factory=dict)

    def add_task(self, task_id: str, y_true: np.ndarray, y_pred: np.ndarray) -> None:
        """Evaluate one task's test set and add it to the pooled error.

        Parameters
        ----------
        task_id : str
            Identifier used as the key in ``per_task``.
        y_true : np.ndarray
            Ground-truth labels or targets for the task.
        y_pred : np.ndarray
            Model predictions aligned with ``y_true``.

        Returns
        -------
        None
            ``per_task``, ``total``, and ``n`` are updated in place.
        """
        tracker = ACETracker(self.task_type)
        for truth, prediction in zip(np.asarray(y_true).ravel(), np.asarray(y_pred).ravel()):
            tracker.update(float(truth), float(prediction))
        self.per_task[task_id] = tracker.value
        self.total += tracker.total
        self.n += tracker.n

    @property
    def value(self) -> float:
        """Return the pooled error over all evaluated tasks."""
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
