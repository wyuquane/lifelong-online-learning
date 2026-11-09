"""Task ordering and example ordering utilities."""

from __future__ import annotations

import numpy as np
from scipy import sparse

from ..seeding import rng_for
from .base import TaskData, TaskStream


def _permute_examples(
    X: np.ndarray | sparse.csr_matrix,
    y: np.ndarray,
    rng: np.random.Generator,
) -> tuple[np.ndarray | sparse.csr_matrix, np.ndarray]:
    order = rng.permutation(len(y))
    if sparse.issparse(X):
        return X.tocsr()[order], y[order]
    return X[order], y[order]


def prepare_stream(
    stream: TaskStream,
    seed: int,
    shuffle_tasks: bool = True,
    shuffle_examples: bool = True,
) -> TaskStream:
    """Return a deterministic, shuffled copy of ``stream``.

    Task order is shuffled globally once per seed. Example order is shuffled
    independently inside each task. Every method receives the same stream for
    a given ``(dataset, seed)``.
    """
    tasks = list(stream.tasks)
    if shuffle_tasks:
        order = rng_for(seed, 1).permutation(len(tasks))
        tasks = [tasks[i] for i in order]

    if not shuffle_examples:
        return TaskStream(stream.name, stream.task_type, tasks)

    prepared: list[TaskData] = []
    for index, task in enumerate(tasks):
        train_rng = rng_for(seed, 2 + index)
        X_train, y_train = _permute_examples(task.X_train, task.y_train, train_rng)
        X_test, y_test = task.X_test, task.y_test
        if X_test is not None and y_test is not None:
            test_rng = rng_for(seed, 10_000 + index)
            X_test, y_test = _permute_examples(X_test, y_test, test_rng)
        prepared.append(
            TaskData(
                task_id=task.task_id,
                X_train=X_train,
                y_train=y_train,
                X_test=X_test,
                y_test=y_test,
                category=task.category,
            )
        )

    return TaskStream(stream.name, stream.task_type, prepared)
