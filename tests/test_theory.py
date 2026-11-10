"""Tests for the empirical theory checks."""

from __future__ import annotations

import math

import numpy as np

from aklo.data.synthetic import make_synthetic
from aklo.data.stream import prepare_stream
from aklo.theory import (
    analyze_trace,
    greedy_packing,
    loss_values,
    solve_constrained_loss,
    trace_stream,
)


def _config(**overrides):
    config = {
        "loss": "hinge",
        "meta_loss": "hinge",
        "eta": 1.0,
        "lambda": 0.001,
        "delta_alpha": 0.001,
        "tau": 0.1,
    }
    config.update(overrides)
    return config


def test_loss_values() -> None:
    y = np.array([1.0, -1.0])
    predictions = np.array([0.5, 0.5])
    np.testing.assert_allclose(loss_values(y, predictions, "hinge"), [0.5, 1.5])
    np.testing.assert_allclose(loss_values(y, predictions, "absolute"), [0.5, 1.5])
    np.testing.assert_allclose(loss_values(y, predictions, "squared"), [0.25, 2.25])


def test_greedy_packing() -> None:
    loss_matrix = np.array(
        [
            [0.0, 0.1, 1.0, 1.1],
            [0.0, 0.2, 1.0, 1.2],
        ]
    )
    packing = greedy_packing(loss_matrix, tau=0.5)
    # Columns 0 and 2 are far apart; columns 1 and 3 are close to them.
    assert packing == [0, 2]


def test_solve_constrained_loss_matches_dense_grid() -> None:
    rng = np.random.default_rng(0)
    X = rng.normal(size=(30, 2))
    y = np.where(X[:, 0] - X[:, 1] >= 0.0, 1.0, -1.0)
    R = 0.7
    w, value = solve_constrained_loss(X, y, "hinge", R)
    assert np.linalg.norm(w) <= R + 1e-8

    angles = np.linspace(0.0, 2.0 * math.pi, 4000, endpoint=False)
    grid_values = []
    for theta in angles:
        candidate = R * np.array([math.cos(theta), math.sin(theta)])
        grid_values.append(loss_values(y, X @ candidate, "hinge").sum())
    grid_values.append(loss_values(y, X @ np.zeros(2), "hinge").sum())
    assert value <= min(grid_values) + 1e-6


def test_trace_stream_records_shapes() -> None:
    stream = prepare_stream(
        make_synthetic("syn1", n_tasks=4, n_samples=15, seed=0), seed=0
    )
    traces = trace_stream(stream, "aklo", _config(), seed=0)
    assert len(traces) == 4
    for task_index, trace in enumerate(traces):
        assert trace.n_samples == 15
        assert trace.alpha.shape == (15,)
        assert trace.current_pred.shape == (15,)
        assert trace.meta_pred.shape == (15,)
        assert trace.member_pred.shape == (15, task_index)
        assert trace.member_loss.shape == (15, task_index)
        assert trace.alpha[0] == 1.0
        assert np.all(np.diff(trace.alpha) <= 0.0)


def test_analyze_trace_smoke() -> None:
    stream = prepare_stream(
        make_synthetic("syn1", n_tasks=4, n_samples=15, seed=0), seed=0
    )
    traces = trace_stream(stream, "aklo", _config(), seed=0)
    analysis = analyze_trace(
        traces,
        task_type="classification",
        meta_loss="hinge",
        current_loss="hinge",
    )
    summary = analysis["summary"]
    assert summary["n_tasks_traced"] == 4
    assert summary["n_tasks_analyzed"] == 3
    assert summary["K"] > 0.0
    assert summary["R"] > 0.0
    assert summary["median_CE"] > 0.0
    assert summary["median_ratio_proof"] is not None
    for record in analysis["tasks"]:
        assert math.isfinite(record["CE"])
        assert math.isfinite(record["bound_proof"])
        assert record["t"] == record["task_index"] + 1
        assert "corollary_1_1" in record


def test_corollary_11_reports_infeasible_condition() -> None:
    # A slowly decaying alpha with a large required N is outside the
    # corollary's hypothesis; the analysis should say so rather than divide by
    # zero or silently claim a violation.
    alpha = np.maximum(0.0, 1.0 - 0.001 * np.arange(100))
    from aklo.theory import _corollary_11

    result = _corollary_11(
        alpha,
        expert=10.0,
        zeta_e=1.0,
        zeta_l=1.0,
        K=10.0,
        R=10.0,
        m=100,
        t=10,
        gamma_values=(0.5, 1.0),
    )
    assert result["applicable"] is True
    assert result["feasible"] is False
    assert result["checked_gamma"][-1]["i0"] < 100
