"""Landmine detection dataset (29 binary classification tasks)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from .base import TaskData, TaskStream


def _split(
    X: np.ndarray,
    y: np.ndarray,
    test_fraction: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None, np.ndarray | None]:
    if test_fraction <= 0 or len(y) < 2:
        return X, y, None, None
    n_test = max(1, int(round(len(y) * test_fraction)))
    if n_test >= len(y):
        n_test = len(y) - 1
    stratify = y if len(np.unique(y)) > 1 else None
    try:
        return train_test_split(
            X, y, test_size=n_test, random_state=seed, stratify=stratify
        )
    except ValueError:
        return train_test_split(X, y, test_size=n_test, random_state=seed)


def load_landmine(
    path: str | Path,
    n_samples: int = 150,
    seed: int = 0,
    test_fraction: float = 0.0,
) -> TaskStream:
    """Load the landmine CSV and build one task per geographical region.

    The paper samples 150 examples per task. The sample is redrawn for each
    repetition because the runner passes a different seed per repetition.
    """
    frame = pd.read_csv(path)
    feature_cols = [c for c in frame.columns if c.startswith("feature_")]
    tasks: list[TaskData] = []

    for task_index, (task_id, group) in enumerate(
        sorted(frame.groupby("task_id"), key=lambda item: int(item[0]))
    ):
        rng = np.random.default_rng(seed + 1_000 + task_index)
        take = min(n_samples, len(group))
        indices = rng.choice(len(group), size=take, replace=False)
        group = group.iloc[indices]
        X = group[feature_cols].to_numpy(dtype=np.float64)
        y = np.where(group["label"].to_numpy() == 1, 1.0, -1.0)
        X_train, y_train, X_test, y_test = _split(
            X, y, test_fraction, seed + task_index
        )
        tasks.append(
            TaskData(
                task_id=f"landmine_{int(task_id):02d}",
                X_train=X_train,
                y_train=y_train,
                X_test=X_test,
                y_test=y_test,
            )
        )

    return TaskStream(name="landmine", task_type="classification", tasks=tasks)
