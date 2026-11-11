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
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=n_test, random_state=seed, stratify=stratify
        )
    except ValueError:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=n_test, random_state=seed
        )
    return X_train, y_train, X_test, y_test


def load_landmine(
    path: str | Path,
    n_samples: int = 150,
    seed: int = 0,
    test_fraction: float = 0.0,
    n_test: int = 0,
) -> TaskStream:
    """Load the landmine CSV and build one task per geographical region.

    The paper samples 150 training examples per task.  ``n_test=-1`` puts every
    row that is not used for training into the test set, which is the E3
    catastrophic-forgetting protocol.  A positive ``n_test`` draws a disjoint
    test block of that size.  ``n_test=0`` keeps the earlier behaviour, where
    ``test_fraction`` optionally splits the sampled rows.
    """
    frame = pd.read_csv(path)
    feature_cols = [c for c in frame.columns if c.startswith("feature_")]
    tasks: list[TaskData] = []

    for task_index, (task_id, group) in enumerate(
        sorted(frame.groupby("task_id"), key=lambda item: int(item[0]))
    ):
        rng = np.random.default_rng(seed + 1_000 + task_index)
        total = len(group)
        if n_test < 0:
            # Keep the training block at the paper's size and use every
            # remaining row as the held-out test set.
            train_size = min(n_samples, total)
            order = rng.permutation(total)
            train_indices = order[:train_size]
            test_indices = order[train_size:]
        elif n_test > 0:
            wanted = min(n_samples + n_test, total)
            order = rng.choice(total, size=wanted, replace=False)
            train_size = min(n_samples, max(wanted - 1, 0))
            train_indices = order[:train_size]
            test_indices = order[train_size:]
        else:
            train_size = min(n_samples, total)
            train_indices = rng.choice(total, size=train_size, replace=False)
            test_indices = None

        train_group = group.iloc[train_indices]
        X_train = train_group[feature_cols].to_numpy(dtype=np.float64)
        y_train = np.where(train_group["label"].to_numpy() == 1, 1.0, -1.0)
        if test_indices is not None:
            test_group = group.iloc[test_indices]
            X_test = test_group[feature_cols].to_numpy(dtype=np.float64)
            y_test = np.where(test_group["label"].to_numpy() == 1, 1.0, -1.0)
        else:
            X_test, y_test = None, None
            X_train, y_train, X_test, y_test = _split(
                X_train, y_train, test_fraction, seed + task_index
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
