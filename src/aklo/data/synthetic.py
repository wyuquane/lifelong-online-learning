"""Synthetic datasets syn1-syn4 from Section 6.1 of the paper."""

from __future__ import annotations

import numpy as np
from sklearn.model_selection import train_test_split

from .base import TaskData, TaskStream


def _split(
    X: np.ndarray,
    y: np.ndarray,
    test_fraction: float,
    seed: int,
    task_type: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None, np.ndarray | None]:
    if test_fraction <= 0 or len(y) < 2:
        return X, y, None, None
    n_test = max(1, int(round(len(y) * test_fraction)))
    if n_test >= len(y):
        n_test = len(y) - 1
    stratify = y if task_type == "classification" and len(np.unique(y)) > 1 else None
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=n_test,
            random_state=seed,
            stratify=stratify,
        )
    except ValueError:
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=n_test,
            random_state=seed,
        )
    return X_train, y_train, X_test, y_test


def make_synthetic(
    name: str,
    n_tasks: int = 200,
    n_samples: int = 100,
    seed: int = 0,
    test_fraction: float = 0.0,
) -> TaskStream:
    """Generate one of the four synthetic datasets.

    Parameters
    ----------
    name:
        One of ``syn1``, ``syn2``, ``syn3`` or ``syn4``.
    n_tasks:
        Total number of tasks. Tasks are split evenly between the two
        distributions D1 and D2, then globally shuffled by the runner.
    n_samples:
        Number of observations per task.  The underlying sample pool is at
        least 300 observations, so experiments that vary ``m_t`` use nested
        prefixes of the same data.
    seed:
        Seed for task parameters and observations.
    test_fraction:
        Optional held-out fraction used by the forgetting experiment.
    """
    if name not in {"syn1", "syn2", "syn3", "syn4"}:
        raise ValueError(f"Unknown synthetic dataset: {name}")

    task_type = "classification" if name in {"syn1", "syn2"} else "regression"
    adversarial = name in {"syn2", "syn4"}
    same_marginal = name in {"syn2", "syn4"}

    mu1 = np.array([10.0, 10.0])
    mu2 = np.array([20.0, 5.0])
    sigma = 1.0
    pool_size = max(int(n_samples), 300)
    tasks: list[TaskData] = []

    for index in range(n_tasks):
        category = "D1" if index < n_tasks // 2 else "D2"
        # A separate RNG stream per task keeps task parameters and samples
        # independent of the number of tasks and of m_t.
        rng = np.random.default_rng([int(seed), int(index)])
        eps = rng.normal(0.0, np.sqrt(1e-3))
        if category == "D1":
            a = np.array([-1.0 + eps, 1.0 + eps])
            mu = mu1
        else:
            # syn1/syn3 use the D2 decision boundary from the paper.
            # syn2/syn4 reuse the D1 boundary and flip the labels.
            a = (
                np.array([-1.0 + eps, 1.0 + eps])
                if same_marginal
                else np.array([-0.25 + eps, 1.0 + eps])
            )
            mu = mu1 if same_marginal else mu2

        X_pool = rng.normal(mu, sigma, size=(pool_size, 2))
        score = X_pool @ a
        if adversarial and category == "D2":
            score = -score

        if task_type == "classification":
            y_pool = np.where(score >= 0.0, 1.0, -1.0)
        else:
            y_pool = score.astype(np.float64)

        X = X_pool[:n_samples]
        y = y_pool[:n_samples]
        X_train, y_train, X_test, y_test = _split(
            X, y, test_fraction, seed + index, task_type
        )
        tasks.append(
            TaskData(
                task_id=f"{name}_task{index:03d}",
                X_train=X_train,
                y_train=y_train,
                X_test=X_test,
                y_test=y_test,
                category=category,
            )
        )

    return TaskStream(name=name, task_type=task_type, tasks=tasks)
