"""Dataset registry."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import TaskStream
from .landmine import load_landmine
from .london import load_london
from .spam import load_spam
from .synthetic import make_synthetic


def load_dataset(
    name: str,
    config: dict[str, Any],
    seed: int,
    root: str | Path = ".",
) -> TaskStream:
    """Load a dataset by name using its YAML configuration.

    Parameters
    ----------
    name : str
        Dataset name, also used by the synthetic generator.
    config : dict[str, Any]
        Dataset configuration containing at least ``kind``.
    seed : int
        Seed controlling subsampling and train/test splits.
    root : str | Path, optional
        Repository root used to resolve relative data paths.

    Returns
    -------
    TaskStream
        Loaded tasks and their shared task type.

    Raises
    ------
    ValueError
        If ``config["kind"]`` is not a supported dataset kind.
    """
    kind = config["kind"]
    test_fraction = float(config.get("test_fraction", 0.0))
    n_test = int(config.get("n_test", 0))

    if kind == "synthetic":
        return make_synthetic(
            name=name,
            n_tasks=int(config.get("n_tasks", 200)),
            n_samples=int(config.get("n_samples", 100)),
            seed=seed,
            test_fraction=test_fraction,
            n_test=n_test,
        )

    path = Path(config["path"])
    if not path.is_absolute():
        path = Path(root) / path

    if kind == "landmine":
        return load_landmine(
            path,
            n_samples=int(config.get("n_samples", 150)),
            seed=seed,
            test_fraction=test_fraction,
            n_test=n_test,
        )
    if kind == "spam":
        return load_spam(
            path,
            n_samples=int(config.get("n_samples", 200)),
            n_users=int(config.get("n_users", 15)),
            seed=seed,
            test_fraction=test_fraction,
            n_test=n_test,
        )
    if kind == "london":
        return load_london(path, seed=seed, test_fraction=test_fraction)

    raise ValueError(f"Unknown dataset kind: {kind}")
