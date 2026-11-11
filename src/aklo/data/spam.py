"""Spam detection dataset (one task per user)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import sparse
from sklearn.model_selection import train_test_split

from .base import TaskData, TaskStream


def _split_sparse(
    X: sparse.csr_matrix,
    y: np.ndarray,
    test_fraction: float,
    seed: int,
) -> tuple[sparse.csr_matrix, np.ndarray, sparse.csr_matrix | None, np.ndarray | None]:
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


def load_spam(
    path: str | Path,
    n_samples: int = 200,
    n_users: int = 15,
    seed: int = 0,
    test_fraction: float = 0.0,
    n_test: int = 0,
) -> TaskStream:
    """Load the ECML-PKDD 2006 spam data.

    The provided NPZ stores a 6000 x 152543 CSR matrix with 15 users and 400
    examples per user. The reproduction samples ``n_samples`` examples per
    user, as in the paper, and uses raw bag-of-word counts.  ``n_test=-1``
    uses every remaining row of a user as the test set (the E3 protocol);
    a positive value draws a disjoint test block of that size.
    """
    archive = np.load(path, allow_pickle=True)
    X_all = sparse.csr_matrix(
        (archive["data"], archive["indices"], archive["indptr"]),
        shape=tuple(archive["shape"]),
    ).astype(np.float64)
    y_all = np.asarray(archive["y"]).ravel().astype(np.float64)
    user_ids = np.asarray(archive["user_ids"]).ravel()

    unique_users = sorted(np.unique(user_ids))[:n_users]
    tasks: list[TaskData] = []
    for task_index, user in enumerate(unique_users):
        indices = np.flatnonzero(user_ids == user)
        rng = np.random.default_rng(seed + 2_000 + task_index)
        total = len(indices)
        if n_test < 0:
            train_size = min(n_samples, total)
            order = rng.permutation(total)
            train_indices = indices[order[:train_size]]
            test_indices = indices[order[train_size:]]
        elif n_test > 0:
            wanted = min(n_samples + n_test, total)
            order = rng.choice(total, size=wanted, replace=False)
            train_size = min(n_samples, max(wanted - 1, 0))
            train_indices = indices[order[:train_size]]
            test_indices = indices[order[train_size:]]
        else:
            train_size = min(n_samples, total)
            train_indices = indices[
                rng.choice(total, size=train_size, replace=False)
            ]
            test_indices = None

        X_train = X_all[train_indices]
        y_train = y_all[train_indices]
        if test_indices is not None:
            X_test = X_all[test_indices]
            y_test = y_all[test_indices]
        else:
            X_test, y_test = None, None
            X_train, y_train, X_test, y_test = _split_sparse(
                X_train, y_train, test_fraction, seed + task_index
            )
        tasks.append(
            TaskData(
                task_id=f"spam_{user}",
                X_train=X_train,
                y_train=y_train,
                X_test=X_test,
                y_test=y_test,
            )
        )

    return TaskStream(name="spam", task_type="classification", tasks=tasks)
