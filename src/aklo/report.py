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
DATASET_LABELS = {
    "syn1": "Syn1",
    "syn2": "Syn2",
    "landmine": "Landmine",
    "spam": "Spam",
    "syn3": "Syn3",
    "syn4": "Syn4",
    "london": "London",
}
# Colors and markers follow the paper's visual language closely enough to make
# the figures comparable at a glance.
METHOD_STYLES = {
    "itol": ("black", "s"),
    "tol": ("#1f77b4", "o"),
    "unif_sum": ("#2ca02c", "^"),
    "tranol": ("#9467bd", "D"),
    "otb": ("#e377c2", "P"),
    "aklo": ("#d62728", "*"),
    "akloms": ("#ff7f0e", "X"),
}
PAPER_METHODS = ["itol", "tol", "unif_sum", "tranol", "otb", "aklo"]

# Paper Figures 4/5 use the legend order from the experiment config, not a
# numeric sort.  Keep that order so the figures match the paper.
SENSITIVITY_ORDER = {
    "e4_sensitivity_cls": {
        "eta": [10, 1, 0.01, 0.001, 0.0001, 0],
        "lambda": [0, 0.0001, 0.001, 0.005, 0.01, 0.05, 0.1],
        "delta_alpha": [0, 0.001, 0.005, 0.01, 1],
    },
    "e5_sensitivity_reg": {
        "eta": [0.5, 0.25, 0.05, 0.0005, 0.0001, 0],
        "lambda": [0, 0.25, 0.625, 0.75, 0.875, 1],
        "delta_alpha": [0, 0.001, 0.005, 0.01, 0.025, 1],
    },
}
SENSITIVITY_SYMBOLS = {
    "eta": r"$\eta$",
    "lambda": r"$\lambda$",
    "delta_alpha": r"$\Delta\alpha$",
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


def _mean_int(values: list[float]) -> str:
    """Format a count as an integer (means of identical counts stay exact)."""
    if not values:
        return "-"
    return str(int(round(float(np.mean(values)))))


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
def _method_by_dataset_table(
    results: list[dict[str, Any]],
    value_key: str,
) -> str:
    """Paper layout: one row per method, one column per dataset."""
    datasets = [name for name in DATASET_ORDER if any(r["dataset"] == name for r in results)]
    methods = [
        method
        for method in PAPER_METHODS
        if any(r["method"] == method for r in results)
    ]
    headers = ["Method"] + [DATASET_LABELS[name] for name in datasets]
    rows = []
    for method in methods:
        cells = [METHOD_LABELS[method]]
        for dataset in datasets:
            group = _method_results(results, dataset, method)
            values = _values(group, value_key, scale=_ace_scale)
            cells.append(
                _link(_mean_std(values), _first(group)) if values else "–"
            )
        rows.append(cells)
    return _markdown_table(headers, rows)


def table_e1(results: list[dict[str, Any]]) -> str:
    """Main comparison table (paper Table 1 layout)."""
    return _method_by_dataset_table(results, "final_cumulative_ace")


def table_e1_paper(results: list[dict[str, Any]]) -> str:
    """Side-by-side paper Table 1 and reproduction values."""
    datasets = [name for name in DATASET_ORDER if name in PAPER_TABLE1]
    methods = PAPER_METHODS
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
    """E3 Table 2 layout: final-state ACE on all task test sets."""
    return _method_by_dataset_table(results, "final_test_ace_task_mean")


def table_e3_pooled(results: list[dict[str, Any]]) -> str:
    """Secondary E3 metric: pooled final-state test ACE."""
    return _method_by_dataset_table(results, "final_test_ace_pooled")


def table_e3_paper(results: list[dict[str, Any]]) -> str:
    """Paper Table 2 next to our final-state test ACE."""
    datasets = [name for name in DATASET_ORDER if name in PAPER_TABLE2]
    methods = PAPER_METHODS
    headers = ["Dataset", "Method", "Paper Table 2", "Our test ACE"]
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
                    DATASET_LABELS[dataset],
                    METHOD_LABELS[method],
                    f"{paper_value:.2f}",
                    _link(
                        _mean_std(
                            _values(
                                group,
                                "final_test_ace_task_mean",
                                _ace_scale,
                            )
                        ),
                        _first(group),
                    ),
                ]
            )
    return _markdown_table(headers, rows)


def _sensitivity_table(
    results: list[dict[str, Any]],
    parameter: str,
    ace_label: str = "ACE (%)",
) -> str:
    groups = _group(
        results,
        lambda result: result["config"].get("model_overrides", {}).get(parameter),
    )
    # Runs that do not override this parameter belong to the sweeps of the
    # other parameters and must not be pooled into a spurious "None" row.
    groups.pop(None, None)
    headers = [parameter, ace_label, "W&B"]
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
    return _sensitivity_table(results, "eta", ace_label="ACE")


def table_e6(results: list[dict[str, Any]]) -> str:
    """AKLOMS ACE by tau and dataset (paper Table 3 layout)."""
    datasets = [name for name in DATASET_ORDER if any(r["dataset"] == name for r in results)]
    taus = sorted(
        {
            float(result["config"].get("model_overrides", {}).get("tau", 0.0))
            for result in results
        }
    )
    headers = ["Dataset"] + [f"{tau:g}" for tau in taus]
    rows = []
    for dataset in datasets:
        cells = [DATASET_LABELS[dataset]]
        for tau in taus:
            group = [
                result
                for result in results
                if result["dataset"] == dataset
                and float(result["config"].get("model_overrides", {}).get("tau", 0.0))
                == tau
            ]
            cells.append(
                _link(
                    _mean_std(
                        _values(group, "final_cumulative_ace", _ace_scale)
                    ),
                    _first(group),
                )
            )
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


def _average_task_curve(results: list[dict[str, Any]]) -> np.ndarray | None:
    """Average cumulative-ACE curve over one or more runs."""
    arrays = []
    for result in results:
        tasks = result.get("tasks", [])
        if not tasks:
            continue
        curve = np.asarray(
            [task.get("cumulative_ace", np.nan) for task in tasks],
            dtype=np.float64,
        )
        arrays.append(curve * _ace_scale(result))
    if not arrays:
        return None
    length = min(len(array) for array in arrays)
    return np.mean([array[:length] for array in arrays], axis=0)


def _paper_style(plt) -> None:
    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.labelsize": 9,
            "axes.titlesize": 10,
            "legend.fontsize": 7,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.dpi": 160,
        }
    )


def figure_e2(results: list[dict[str, Any]], output_dir: Path) -> Path | None:
    """Paper Figure 3: ACE evolution for each m_t on syn1."""
    plt = _pyplot()
    _paper_style(plt)
    methods = [m for m in PAPER_METHODS if any(r["method"] == m for r in results)]
    sample_counts = sorted(
        {
            int(result["config"].get("data_overrides", {}).get("n_samples", 0))
            for result in results
        }
    )
    sample_counts = [value for value in sample_counts if value > 0]
    if not methods or not sample_counts:
        return None

    columns = 4
    rows = int(np.ceil(len(sample_counts) / columns))
    fig, axes = plt.subplots(
        rows, columns, figsize=(16, 3.9 * rows), squeeze=False
    )
    letters = "abcdefghijklmnop"
    for panel, n_samples in enumerate(sample_counts):
        axis = axes[panel // columns][panel % columns]
        for method in methods:
            group = [
                result
                for result in results
                if result["method"] == method
                and int(
                    result["config"].get("data_overrides", {}).get("n_samples", -1)
                )
                == n_samples
            ]
            curve = _average_task_curve(group)
            if curve is None:
                continue
            color, marker = METHOD_STYLES[method]
            axis.plot(
                np.arange(1, len(curve) + 1),
                curve,
                color=color,
                marker=marker,
                markersize=4,
                markerfacecolor="white",
                markeredgewidth=1.0,
                markevery=10,
                linewidth=1.4,
                label=METHOD_LABELS[method],
            )
        axis.set_xlim(0, 200)
        axis.set_xticks(np.arange(0, 201, 25))
        axis.set_ylim(bottom=0.0)
        axis.set_xlabel("Task Index", labelpad=2)
        axis.set_ylabel("ACE (%)")
        axis.legend(loc="upper right", fontsize=6.5, frameon=True)
        axis.text(
            0.5,
            -0.28,
            f"({letters[panel]}) $m_t$ = {n_samples}",
            transform=axis.transAxes,
            ha="center",
            va="top",
            fontsize=11,
        )
    for panel in range(len(sample_counts), rows * columns):
        axes[panel // columns][panel % columns].axis("off")
    fig.subplots_adjust(bottom=0.16, hspace=0.55, wspace=0.30)
    path = output_dir / "e2_small_m.png"
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return path


def _task_curves(
    results: list[dict[str, Any]],
    parameter: str,
    values: list[float],
) -> dict[float, np.ndarray]:
    """Average cumulative-ACE curves for each swept parameter value."""
    curves: dict[float, np.ndarray] = {}
    for value in values:
        group = [
            result
            for result in results
            if result.get("config", {})
            .get("model_overrides", {})
            .get(parameter)
            == value
        ]
        arrays = []
        for result in group:
            tasks = result.get("tasks", [])
            if not tasks:
                continue
            curve = np.asarray(
                [task.get("cumulative_ace", np.nan) for task in tasks],
                dtype=np.float64,
            )
            arrays.append(curve * _ace_scale(result))
        if arrays:
            length = min(len(array) for array in arrays)
            curves[float(value)] = np.mean(
                [array[:length] for array in arrays], axis=0
            )
    return curves


def _paper_sensitivity_figure(
    results: list[dict[str, Any]],
    experiment: str,
    output_path: Path,
) -> Path | None:
    """Three-panel ACE-vs-task figure in the style of paper Figures 4/5."""
    plt = _pyplot()
    _paper_style(plt)
    if not results:
        return None
    order = SENSITIVITY_ORDER[experiment]
    parameters = ["eta", "lambda", "delta_alpha"]
    task_type = results[0].get("task_type", "classification")
    ylabel = "ACE (%)" if task_type == "classification" else "ACE"
    colors = plt.get_cmap("tab10").colors
    markers = ["o", "s", "^", "D", "x", "v", "P"]

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))
    plotted = False
    for axis, parameter, letter in zip(axes, parameters, "abc"):
        values = order[parameter]
        curves = _task_curves(results, parameter, values)
        for index, value in enumerate(values):
            curve = curves.get(float(value))
            if curve is None:
                continue
            symbol = SENSITIVITY_SYMBOLS[parameter]
            axis.plot(
                np.arange(1, len(curve) + 1),
                curve,
                color=colors[index % len(colors)],
                marker=markers[index % len(markers)],
                markersize=4.5,
                markerfacecolor="white",
                markeredgewidth=1.1,
                markevery=10,
                linewidth=1.5,
                label=f"{symbol} = {value:g}",
            )
            plotted = True
        axis.set_xlim(0, 200)
        axis.set_xticks(np.arange(0, 201, 25))
        axis.set_xlabel("Tasks", labelpad=2)
        axis.set_ylabel(ylabel)
        axis.set_ylim(bottom=0.0)
        axis.legend(loc="upper right", fontsize=7.5, frameon=True)
        axis.text(
            0.5,
            -0.30,
            f"({letter}) Parameter: {SENSITIVITY_SYMBOLS[parameter]}",
            transform=axis.transAxes,
            ha="center",
            va="top",
            fontsize=12,
        )
    if not plotted:
        plt.close(fig)
        return None
    fig.subplots_adjust(bottom=0.24, wspace=0.30)
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return output_path


def figure_e4(results: list[dict[str, Any]], output_dir: Path) -> Path | None:
    return _paper_sensitivity_figure(
        results,
        "e4_sensitivity_cls",
        output_dir / "e4_sensitivity_cls.png",
    )


def figure_e5(results: list[dict[str, Any]], output_dir: Path) -> Path | None:
    return _paper_sensitivity_figure(
        results,
        "e5_sensitivity_reg",
        output_dir / "e5_sensitivity_reg.png",
    )


def _e7_series(results: list[dict[str, Any]]) -> dict[int, list[dict[str, float]]]:
    """ACE, remaining-model count, and remaining-model ratio per task count."""
    task_counts = sorted(
        {
            int(result["config"].get("data_overrides", {}).get("n_tasks", 0))
            for result in results
        }
    )
    series: dict[int, list[dict[str, float]]] = {}
    for task_count in task_counts:
        taus = sorted(
            {
                float(result["config"].get("model_overrides", {}).get("tau", 0.0))
                for result in results
                if int(
                    result["config"].get("data_overrides", {}).get("n_tasks", -1)
                )
                == task_count
            }
        )
        points = []
        for tau in taus:
            group = [
                result
                for result in results
                if int(
                    result["config"].get("data_overrides", {}).get("n_tasks", -1)
                )
                == task_count
                and float(
                    result["config"].get("model_overrides", {}).get("tau", -1.0)
                )
                == tau
            ]
            values = _values(group, "final_cumulative_ace", _ace_scale)
            ratios = [
                result.get("summary", {}).get("final_state", {}).get("selected_ratio")
                for result in group
            ]
            ratios = [float(value) for value in ratios if value is not None]
            if not values or not ratios:
                continue
            ratio = float(np.mean(ratios))
            points.append(
                {
                    "tau": float(tau),
                    "ace": float(np.mean(values)),
                    "ratio": ratio,
                    "n_models": ratio * task_count,
                }
            )
        if points:
            series[task_count] = sorted(points, key=lambda item: item["tau"])
    return series


def figure_e7(results: list[dict[str, Any]], output_dir: Path) -> Path | None:
    """Paper Figure 7: AKLOMS ACE, remaining models, and remaining ratio."""
    plt = _pyplot()
    _paper_style(plt)
    series = _e7_series(results)
    if not series:
        return None
    colors = plt.get_cmap("tab10").colors
    markers = ["o", "s", "^", "D", "x", "v", "P", "X"]

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.6))
    for index, (task_count, points) in enumerate(series.items()):
        color = colors[index % len(colors)]
        marker = markers[index % len(markers)]
        label = f"# of Tasks - {task_count}"
        axes[0].plot(
            [point["tau"] for point in points],
            [point["ace"] for point in points],
            color=color,
            marker=marker,
            markersize=4.5,
            markerfacecolor="white",
            linewidth=1.4,
            label=label,
        )
        ordered = sorted(points, key=lambda item: item["ratio"])
        axes[1].plot(
            [point["n_models"] for point in ordered],
            [point["ace"] for point in ordered],
            color=color,
            marker=marker,
            markersize=4.5,
            markerfacecolor="white",
            linewidth=1.4,
            label=label,
        )
        axes[2].plot(
            [point["ratio"] for point in ordered],
            [point["ace"] for point in ordered],
            color=color,
            marker=marker,
            markersize=4.5,
            markerfacecolor="white",
            linewidth=1.4,
            label=label,
        )

    axes[0].set_xlim(-0.5, 25.5)
    axes[0].set_xticks([0, 5, 10, 15, 20, 25])
    axes[0].set_xlabel(r"$\tau$")
    axes[0].set_ylabel("ACE (%)")
    axes[0].legend(loc="upper left", fontsize=6.5, frameon=True)

    axes[1].set_xlim(left=0.0)
    axes[1].set_xlabel("Model Number")
    axes[1].set_ylabel("ACE (%)")
    axes[1].set_title("Model Number - Performance", fontsize=10)
    axes[1].legend(loc="upper right", fontsize=6.5, frameon=True)

    axes[2].set_xlim(0.0, 1.01)
    axes[2].set_xticks(np.arange(0.0, 1.01, 0.2))
    axes[2].set_xlabel("Model Ratio")
    axes[2].set_ylabel("ACE (%)")
    axes[2].set_title("Model Ratio - Performance", fontsize=10)
    axes[2].legend(loc="upper right", fontsize=6.5, frameon=True)

    for axis, label in zip(axes, ["(a)", "(b)", "(b)"]):
        axis.text(
            0.5,
            -0.28,
            label,
            transform=axis.transAxes,
            ha="center",
            va="top",
            fontsize=12,
        )
    fig.subplots_adjust(bottom=0.20, wspace=0.30)
    path = output_dir / "e7_akloms_models.png"
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return path


def figure_e8(results: list[dict[str, Any]], output_dir: Path) -> Path | None:
    """Paper Figure 8: runtime versus m_t and task count, with line plots."""
    plt = _pyplot()
    _paper_style(plt)
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
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.6))
    colors = plt.get_cmap("tab10").colors
    markers = ["o", "s", "^", "D", "x", "v", "P", "X"]

    if aklo_results:
        task_counts = sorted(
            {int(r["config"]["notes"]["task_count"]) for r in aklo_results}
        )
        sample_counts = sorted(
            {int(r["config"]["notes"]["n_samples"]) for r in aklo_results}
        )
        for index, task_count in enumerate(task_counts):
            xs, ys = [], []
            for n_samples in sample_counts:
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
                    xs.append(n_samples)
                    ys.append(float(np.mean(values)))
            axes[0].plot(
                xs,
                ys,
                color=colors[index % len(colors)],
                marker=markers[index % len(markers)],
                markersize=4.5,
                markerfacecolor="white",
                linewidth=1.4,
                label=f"Task # - {task_count}",
            )
        axes[0].set_xlabel("Data # of One Task")
        axes[0].set_ylabel("Running Time (s)")
        axes[0].set_title("AKLO", fontsize=11)
        axes[0].legend(fontsize=6.5, loc="upper left", frameon=True)
    else:
        axes[0].axis("off")

    if akloms_results:
        task_counts = sorted(
            {int(r["config"]["notes"]["task_count"]) for r in akloms_results}
        )
        present_taus = {
            float(r["config"]["notes"]["tau"]) for r in akloms_results
        }
        tau_order = [10.0, 0.05, 0.025, 0.01, 0.005, 0.0025, 0.001, 0.0]
        taus = [tau for tau in tau_order if tau in present_taus]
        taus.extend(sorted(present_taus - set(taus)))
        for index, tau in enumerate(taus):
            xs, ys = [], []
            for task_count in task_counts:
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
                    xs.append(task_count)
                    ys.append(float(np.mean(values)))
            axes[1].plot(
                xs,
                ys,
                color=colors[index % len(colors)],
                marker=markers[index % len(markers)],
                markersize=4.5,
                markerfacecolor="white",
                linewidth=1.4,
                label=rf"$\tau$ - {tau:g}",
            )
        axes[1].set_xlabel("# of Tasks")
        axes[1].set_ylabel("Running Time (s)")
        axes[1].set_title("AKLOMS", fontsize=11)
        axes[1].legend(fontsize=6.5, loc="upper left", frameon=True)
    else:
        axes[1].axis("off")

    for axis, label in zip(axes, ["(a)", "(b)"]):
        axis.text(
            0.5,
            -0.24,
            label,
            transform=axis.transAxes,
            ha="center",
            va="top",
            fontsize=12,
        )
    fig.subplots_adjust(bottom=0.18, wspace=0.28)
    path = output_dir / "e8_runtime.png"
    fig.savefig(path, dpi=160, bbox_inches="tight")
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
        "Generated from the JSON files in `results/`. Classification ACE is a",
        "percentage; regression ACE is on the target scale. W&B links are",
        "included when the run was tracked online.",
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
        "Training follows E1 exactly. After the last task, the method's final",
        "predictor is evaluated on the test set of every task `1..T`, matching",
        "the paper's description: the whole test set constituted of samples from",
        "previous tasks is fed to the model after training. The synthetic",
        "datasets use 50 tasks (25 D1 + 25 D2) with 100 training and 100 separate",
        "test samples per task. Landmine uses 150 training rows per task and all",
        "remaining rows as test; Spam uses 200 training rows per user and all",
        "remaining rows as test. London keeps an 80/20 split per school. Each",
        "experiment is repeated with 10 seeds; the data and split are fixed and",
        "only the task/example order changes. The primary metric is the",
        "task-averaged test ACE, with the pooled test ACE as a secondary metric.",
        "Classification ACE is multiplied by 100; regression ACE is on the target",
        "scale. OTB is not defined for regression, so those cells are empty.",
        "",
        table_e3(load_results(results_dir, "e3_catastrophic-forgetting")),
        "",
        "### Secondary metric: pooled test ACE",
        "",
        table_e3_pooled(
            load_results(results_dir, "e3_catastrophic-forgetting")
        ),
        "",
        "### Paper vs reproduction",
        "",
        table_e3_paper(
            load_results(results_dir, "e3_catastrophic-forgetting")
        ),
        "",
        "The paper reports mean ± standard deviation over 10 repetitions. Our",
        "table uses the same aggregation over seeds 0-9. See",
        "`docs/experiment_protocol.md` for the exact protocol.",
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
        _sensitivity_table(load_results(results_dir, "e5_sensitivity_reg"), "lambda", "ACE"),
        "",
        "### delta_alpha",
        "",
        _sensitivity_table(load_results(results_dir, "e5_sensitivity_reg"), "delta_alpha", "ACE"),
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
            ("e2_small_m.png", figure_e2(load_results(results_dir, "e2_small_m"), output_dir)),
            ("e4_sensitivity_cls.png", figure_e4(load_results(results_dir, "e4_sensitivity_cls"), output_dir)),
            ("e5_sensitivity_reg.png", figure_e5(load_results(results_dir, "e5_sensitivity_reg"), output_dir)),
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
