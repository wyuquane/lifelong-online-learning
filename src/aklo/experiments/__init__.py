"""Experiment registry: turn YAML experiment configs into run specifications."""

from __future__ import annotations

from typing import Any

from ..runner import RunSpec


def _seeds(experiment: dict[str, Any], base: dict[str, Any]) -> list[int]:
    return [int(seed) for seed in experiment.get("seeds", base.get("seeds", [0]))]


def _label(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def _supports(model_config: dict[str, Any], task_type: str | None) -> bool:
    supported = model_config.get("supported_task_types")
    return supported is None or task_type in supported


def _make_spec(
    experiment_name: str,
    dataset_name: str,
    method: str,
    seed: int,
    datasets: dict[str, Any],
    models: dict[str, Any],
    *,
    suffix: str = "",
    data_overrides: dict[str, Any] | None = None,
    model_overrides: dict[str, Any] | None = None,
    test_fraction: float = 0.0,
    evaluate_forgetting: bool = False,
    log_selected_models: bool = False,
    notes: dict[str, Any] | None = None,
) -> RunSpec:
    run_name = f"{experiment_name}-{dataset_name}-{method}{suffix}-s{seed}"
    return RunSpec(
        experiment=experiment_name,
        dataset=dataset_name,
        method=method,
        seed=seed,
        run_name=run_name,
        group=experiment_name,
        tags=[dataset_name, method, f"seed-{seed}"],
        data_config=datasets[dataset_name],
        model_config=models[method],
        data_overrides=dict(data_overrides or {}),
        model_overrides=dict(model_overrides or {}),
        test_fraction=float(test_fraction),
        evaluate_forgetting=bool(evaluate_forgetting),
        log_selected_models=bool(log_selected_models),
        notes=dict(notes or {}),
    )


# ---------------------------------------------------------------------------
# Individual experiment families
# ---------------------------------------------------------------------------
def _e1_main(experiment: dict[str, Any], config: dict[str, Any]) -> list[RunSpec]:
    name = experiment["experiment"]
    specs: list[RunSpec] = []
    for dataset_name in experiment["datasets"]:
        dataset = config["datasets"][dataset_name]
        for method in experiment["methods"]:
            model = config["models"][method]
            if not _supports(model, dataset.get("task_type")):
                continue
            for seed in _seeds(experiment, config["base"]):
                specs.append(
                    _make_spec(
                        name,
                        dataset_name,
                        method,
                        seed,
                        config["datasets"],
                        config["models"],
                        test_fraction=float(experiment.get("test_fraction", 0.0)),
                        evaluate_forgetting=bool(
                            experiment.get("evaluate_forgetting", False)
                        ),
                    )
                )
    return specs


def _e2_small_m(experiment: dict[str, Any], config: dict[str, Any]) -> list[RunSpec]:
    name = experiment["experiment"]
    dataset_name = experiment["dataset"]
    specs: list[RunSpec] = []
    for n_samples in experiment["n_samples_values"]:
        for method in experiment["methods"]:
            for seed in _seeds(experiment, config["base"]):
                specs.append(
                    _make_spec(
                        name,
                        dataset_name,
                        method,
                        seed,
                        config["datasets"],
                        config["models"],
                        suffix=f"-m{_label(n_samples)}",
                        data_overrides={"n_samples": int(n_samples)},
                        test_fraction=float(experiment.get("test_fraction", 0.0)),
                        evaluate_forgetting=bool(
                            experiment.get("evaluate_forgetting", False)
                        ),
                    )
                )
    return specs


def _e3_task_test(
    experiment: dict[str, Any], config: dict[str, Any]
) -> list[RunSpec]:
    """Per-task 80/20 train/test protocol for the Table 2 comparison.

    The training split keeps the E1 sample count for datasets with a fixed
    ``n_samples``; the extra rows are drawn by the loader and then split.  The
    per-dataset overrides live in ``e3_task_test.yaml`` so the relationship to
    E1 is explicit and auditable.
    """
    name = experiment["experiment"]
    test_fraction = float(experiment.get("test_fraction", 0.2))
    per_dataset = experiment.get("data_overrides", {})
    specs: list[RunSpec] = []
    for dataset_name in experiment["datasets"]:
        dataset = config["datasets"][dataset_name]
        for method in experiment["methods"]:
            model = config["models"][method]
            if not _supports(model, dataset.get("task_type")):
                continue
            for seed in _seeds(experiment, config["base"]):
                specs.append(
                    _make_spec(
                        name,
                        dataset_name,
                        method,
                        seed,
                        config["datasets"],
                        config["models"],
                        data_overrides=per_dataset.get(dataset_name, {}),
                        test_fraction=test_fraction,
                        evaluate_forgetting=bool(
                            experiment.get("evaluate_forgetting", False)
                        ),
                    )
                )
    return specs


def _sensitivity(experiment: dict[str, Any], config: dict[str, Any]) -> list[RunSpec]:
    name = experiment["experiment"]
    dataset_name = experiment["dataset"]
    method = experiment["method"]
    specs: list[RunSpec] = []
    for parameter, values in experiment["sweeps"].items():
        for value in values:
            for seed in _seeds(experiment, config["base"]):
                specs.append(
                    _make_spec(
                        name,
                        dataset_name,
                        method,
                        seed,
                        config["datasets"],
                        config["models"],
                        suffix=f"-{parameter}-{_label(value)}",
                        model_overrides={parameter: value},
                        test_fraction=float(experiment.get("test_fraction", 0.0)),
                        evaluate_forgetting=bool(
                            experiment.get("evaluate_forgetting", False)
                        ),
                        notes={"swept_parameter": parameter, "swept_value": value},
                    )
                )
    return specs


def _e6_akloms_tau(
    experiment: dict[str, Any], config: dict[str, Any]
) -> list[RunSpec]:
    name = experiment["experiment"]
    method = experiment["method"]
    specs: list[RunSpec] = []
    for dataset_name in experiment["datasets"]:
        for tau in experiment["tau_values"]:
            for seed in _seeds(experiment, config["base"]):
                specs.append(
                    _make_spec(
                        name,
                        dataset_name,
                        method,
                        seed,
                        config["datasets"],
                        config["models"],
                        suffix=f"-tau{_label(tau)}",
                        model_overrides={"tau": float(tau)},
                        test_fraction=float(experiment.get("test_fraction", 0.0)),
                        evaluate_forgetting=bool(
                            experiment.get("evaluate_forgetting", False)
                        ),
                    )
                )
    return specs


def _e7_akloms_models(
    experiment: dict[str, Any], config: dict[str, Any]
) -> list[RunSpec]:
    name = experiment["experiment"]
    dataset_name = experiment["dataset"]
    method = experiment["method"]
    visualization_tau = set(experiment.get("visualization_tau", []))
    tau_grid = sorted(
        set(experiment.get("tau_values", []))
        | set(experiment.get("ratio_tau_values", []))
    )
    specs: list[RunSpec] = []
    for task_count in experiment["task_counts"]:
        for tau in tau_grid:
            for seed in _seeds(experiment, config["base"]):
                figure = (
                    "fig7a"
                    if tau in experiment.get("tau_values", [])
                    else "fig7b"
                )
                specs.append(
                    _make_spec(
                        name,
                        dataset_name,
                        method,
                        seed,
                        config["datasets"],
                        config["models"],
                        suffix=f"-T{_label(task_count)}-tau{_label(tau)}",
                        data_overrides={"n_tasks": int(task_count)},
                        model_overrides={"tau": float(tau)},
                        test_fraction=float(experiment.get("test_fraction", 0.0)),
                        evaluate_forgetting=bool(
                            experiment.get("evaluate_forgetting", False)
                        ),
                        log_selected_models=(
                            int(task_count) == 200 and tau in visualization_tau
                        ),
                        notes={
                            "task_count": int(task_count),
                            "tau": float(tau),
                            "figure": figure,
                        },
                    )
                )
    return specs


def _e8_runtime(experiment: dict[str, Any], config: dict[str, Any]) -> list[RunSpec]:
    name = experiment["experiment"]
    dataset_name = experiment["dataset"]
    specs: list[RunSpec] = []
    seeds = _seeds(experiment, config["base"])

    # Figure 8(a): AKLO, task-count x sample-count grid.
    for task_count in experiment["aklo_task_counts"]:
        for n_samples in experiment["aklo_sample_counts"]:
            for seed in seeds:
                specs.append(
                    _make_spec(
                        name,
                        dataset_name,
                        "aklo",
                        seed,
                        config["datasets"],
                        config["models"],
                        suffix=f"-aklo-T{_label(task_count)}-m{_label(n_samples)}",
                        data_overrides={
                            "n_tasks": int(task_count),
                            "n_samples": int(n_samples),
                        },
                        notes={
                            "figure": "fig8a",
                            "task_count": int(task_count),
                            "n_samples": int(n_samples),
                        },
                    )
                )

    # Figure 8(b): AKLOMS, task-count x tau grid at a fixed sample count.
    n_samples = int(experiment.get("akloms_sample_count", 100))
    for task_count in experiment["akloms_task_counts"]:
        for tau in experiment["akloms_tau_values"]:
            for seed in seeds:
                specs.append(
                    _make_spec(
                        name,
                        dataset_name,
                        "akloms",
                        seed,
                        config["datasets"],
                        config["models"],
                        suffix=f"-akloms-T{_label(task_count)}-tau{_label(tau)}",
                        data_overrides={
                            "n_tasks": int(task_count),
                            "n_samples": n_samples,
                        },
                        model_overrides={"tau": float(tau)},
                        notes={
                            "figure": "fig8b",
                            "task_count": int(task_count),
                            "tau": float(tau),
                            "n_samples": n_samples,
                        },
                    )
                )
    return specs


_BUILDERS = {
    "e1_main": _e1_main,
    "e2_small_m": _e2_small_m,
    "e3_task_test": _e3_task_test,
    "e4_sensitivity_cls": _sensitivity,
    "e5_sensitivity_reg": _sensitivity,
    "e6_akloms_tau": _e6_akloms_tau,
    "e7_akloms_models": _e7_akloms_models,
    "e8_runtime": _e8_runtime,
}


def build_specs(config: dict[str, Any]) -> list[RunSpec]:
    """Build all run specifications for a loaded experiment config."""
    experiment = config["experiment"]
    name = experiment["experiment"]
    if name not in _BUILDERS:
        raise ValueError(f"Unknown experiment: {name}")
    return _BUILDERS[name](experiment, config)


def experiment_names() -> list[str]:
    return list(_BUILDERS)
