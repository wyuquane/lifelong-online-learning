"""Configuration loading for the AKLO reproduction."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML file and return a dictionary."""
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected a mapping in {path}, got {type(data).__name__}")
    return data


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge ``override`` into a copy of ``base``."""
    result = deepcopy(base)
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def _resolve(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def load_config(experiment_path: str | Path) -> dict[str, Any]:
    """Load base, experiment, dataset and model configurations.

    Returns a dictionary with keys ``base``, ``experiment``, ``datasets``,
    ``models`` and ``root``. Dataset and model configs are loaded by the
    names listed in the experiment file.
    """
    base = load_yaml(ROOT / "configs" / "base.yaml")
    experiment = load_yaml(_resolve(experiment_path))

    dataset_names = experiment.get("datasets")
    if dataset_names is None:
        dataset_names = [experiment["dataset"]]
    method_names = experiment.get("methods")
    if method_names is None:
        method_names = [experiment["method"]]

    datasets = {}
    for name in dataset_names:
        datasets[name] = load_yaml(ROOT / "configs" / "data" / f"{name}.yaml")

    models = {}
    for name in method_names:
        models[name] = load_yaml(ROOT / "configs" / "models" / f"{name}.yaml")

    return {
        "base": base,
        "experiment": experiment,
        "datasets": datasets,
        "models": models,
        "root": str(ROOT),
    }
