"""London School dataset (139 regression tasks, one per school)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from sklearn.model_selection import train_test_split

from .base import TaskData, TaskStream

_YEARS = [1, 2, 3]
_VR_BANDS = [0, 1, 2, 3]
_ETHNIC = list(range(1, 12))
_SCHOOL_GENDERS = [1, 2, 3]
_DENOMINATIONS = [1, 2, 3]


def _one_hot(value: int, categories: list[int]) -> list[float]:
    return [1.0 if value == category else 0.0 for category in categories]


def _parse(path: str | Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rows: list[list[float]] = []
    targets: list[float] = []
    schools: list[int] = []

    with open(path, "r", encoding="latin-1") as handle:
        for line in handle:
            line = line.rstrip("\n\r")
            if len(line) != 16:
                continue
            year = int(line[0])
            school = int(line[1:4])
            exam = int(line[4:6])
            fsm = int(line[6:8]) / 100.0
            vr1 = int(line[8:10]) / 100.0
            gender = int(line[10])
            vr_band = int(line[11])
            ethnic = int(line[12:14])
            school_gender = int(line[14])
            denomination = int(line[15])

            features = []
            features.extend(_one_hot(year, _YEARS))
            features.append(float(gender))  # binary student gender
            features.extend(_one_hot(vr_band, _VR_BANDS))
            features.extend(_one_hot(ethnic, _ETHNIC))
            features.extend(_one_hot(school_gender, _SCHOOL_GENDERS))
            features.extend(_one_hot(denomination, _DENOMINATIONS))
            features.extend([fsm, vr1, 1.0])  # two school-level percentages + bias

            rows.append(features)
            targets.append(float(exam))
            schools.append(school)

    return (
        np.asarray(rows, dtype=np.float64),
        np.asarray(targets, dtype=np.float64),
        np.asarray(schools, dtype=np.int64),
    )


def load_london(
    path: str | Path,
    seed: int = 0,
    test_fraction: float = 0.0,
) -> TaskStream:
    """Load the London School fixed-width file and build one task per school.

    The paper reports 27 features plus a bias.  We one-hot encode the
    categorical columns (year, VR band, ethnic group, school gender,
    denomination), use student gender as one binary feature, divide the two
    school-level percentages by 100, and append a bias feature.  This yields
    28 inputs.  The target is the raw examination score.
    """
    X, y, schools = _parse(path)
    tasks: list[TaskData] = []
    for task_index, school in enumerate(sorted(np.unique(schools))):
        indices = np.flatnonzero(schools == school)
        X_task = X[indices]
        y_task = y[indices]
        if test_fraction > 0 and len(y_task) > 1:
            n_test = max(1, int(round(len(y_task) * test_fraction)))
            if n_test >= len(y_task):
                n_test = len(y_task) - 1
            X_train, X_test, y_train, y_test = train_test_split(
                X_task,
                y_task,
                test_size=n_test,
                random_state=seed + task_index,
            )
        else:
            X_train, y_train, X_test, y_test = X_task, y_task, None, None
        tasks.append(
            TaskData(
                task_id=f"london_school{school:03d}",
                X_train=X_train,
                y_train=y_train,
                X_test=X_test,
                y_test=y_test,
            )
        )

    return TaskStream(name="london", task_type="regression", tasks=tasks)
