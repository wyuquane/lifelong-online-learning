"""Tests for Algorithm 3 (AKLOMS)."""

from __future__ import annotations

import numpy as np

from aklo.data.synthetic import make_synthetic
from aklo.data.stream import prepare_stream
from aklo.models import build_model
from aklo.models.akloms import _eligible_additions


def _config(**overrides):
    config = {
        "loss": "hinge",
        "meta_loss": "hinge",
        "eta": 1.0,
        "lambda": 0.0,
        "delta_alpha": 0.001,
        "tau": 0.001,
    }
    config.update(overrides)
    return config


def test_tau_zero_matches_aklo_predictions() -> None:
    stream = prepare_stream(
        make_synthetic("syn1", n_tasks=4, n_samples=15, seed=1), seed=1
    )
    aklo = build_model("aklo", 2, "classification", _config())
    akloms = build_model("akloms", 2, "classification", _config(tau=0.0))

    for task_index, task in enumerate(stream.tasks):
        aklo.start_task(task_index, task.n_train, task.task_id, task.category)
        akloms.start_task(task_index, task.n_train, task.task_id, task.category)
        for index in range(task.n_train):
            x = task.X_train[index]
            y = float(task.y_train[index])
            assert aklo.predict(x) == akloms.predict(x)
            aklo.update(x, y)
            akloms.update(x, y)
        aklo.end_task()
        akloms.end_task()


def test_tau_zero_cover_is_full_knowledge_base() -> None:
    model = build_model("akloms", 2, "classification", _config(tau=0.0))
    for task_index in range(3):
        model.start_task(task_index, n_samples=5)
        assert model.cover_indices == list(range(len(model.knowledge_base)))
        model.update(np.array([1.0, 0.0]), 1.0)
        model.end_task()
    assert model.state()["kb_size"] == 3


def test_positive_tau_keeps_a_subset() -> None:
    model = build_model("akloms", 2, "classification", _config(tau=100.0))
    for task_index in range(4):
        model.start_task(task_index, n_samples=5)
        model.update(np.array([1.0, 0.0]), 1.0)
        model.end_task()
        state = model.state()
        if task_index == 0:
            # No previous models exist at the first task.
            assert state["cover_size"] == 0
        else:
            assert 0 < state["cover_size"] <= state["kb_size"]
    # A huge tau should never add a second model to the cover.
    assert state["cover_size"] == 1


def test_small_tau_can_grow_cover() -> None:
    model = build_model("akloms", 2, "classification", _config(tau=1e-6))
    for task_index in range(5):
        model.start_task(task_index, n_samples=10)
        label = 1.0 if task_index % 2 == 0 else -1.0
        for _ in range(10):
            model.update(np.array([1.0, 0.0]), label)
        model.end_task()
    # Alternating labels produce models with different weights.
    assert model.state()["cover_size"] > 1


def test_selected_models_are_cover() -> None:
    model = build_model("akloms", 2, "classification", _config(tau=0.0))
    for task_index in range(3):
        model.start_task(task_index, n_samples=5)
        model.update(np.array([1.0, 0.0]), 1.0)
        model.end_task()
    model.start_task(3, n_samples=5)
    selected = model.selected_models()
    assert len(selected) == len(model.cover_indices)
    for snapshot, index in zip(selected, model.cover_indices):
        assert snapshot is model.knowledge_base[index]


def test_current_model_is_added_after_task_only() -> None:
    model = build_model("akloms", 2, "classification", _config(tau=0.0))
    model.start_task(0, n_samples=5)
    model.update(np.array([1.0, 0.0]), 1.0)
    assert len(model.knowledge_base) == 0
    model.end_task()
    assert len(model.knowledge_base) == 1


def test_eligible_additions_matches_pairwise_check() -> None:
    rng = np.random.default_rng(0)
    predictions = rng.normal(size=50)
    cover = sorted(rng.choice(50, size=10, replace=False).tolist())
    for tau in (0.001, 0.1, 1.0, 10.0):
        brute = np.all(
            np.abs(predictions[:, None] - predictions[cover][None, :])
            >= 2.0 * tau,
            axis=1,
        )
        brute[cover] = False
        got = _eligible_additions(predictions, cover, tau)
        assert np.array_equal(got, np.flatnonzero(brute))


def test_eligible_additions_boundary_is_inclusive() -> None:
    predictions = np.array([0.0, 2.0, 4.0])
    # Distance exactly 2*tau still counts as "at least 2*tau".
    assert _eligible_additions(predictions, [0], 1.0).tolist() == [1, 2]
