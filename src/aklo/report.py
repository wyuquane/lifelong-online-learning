"""Tables and figures built from saved run results.

The module is deliberately independent of W&B: it reads the JSON files written
by :mod:`aklo.runner` and produces Markdown tables and PNG figures. This keeps
the reproduction usable offline and makes the report reproducible from the
committed experiment configuration plus the public W&B runs.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np

DATASET_ORDER = ["syn1", "syn2", "landmine", "spam", "syn3", "syn4", "london"]
CLASSIFICATION_DATASETS = ["syn1", "syn2", "landmine", "spam"]
REGRESSION_DATASETS = ["syn3", "syn4", "london"]
METHOD_ORDER = ["itol", "tol", "unif_sum", "tranol", "otb", "aklo", "akloms"]
METHOD_LABELS = {
    "itol": "ITOL",
    "tol": "TOL",
    "unif_sum": "UnifSum",
    "tranol": "TransOL",
    "otb": "OTB",
    "aklo": "AKLO",
    "akloms": "AKLOMS",
}

# Paper Table 1: Average Cumulative Error Rate (%) +/- standard deviation.
PAPER_TABLE1: dict[str, dict[str, float]] = {
    "syn1": {
        "itol": 36.18,
        "tol": 21.16,
        "unif_sum": 49.63,
        "tranol": 36.40,
        "otb": 30.19,
        "aklo": 10.10,
    },
    "syn2": {
        "itol": 33.70,
        "tol": 33.34,
        "unif_sum": 43.07,
        "tranol": 32.97,
        "otb": 34.90,
        "aklo": 10.16,
    },
    "landmine": {
        "itol": 13.86,
        "tol": 11.54,
        "unif_sum": 7.97,
        "tranol": 8.05,
        "otb": 10.94,
        "aklo": 7.30,
    },
    "spam": {
        "itol": 25.00,
        "tol": 19.51,
        "unif_sum": 19.50,
        "tranol": 24.50,
        "otb": 24.10,
        "aklo": 17.36,
    },
    "syn3": {
        "itol": 14.54,
        "tol": 7.63,
        "unif_sum": 27.69,
        "tranol": 61.61,
        "aklo": 4.06,
    },
    "syn4": {
        "itol": 8.02,
        "tol": 9.96,
        "unif_sum": 51.23,
        "tranol": 54.55,
        "aklo": 2.98,
    },
    "london": {
        "itol": 20.76,
        "tol": 20.91,
        "unif_sum": 10.94,
        "tranol": 79.58,
        "aklo": 10.05,
    },
}

# Paper Table 2: catastrophic forgetting, test samples from previous tasks.
PAPER_TABLE2: dict[str, dict[str, float]] = {
    "syn1": {
        "itol": 36.36,
        "tol": 21.54,
        "unif_sum": 49.96,
        "tranol": 35.99,
        "otb": 30.24,
        "aklo": 8.78,
    },
    "syn2": {
        "itol": 33.51,
        "tol": 33.65,
        "unif_sum": 41.32,
        "tranol": 32.56,
        "otb": 35.06,
        "aklo": 8.34,
    },
    "landmine": {
        "itol": 14.00,
        "tol": 11.59,
        "unif_sum": 6.86,
        "tranol": 8.08,
        "otb": 11.09,
        "aklo": 6.78,
    },
    "spam": {
        "itol": 25.23,
        "tol": 17.13,
        "unif_sum": 12.33,
        "tranol": 26.43,
        "otb": 23.17,
        "aklo": 9.97,
    },
    "syn3": {
        "itol": 14.53,
        "tol": 7.62,
        "unif_sum": 27.60,
        "tranol": 61.54,
        "aklo": 3.58,
    },
    "syn4": {
        "itol": 8.05,
        "tol": 9.82,
        "unif_sum": 51.36,
        "tranol": 54.57,
        "aklo": 2.34,
    },
    "london": {
        "itol": 20.80,
        "tol": 20.87,
        "unif_sum": 10.42,
        "tranol": 79.58,
        "aklo": 9.57,
    },
}

# Paper Table 3: AKLOMS ACE (%) by tau.
PAPER_TABLE3: dict[str, dict[str, float]] = {
    "syn1": {
        0.001: 10.91,
        0.01: 11.92,
        0.05: 15.10,
        0.1: 18.27,
        0.5: 34.71,
        1.0: 33.88,
        5.0: 34.72,
        10.0: 33.78,
        100.0: 34.64,
    },
    "syn2": {
        0.001: 11.10,
        0.01: 13.16,
        0.05: 17.00,
        0.1: 21.05,
        0.5: 26.93,
        1.0: 48.74,
        5.0: 48.62,
        10.0: 48.95,
        100.0: 47.71,
    },
    "landmine": {
        0.001: 7.17,
        0.01: 7.18,
        0.05: 7.16,
        0.1: 7.19,
        0.5: 8.01,
        1.0: 11.29,
        5.0: 11.68,
        10.0: 12.99,
        100.0: 11.18,
    },
    "spam": {
        0.001: 18.34,
        0.01: 18.53,
        0.05: 18.99,
        0.1: 19.89,
        0.5: 19.92,
        1.0: 21.34,
        5.0: 23.69,
        10.0: 23.00,
        100.0: 23.67,
    },
    "syn3": {
        0.001: 3.96,
        0.01: 4.34,
        0.05: 5.61,
        0.1: 6.30,
        0.5: 29.53,
        1.0: 30.08,
        5.0: 29.59,
        10.0: 29.48,
        100.0: 29.70,
    },
    "syn4": {
        0.001: 3.15,
        0.01: 3.31,
        0.05: 4.43,
        0.1: 5.32,
        0.5: 5.82,
        1.0: 53.37,
        5.0: 53.27,
        10.0: 51.99,
        100.0: 53.22,
    },
    "london": {
        0.001: 9.83,
        0.01: 10.06,
        0.05: 10.14,
        0.1: 10.30,
        0.5: 10.41,
        1.0: 11.65,
        5.0: 16.75,
        10.0: 17.02,
        100.0: 16.64,
    },
}


# ---------------------------------------------------------------------------
# Loading and formatting helpers
# ---------------------------------------------------------------------------
def load_results(results_dir: str | Path, experiment: str | None = None) -> list[dict[str, Any]]:
    """Load JSON result files, optionally restricted to one experiment."""
    directory = Path(results_dir)
    if experiment is not None:
        files = sorted((directory / experiment).glob("*.json"))
    else:
        files = sorted(directory.glob("*/*.json"))
    results = []
    for path in files:
        try:
            result = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as error:
            print(f"[report] skipping {path}: {error}")
            continue
        if result.get("config", {}).get("smoke"):
            continue
        results.append(result)
    return results


def _values(
    results: Iterable[dict[str, Any]],
    key: str,
    scale: float | Any = 1.0,
) -> list[float]:
    values = []
    for result in results:
        value = result.get("summary", {}).get(key)
        if value is not None:
            factor = scale(result) if callable(scale) else scale
            values.append(float(value) * factor)
    return values


def _ace_scale(result: dict[str, Any]) -> float:
    """Classification ACE is a rate (x100); regression ACE is already raw."""
    return 100.0 if result.get("task_type") == "classification" else 1.0


def _mean_std(values: list[float]) -> str:
    if not values:
        return "-"
    mean = float(np.mean(values))
    if len(values) == 1:
        return f"{mean:.2f}"
    return f"{mean:.2f} ± {float(np.std(values, ddof=0)):.2f}"


def _link(value: str, result: dict[str, Any] | None) -> str:
    if result is None:
        return value
    url = result.get("summary", {}).get("wandb_url")
    if not url:
        return value
    return f"[{value}]({url})"


def _first(results: list[dict[str, Any]]) -> dict[str, Any] | None:
    return results[0] if results else None


def _markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)


def _group(
    results: Iterable[dict[str, Any]],
    key_fn,
) -> dict[Any, list[dict[str, Any]]]:
    grouped: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        grouped[key_fn(result)].append(result)
    return grouped


def _method_results(
    results: Iterable[dict[str, Any]],
    dataset: str,
    method: str,
) -> list[dict[str, Any]]:
    return [
        result
        for result in results
        if result.get("dataset") == dataset and result.get("method") == method
    ]


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------
def table_e1(results: list[dict[str, Any]]) -> str:
    """Main comparison table (paper Table 1)."""
    datasets = [name for name in DATASET_ORDER if any(r["dataset"] == name for r in results)]
    methods = [
        method
        for method in METHOD_ORDER
        if any(r["method"] == method for r in results)
    ]
    headers = ["Dataset"] + [METHOD_LABELS[method] for method in methods] + ["Paper AKLO"]
    rows = []
    for dataset in datasets:
        cells = [dataset]
        for method in methods:
            group = _method_results(results, dataset, method)
            values = _values(group, "final_cumulative_ace", scale=_ace_scale)
            cells.append(_link(_mean_std(values), _first(group)))
        cells.append(f"{PAPER_TABLE1.get(dataset, {}).get('aklo', float('nan')):.2f}")
        rows.append(cells)
    return _markdown_table(headers, rows)


def table_e1_paper(results: list[dict[str, Any]]) -> str:
    """Side-by-side paper Table 1 and reproduction values."""
    datasets = [name for name in DATASET_ORDER if name in PAPER_TABLE1]
    methods = ["itol", "tol", "unif_sum", "tranol", "otb", "aklo"]
    headers = ["Dataset", "Method", "Paper", "Reproduction"]
    rows = []
    for dataset in datasets:
        for method in methods:
            paper_value = PAPER_TABLE1[dataset].get(method)
            if paper_value is None:
                continue
            group = _method_results(results, dataset, method)
            if not group:
                continue
            reproduction = _values(group, "final_cumulative_ace", scale=_ace_scale)
            rows.append(
                [
                    dataset,
                    METHOD_LABELS[method],
                    f"{paper_value:.2f}",
                    _link(_mean_std(reproduction), _first(group)),
                ]
            )
    return _markdown_table(headers, rows)


def table_e2(results: list[dict[str, Any]]) -> str:
    """ACE versus the number of observations per task (paper Figure 3)."""
    methods = [
        method
        for method in METHOD_ORDER
        if any(r["method"] == method for r in results)
    ]
    sample_counts = sorted(
        {
            int(result["config"].get("data_overrides", {}).get("n_samples", 0))
            for result in results
        }
    )
    headers = ["m_t"] + [METHOD_LABELS[method] for method in methods]
    rows = []
    for n_samples in sample_counts:
        cells = [str(n_samples)]
        for method in methods:
            group = [
                result
                for result in results
                if result["method"] == method
                and int(result["config"].get("data_overrides", {}).get("n_samples", -1))
                == n_samples
            ]
            cells.append(_link(_mean_std(_values(group, "final_cumulative_ace", _ace_scale)), _first(group)))
        rows.append(cells)
    return _markdown_table(headers, rows)


def table_e3(results: list[dict[str, Any]]) -> str:
    """Held-out test diagnostics for the forgetting experiment."""
    datasets = [name for name in DATASET_ORDER if any(r["dataset"] == name for r in results)]
    methods = [
        method
        for method in METHOD_ORDER
        if any(r["method"] == method for r in results)
    ]
    headers = ["Dataset", "Method", "Prequential", "Current test", "Old test", "Final test", "Final train"]
    rows = []
    for dataset in datasets:
        for method in methods:
            group = _method_results(results, dataset, method)
            if not group:
                continue
            rows.append(
                [
                    dataset,
                    METHOD_LABELS[method],
                    _link(_mean_std(_values(group, "final_cumulative_ace", _ace_scale)), _first(group)),
                    _mean_std(_values(group, "mean_current_test_ace", _ace_scale)),
                    _mean_std(_values(group, "mean_old_test_ace", _ace_scale)),
                    _mean_std(_values(group, "forgetting_task_mean", _ace_scale)),
                    _mean_std(_values(group, "final_train_ace_task_mean", _ace_scale)),
                ]
            )
    return _markdown_table(headers, rows)


def table_e3_paper(results: list[dict[str, Any]]) -> str:
    """Side-by-side paper Table 2 and the reproduction's final test ACE."""
    datasets = [name for name in DATASET_ORDER if name in PAPER_TABLE2]
    methods = ["itol", "tol", "unif_sum", "tranol", "otb", "aklo"]
    headers = ["Dataset", "Method", "Paper Table 2", "Our final test", "Our final train"]
    rows = []
    for dataset in datasets:
        for method in methods:
            paper_value = PAPER_TABLE2[dataset].get(method)
            if paper_value is None:
                continue
            group = _method_results(results, dataset, method)
            if not group:
                continue
            rows.append(
                [
                    dataset,
                    METHOD_LABELS[method],
                    f"{paper_value:.2f}",
                    _mean_std(_values(group, "forgetting_task_mean", _ace_scale)),
                    _mean_std(_values(group, "final_train_ace_task_mean", _ace_scale)),
                ]
            )
    return _markdown_table(headers, rows)


def _sensitivity_table(
    results: list[dict[str, Any]],
    parameter: str,
) -> str:
    groups = _group(
        results,
        lambda result: result["config"].get("model_overrides", {}).get(parameter),
    )
    # Runs that do not override this parameter belong to the sweeps of the
    # other parameters and must not be pooled into a spurious "None" row.
    groups.pop(None, None)
    headers = [parameter, "ACE (%)", "W&B"]
    rows = []
    for value in sorted(groups, key=lambda item: (item is None, item)):
        group = groups[value]
        rows.append(
            [
                f"{value:g}" if isinstance(value, (int, float)) else str(value),
                _mean_std(_values(group, "final_cumulative_ace", _ace_scale)),
                _link("run", _first(group)),
            ]
        )
    if not rows:
        return "_No results for this parameter._"
    return _markdown_table(headers, rows)


def table_e4(results: list[dict[str, Any]]) -> str:
    return _sensitivity_table(results, "eta")


def table_e5(results: list[dict[str, Any]]) -> str:
    return _sensitivity_table(results, "eta")


def table_e6(results: list[dict[str, Any]]) -> str:
    """AKLOMS ACE by tau and dataset (paper Table 3)."""
    datasets = [name for name in DATASET_ORDER if any(r["dataset"] == name for r in results)]
    taus = sorted(
        {
            float(result["config"].get("model_overrides", {}).get("tau", 0.0))
            for result in results
        }
    )
    headers = ["tau"] + datasets + ["Paper mean"]
    rows = []
    for tau in taus:
        cells = [f"{tau:g}"]
        paper_values = []
        for dataset in datasets:
            group = [
                result
                for result in results
                if result["dataset"] == dataset
                and float(result["config"].get("model_overrides", {}).get("tau", 0.0))
                == tau
            ]
            cells.append(_link(_mean_std(_values(group, "final_cumulative_ace", _ace_scale)), _first(group)))
            paper_value = PAPER_TABLE3.get(dataset, {}).get(tau)
            if paper_value is not None:
                paper_values.append(paper_value)
        cells.append(f"{np.mean(paper_values):.2f}" if paper_values else "-")
        rows.append(cells)
    return _markdown_table(headers, rows)


def table_e7(results: list[dict[str, Any]]) -> str:
    """AKLOMS ACE and selected-model ratio by task count and tau."""
    task_counts = sorted(
        {
            int(result["config"].get("data_overrides", {}).get("n_tasks", 0))
            for result in results
        }
    )
    taus = sorted(
        {
            float(result["config"].get("model_overrides", {}).get("tau", 0.0))
            for result in results
        }
    )
    headers = ["Tasks"] + [f"tau={tau:g}" for tau in taus]
    rows = []
    for task_count in task_counts:
        cells = [str(task_count)]
        for tau in taus:
            group = [
                result
                for result in results
                if int(result["config"].get("data_overrides", {}).get("n_tasks", -1))
                == task_count
                and float(result["config"].get("model_overrides", {}).get("tau", -1.0))
                == tau
            ]
            cells.append(_mean_std(_values(group, "final_cumulative_ace", _ace_scale)))
        rows.append(cells)
    return _markdown_table(headers, rows)


def table_e7_ratio(results: list[dict[str, Any]]) -> str:
    task_counts = sorted(
        {
            int(result["config"].get("data_overrides", {}).get("n_tasks", 0))
            for result in results
        }
    )
    taus = sorted(
        {
            float(result["config"].get("model_overrides", {}).get("tau", 0.0))
            for result in results
        }
    )
    headers = ["Tasks"] + [f"tau={tau:g}" for tau in taus]
    rows = []
    for task_count in task_counts:
        cells = [str(task_count)]
        for tau in taus:
            group = [
                result
                for result in results
                if int(result["config"].get("data_overrides", {}).get("n_tasks", -1))
                == task_count
                and float(result["config"].get("model_overrides", {}).get("tau", -1.0))
                == tau
            ]
            ratios = [
                result.get("summary", {}).get("final_state", {}).get("selected_ratio")
                for result in group
            ]
            ratios = [float(value) for value in ratios if value is not None]
            cells.append(_mean_std([value * 100.0 for value in ratios]))
        rows.append(cells)
    return _markdown_table(headers, rows)


def table_e8(results: list[dict[str, Any]]) -> str:
    """Runtime grids for Figure 8."""
    aklo_results = [
        result
        for result in results
        if result.get("method") == "aklo"
        and result["config"].get("notes", {}).get("figure") == "fig8a"
    ]
    akloms_results = [
        result
        for result in results
        if result.get("method") == "akloms"
        and result["config"].get("notes", {}).get("figure") == "fig8b"
    ]
    lines = ["### AKLO runtime (seconds)", ""]
    if aklo_results:
        task_counts = sorted(
            {
                int(result["config"]["notes"]["task_count"])
                for result in aklo_results
            }
        )
        sample_counts = sorted(
            {
                int(result["config"]["notes"]["n_samples"])
                for result in aklo_results
            }
        )
        headers = ["Tasks \\ m_t"] + [str(value) for value in sample_counts]
        rows = []
        for task_count in task_counts:
            cells = [str(task_count)]
            for n_samples in sample_counts:
                group = [
                    result
                    for result in aklo_results
                    if int(result["config"]["notes"]["task_count"]) == task_count
                    and int(result["config"]["notes"]["n_samples"]) == n_samples
                ]
                values = _values(group, "train_seconds")
                cells.append(f"{np.mean(values):.3f}" if values else "-")
            rows.append(cells)
        lines.append(_markdown_table(headers, rows))
    else:
        lines.append("_No E8 AKLO results yet._")

    lines.extend(["", "### AKLOMS runtime (seconds)", ""])
    if akloms_results:
        task_counts = sorted(
            {
                int(result["config"]["notes"]["task_count"])
                for result in akloms_results
            }
        )
        taus = sorted(
            {
                float(result["config"]["notes"]["tau"])
                for result in akloms_results
            }
        )
        headers = ["Tasks \\ tau"] + [f"{tau:g}" for tau in taus]
        rows = []
        for task_count in task_counts:
            cells = [str(task_count)]
            for tau in taus:
                group = [
                    result
                    for result in akloms_results
                    if int(result["config"]["notes"]["task_count"]) == task_count
                    and float(result["config"]["notes"]["tau"]) == tau
                ]
                values = _values(group, "train_seconds")
                cells.append(f"{np.mean(values):.3f}" if values else "-")
            rows.append(cells)
        lines.append(_markdown_table(headers, rows))
    else:
        lines.append("_No E8 AKLOMS results yet._")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------
def _pyplot():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def figure_e1(results: list[dict[str, Any]], output_dir: Path) -> Path | None:
    plt = _pyplot()
    datasets = [name for name in DATASET_ORDER if any(r["dataset"] == name for r in results)]
    methods = [m for m in METHOD_ORDER if any(r["method"] == m for r in results)]
    if not datasets or not methods:
        return None
    width = 0.8 / len(methods)
    x = np.arange(len(datasets))
    fig, ax = plt.subplots(figsize=(10, 4.5))
    for index, method in enumerate(methods):
        means = []
        for dataset in datasets:
            values = _values(
                _method_results(results, dataset, method),
                "final_cumulative_ace",
                _ace_scale,
            )
            means.append(float(np.mean(values)) if values else np.nan)
        ax.bar(x + index * width - 0.4 + width / 2, means, width, label=METHOD_LABELS[method])
    ax.set_xticks(x)
    ax.set_xticklabels(datasets)
    ax.set_ylabel("ACE (%)")
    ax.set_title("E1: average cumulative error by dataset")
    ax.legend(ncol=3, fontsize=8)
    fig.tight_layout()
    path = output_dir / "e1_main.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def figure_e2(results: list[dict[str, Any]], output_dir: Path) -> Path | None:
    plt = _pyplot()
    methods = [m for m in METHOD_ORDER if any(r["method"] == m for r in results)]
    if not methods:
        return None
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for method in methods:
        points = []
        for result in results:
            if result["method"] != method:
                continue
            n_samples = result["config"].get("data_overrides", {}).get("n_samples")
            value = result.get("summary", {}).get("final_cumulative_ace")
            if n_samples is not None and value is not None:
                points.append((int(n_samples), float(value) * _ace_scale(result)))
        if points:
            points.sort()
            ax.plot([p[0] for p in points], [p[1] for p in points], marker="o", label=METHOD_LABELS[method])
    ax.set_xscale("log")
    ax.set_xlabel("Observations per task (m_t)")
    ax.set_ylabel("ACE (%)")
    ax.set_title("E2: effect of the number of observations per task (syn1)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    path = output_dir / "e2_small_m.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def figure_e3(results: list[dict[str, Any]], output_dir: Path) -> Path | None:
    plt = _pyplot()
    datasets = [name for name in DATASET_ORDER if any(r["dataset"] == name for r in results)]
    if not datasets:
        return None
    metrics = [
        ("final_cumulative_ace", "Prequential"),
        ("mean_current_test_ace", "Current test"),
        ("mean_old_test_ace", "Old test"),
        ("forgetting_task_mean", "Final test"),
    ]
    x = np.arange(len(datasets))
    width = 0.8 / len(metrics)
    fig, ax = plt.subplots(figsize=(10, 4.5))
    for index, (key, label) in enumerate(metrics):
        means = []
        for dataset in datasets:
            values = _values(
                _method_results(results, dataset, "aklo"),
                key,
                _ace_scale,
            )
            means.append(float(np.mean(values)) if values else np.nan)
        ax.bar(x + index * width - 0.4 + width / 2, means, width, label=label)
    ax.set_xticks(x)
    ax.set_xticklabels(datasets)
    ax.set_ylabel("ACE (%)")
    ax.set_title("E3: AKLO prequential vs held-out test diagnostics")
    ax.legend(fontsize=8)
    fig.tight_layout()
    path = output_dir / "e3_forgetting.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def _sensitivity_figure(
    results: list[dict[str, Any]],
    parameter: str,
    title: str,
    output_path: Path,
) -> Path | None:
    plt = _pyplot()
    groups = _group(
        results,
        lambda result: result["config"].get("model_overrides", {}).get(parameter),
    )
    if not groups:
        return None
    points = []
    for value, group in groups.items():
        if value is None:
            continue
        values = _values(group, "final_cumulative_ace", _ace_scale)
        if values:
            points.append((float(value), float(np.mean(values))))
    if not points:
        return None
    points.sort()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot([p[0] for p in points], [p[1] for p in points], marker="o")
    ax.set_xscale("symlog", linthresh=1e-5)
    ax.set_xlabel(parameter)
    ax.set_ylabel("ACE (%)")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return output_path


def figure_e4(results: list[dict[str, Any]], output_dir: Path) -> Path | None:
    # The experiment contains three sweeps; make one figure with three panels.
    plt = _pyplot()
    parameters = ["eta", "lambda", "delta_alpha"]
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))
    plotted = False
    for axis, parameter in zip(axes, parameters):
        groups = _group(
            results,
            lambda result: result["config"].get("model_overrides", {}).get(parameter),
        )
        points = []
        for value, group in groups.items():
            if value is None:
                continue
            values = _values(group, "final_cumulative_ace", _ace_scale)
            if values:
                points.append((float(value), float(np.mean(values))))
        if points:
            points.sort()
            axis.plot([p[0] for p in points], [p[1] for p in points], marker="o")
            axis.set_xscale("symlog", linthresh=1e-5)
            plotted = True
        axis.set_xlabel(parameter)
        axis.set_ylabel("ACE (%)")
        axis.set_title(f"syn1: {parameter}")
    if not plotted:
        plt.close(fig)
        return None
    fig.tight_layout()
    path = output_dir / "e4_sensitivity_cls.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def figure_e5(results: list[dict[str, Any]], output_dir: Path) -> Path | None:
    plt = _pyplot()
    parameters = ["eta", "lambda", "delta_alpha"]
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))
    plotted = False
    for axis, parameter in zip(axes, parameters):
        groups = _group(
            results,
            lambda result: result["config"].get("model_overrides", {}).get(parameter),
        )
        points = []
        for value, group in groups.items():
            if value is None:
                continue
            values = _values(group, "final_cumulative_ace", _ace_scale)
            if values:
                points.append((float(value), float(np.mean(values))))
        if points:
            points.sort()
            axis.plot([p[0] for p in points], [p[1] for p in points], marker="o")
            axis.set_xscale("symlog", linthresh=1e-5)
            plotted = True
        axis.set_xlabel(parameter)
        axis.set_ylabel("ACE (%)")
        axis.set_title(f"syn3: {parameter}")
    if not plotted:
        plt.close(fig)
        return None
    fig.tight_layout()
    path = output_dir / "e5_sensitivity_reg.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def figure_e6(results: list[dict[str, Any]], output_dir: Path) -> Path | None:
    plt = _pyplot()
    datasets = [name for name in DATASET_ORDER if any(r["dataset"] == name for r in results)]
    if not datasets:
        return None
    columns = 4
    rows = int(np.ceil(len(datasets) / columns))
    fig, axes = plt.subplots(rows, columns, figsize=(14, 3.2 * rows), squeeze=False)
    for index, dataset in enumerate(datasets):
        axis = axes[index // columns][index % columns]
        points = []
        for result in results:
            if result["dataset"] != dataset:
                continue
            tau = result["config"].get("model_overrides", {}).get("tau")
            value = result.get("summary", {}).get("final_cumulative_ace")
            if tau is not None and value is not None:
                points.append((float(tau), float(value) * _ace_scale(result)))
        points.sort()
        if points:
            axis.plot([p[0] for p in points], [p[1] for p in points], marker="o")
            axis.set_xscale("log")
        axis.set_title(dataset)
        axis.set_xlabel("tau")
        axis.set_ylabel("ACE (%)")
    for index in range(len(datasets), rows * columns):
        axes[index // columns][index % columns].axis("off")
    fig.suptitle("E6: AKLOMS sensitivity to tau")
    fig.tight_layout()
    path = output_dir / "e6_akloms_tau.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def figure_e7(results: list[dict[str, Any]], output_dir: Path) -> Path | None:
    plt = _pyplot()
    if not results:
        return None
    task_counts = sorted(
        {
            int(result["config"].get("data_overrides", {}).get("n_tasks", 0))
            for result in results
        }
    )
    taus = sorted(
        {
            float(result["config"].get("model_overrides", {}).get("tau", 0.0))
            for result in results
        }
    )
    if not task_counts or not taus:
        return None
    ace_grid = np.full((len(task_counts), len(taus)), np.nan)
    ratio_grid = np.full((len(task_counts), len(taus)), np.nan)
    for i, task_count in enumerate(task_counts):
        for j, tau in enumerate(taus):
            group = [
                result
                for result in results
                if int(result["config"].get("data_overrides", {}).get("n_tasks", -1))
                == task_count
                and float(result["config"].get("model_overrides", {}).get("tau", -1.0))
                == tau
            ]
            values = _values(group, "final_cumulative_ace", _ace_scale)
            if values:
                ace_grid[i, j] = float(np.mean(values))
            ratios = [
                result.get("summary", {}).get("final_state", {}).get("selected_ratio")
                for result in group
            ]
            ratios = [float(value) for value in ratios if value is not None]
            if ratios:
                ratio_grid[i, j] = float(np.mean(ratios)) * 100.0
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.2))
    for axis, grid, title in zip(
        axes,
        [ace_grid, ratio_grid],
        ["ACE (%)", "Selected models (%)"],
    ):
        image = axis.imshow(grid, aspect="auto", cmap="viridis")
        axis.set_xticks(range(len(taus)))
        axis.set_xticklabels([f"{tau:g}" for tau in taus], rotation=45)
        axis.set_yticks(range(len(task_counts)))
        axis.set_yticklabels([str(value) for value in task_counts])
        axis.set_xlabel("tau")
        axis.set_ylabel("Tasks")
        axis.set_title(title)
        fig.colorbar(image, ax=axis)
    fig.suptitle("E7: AKLOMS model selection on syn1")
    fig.tight_layout()
    path = output_dir / "e7_akloms_models.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def figure_e8(results: list[dict[str, Any]], output_dir: Path) -> Path | None:
    plt = _pyplot()
    aklo_results = [
        result
        for result in results
        if result.get("method") == "aklo"
        and result["config"].get("notes", {}).get("figure") == "fig8a"
    ]
    akloms_results = [
        result
        for result in results
        if result.get("method") == "akloms"
        and result["config"].get("notes", {}).get("figure") == "fig8b"
    ]
    if not aklo_results and not akloms_results:
        return None
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.2))
    if aklo_results:
        task_counts = sorted({int(r["config"]["notes"]["task_count"]) for r in aklo_results})
        sample_counts = sorted({int(r["config"]["notes"]["n_samples"]) for r in aklo_results})
        grid = np.full((len(task_counts), len(sample_counts)), np.nan)
        for i, task_count in enumerate(task_counts):
            for j, n_samples in enumerate(sample_counts):
                values = _values(
                    [
                        r
                        for r in aklo_results
                        if int(r["config"]["notes"]["task_count"]) == task_count
                        and int(r["config"]["notes"]["n_samples"]) == n_samples
                    ],
                    "train_seconds",
                )
                if values:
                    grid[i, j] = float(np.mean(values))
        image = axes[0].imshow(grid, aspect="auto", cmap="viridis")
        axes[0].set_xticks(range(len(sample_counts)))
        axes[0].set_xticklabels([str(v) for v in sample_counts])
        axes[0].set_yticks(range(len(task_counts)))
        axes[0].set_yticklabels([str(v) for v in task_counts])
        axes[0].set_xlabel("m_t")
        axes[0].set_ylabel("Tasks")
        axes[0].set_title("AKLO runtime (s)")
        fig.colorbar(image, ax=axes[0])
    else:
        axes[0].axis("off")
    if akloms_results:
        task_counts = sorted({int(r["config"]["notes"]["task_count"]) for r in akloms_results})
        taus = sorted({float(r["config"]["notes"]["tau"]) for r in akloms_results})
        grid = np.full((len(task_counts), len(taus)), np.nan)
        for i, task_count in enumerate(task_counts):
            for j, tau in enumerate(taus):
                values = _values(
                    [
                        r
                        for r in akloms_results
                        if int(r["config"]["notes"]["task_count"]) == task_count
                        and float(r["config"]["notes"]["tau"]) == tau
                    ],
                    "train_seconds",
                )
                if values:
                    grid[i, j] = float(np.mean(values))
        image = axes[1].imshow(grid, aspect="auto", cmap="viridis")
        axes[1].set_xticks(range(len(taus)))
        axes[1].set_xticklabels([f"{tau:g}" for tau in taus], rotation=45)
        axes[1].set_yticks(range(len(task_counts)))
        axes[1].set_yticklabels([str(v) for v in task_counts])
        axes[1].set_xlabel("tau")
        axes[1].set_ylabel("Tasks")
        axes[1].set_title("AKLOMS runtime (s)")
        fig.colorbar(image, ax=axes[1])
    else:
        axes[1].axis("off")
    fig.suptitle("E8: runtime scaling")
    fig.tight_layout()
    path = output_dir / "e8_runtime.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Report assembly
# ---------------------------------------------------------------------------
def build_report(
    results_dir: str | Path = "results",
    output_dir: str | Path = "reports",
    make_figures: bool = True,
) -> Path:
    """Build ``report.md`` and the figures from saved JSON results."""
    results_dir = Path(results_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    sections: list[str] = [
        "# AKLO reproduction report",
        "",
        "Generated from the JSON files in `results/`. Values are percentages",
        "unless stated otherwise. W&B links are included when the run was",
        "tracked online.",
        "",
        "## E1: main comparison (paper Table 1)",
        "",
        table_e1(load_results(results_dir, "e1_main")),
        "",
        "### Paper vs reproduction",
        "",
        table_e1_paper(load_results(results_dir, "e1_main")),
        "",
        "## E2: number of observations per task (paper Figure 3)",
        "",
        table_e2(load_results(results_dir, "e2_small_m")),
        "",
        "## E3: catastrophic forgetting (paper Table 2)",
        "",
        table_e3(load_results(results_dir, "e3_forgetting")),
        "",
        "### Paper vs reproduction",
        "",
        table_e3_paper(load_results(results_dir, "e3_forgetting")),
        "",
        "The paper's Table 2 is lower than its Table 1, which is consistent with",
        "re-feeding the training samples after training. We keep a held-out",
        "split and report both readings; see `docs/experiment_protocol.md`.",
        "",
        "## E4: classification sensitivity (paper Figure 4)",
        "",
        "### eta",
        "",
        table_e4(load_results(results_dir, "e4_sensitivity_cls")),
        "",
        "### lambda",
        "",
        _sensitivity_table(load_results(results_dir, "e4_sensitivity_cls"), "lambda"),
        "",
        "### delta_alpha",
        "",
        _sensitivity_table(load_results(results_dir, "e4_sensitivity_cls"), "delta_alpha"),
        "",
        "## E5: regression sensitivity (paper Figure 5)",
        "",
        "### eta",
        "",
        table_e5(load_results(results_dir, "e5_sensitivity_reg")),
        "",
        "### lambda",
        "",
        _sensitivity_table(load_results(results_dir, "e5_sensitivity_reg"), "lambda"),
        "",
        "### delta_alpha",
        "",
        _sensitivity_table(load_results(results_dir, "e5_sensitivity_reg"), "delta_alpha"),
        "",
        "## E6: AKLOMS tau sensitivity (paper Table 3)",
        "",
        table_e6(load_results(results_dir, "e6_akloms_tau")),
        "",
        "## E7: AKLOMS model selection (paper Figure 7)",
        "",
        table_e7(load_results(results_dir, "e7_akloms_models")),
        "",
        "### Selected-model ratio (%)",
        "",
        table_e7_ratio(load_results(results_dir, "e7_akloms_models")),
        "",
        "## E8: runtime scaling (paper Figure 8)",
        "",
        table_e8(load_results(results_dir, "e8_runtime")),
        "",
        "`train_seconds` covers only the per-sample predict/update loop; data",
        "loading and W&B calls are excluded. The runs still share one Windows",
        "machine, and background W&B uploads can perturb wall-clock timing, so",
        "the absolute seconds are indicative and the scaling shape is the",
        "reliable signal. The small-task-count cells are the noisiest; the",
        "trend is clearest from 400 tasks upward.",
        "",
        "At the tested `tau` values the AKLOMS cover stays close to the full",
        "knowledge base (see E6/E7), so the AKLOMS table mainly measures the",
        "cost of a near-full cover. The paper's negative `tau`/runtime trend",
        "requires much larger `tau` in this implementation; `tau=0` is the",
        "AKLO-equivalent special case.",
        "",
        "## Theory checks",
        "",
        "The empirical checks of Theorem 1, Corollary 1.1, and Corollary 1.2 are",
        "diagnostics, not benchmark runs, and are not logged to W&B. The summary",
        "and per-run reports are in [theory/README.md](theory/README.md).",
        "",
    ]

    if make_figures:
        figures = [
            ("e1_main.png", figure_e1(load_results(results_dir, "e1_main"), output_dir)),
            ("e2_small_m.png", figure_e2(load_results(results_dir, "e2_small_m"), output_dir)),
            ("e3_forgetting.png", figure_e3(load_results(results_dir, "e3_forgetting"), output_dir)),
            ("e4_sensitivity_cls.png", figure_e4(load_results(results_dir, "e4_sensitivity_cls"), output_dir)),
            ("e5_sensitivity_reg.png", figure_e5(load_results(results_dir, "e5_sensitivity_reg"), output_dir)),
            ("e6_akloms_tau.png", figure_e6(load_results(results_dir, "e6_akloms_tau"), output_dir)),
            ("e7_akloms_models.png", figure_e7(load_results(results_dir, "e7_akloms_models"), output_dir)),
            ("e8_runtime.png", figure_e8(load_results(results_dir, "e8_runtime"), output_dir)),
        ]
        sections.append("## Figures")
        sections.append("")
        for name, path in figures:
            if path is not None:
                sections.append(f"![{name}]({name})")
                sections.append("")

    report_path = output_dir / "report.md"
    report_path.write_text("\n".join(sections), encoding="utf-8")
    return report_path
