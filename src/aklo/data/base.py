"""Common data structures used by all datasets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class TaskData:
    """One task in a lifelong stream.

    ``X_train`` and ``X_test`` may be dense NumPy arrays or SciPy CSR
    matrices. ``y_train`` and ``y_test`` are one-dimensional arrays.
    """

    task_id: str
    X_train: Any
    y_train: np.ndarray
    X_test: Any | None = None
    y_test: np.ndarray | None = None
    category: str | None = None

    def __post_init__(self) -> None:
        self.y_train = np.asarray(self.y_train).ravel()
        if self.y_test is not None:
            self.y_test = np.asarray(self.y_test).ravel()

    @property
    def n_train(self) -> int:
        return int(self.y_train.shape[0])

    @property
    def n_features(self) -> int:
        return int(self.X_train.shape[1])


@dataclass
class TaskStream:
    """A named sequence of tasks."""

    name: str
    task_type: str
    tasks: list[TaskData] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.tasks)

    def __iter__(self):
        return iter(self.tasks)

    @property
    def n_features(self) -> int:
        if not self.tasks:
            raise ValueError("Empty task stream")
        return self.tasks[0].n_features
