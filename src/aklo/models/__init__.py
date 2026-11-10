"""Model factory."""

from __future__ import annotations

from typing import Any

from .aklo import AKLO
from .akloms import AKLOMS
from .baselines import ITOL, OTB, TOL, TranOL, UnifSum


def _resolve_config(model_config: dict[str, Any], task_type: str) -> dict[str, Any]:
    resolved = {
        key: value
        for key, value in model_config.items()
        if key not in {"classification", "regression", "supported_task_types"}
    }
    task_section = model_config.get(task_type)
    if isinstance(task_section, dict):
        resolved.update(task_section)
    return resolved


def build_model(
    method: str,
    dim: int,
    task_type: str,
    model_config: dict[str, Any],
    seed: int = 0,
    overrides: dict[str, Any] | None = None,
):
    """Build a learner by name.

    ``model_config`` is the YAML dictionary for the method. If it contains a
    ``classification`` or ``regression`` section, that section is merged over
    the top-level defaults. ``overrides`` is applied last, after the task
    section has been resolved.
    """
    supported = model_config.get("supported_task_types")
    if supported is not None and task_type not in supported:
        raise ValueError(f"{method} does not support task type {task_type}")

    config = _resolve_config(model_config, task_type)
    if overrides:
        config.update(overrides)
    factories = {
        "aklo": AKLO,
        "akloms": AKLOMS,
        "itol": ITOL,
        "tol": TOL,
        "unif_sum": UnifSum,
        "tranol": TranOL,
        "otb": OTB,
    }
    if method not in factories:
        raise ValueError(f"Unknown method: {method}")
    return factories[method](dim, task_type, config, seed=seed)
