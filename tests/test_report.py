"""Tests for report figure generation."""

from __future__ import annotations

from pathlib import Path

from aklo.report import PAPER_METHODS, figure_paper2

CLASSIFICATION = {"syn1", "syn2", "landmine", "spam"}
DATASETS = ["syn1", "syn2", "landmine", "spam", "syn3", "syn4", "london"]


def _fake_result(dataset: str, method: str, seed: int) -> dict:
    task_type = "classification" if dataset in CLASSIFICATION else "regression"
    return {
        "dataset": dataset,
        "method": method,
        "task_type": task_type,
        "seed": seed,
        "config": {},
        "summary": {},
        "tasks": [
            {"cumulative_ace": 0.60 - 0.05 * index - 0.001 * seed}
            for index in range(4)
        ],
    }


def test_figure_paper2_generates_png(tmp_path: Path) -> None:
    """Figure 2 is built from E1-style per-task results."""
    results = [
        _fake_result(dataset, method, seed)
        for dataset in DATASETS
        for method in PAPER_METHODS
        for seed in range(2)
    ]
    path = figure_paper2(results, tmp_path)
    assert path is not None
    assert path.name == "figure2_ace_evolution.png"
    assert path.stat().st_size > 0


def test_figure_paper2_handles_empty_results(tmp_path: Path) -> None:
    """No results means no figure instead of an exception."""
    assert figure_paper2([], tmp_path) is None
