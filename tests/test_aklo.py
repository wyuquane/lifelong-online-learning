"""Tests for Algorithm 1/2 (AKLO)."""

from __future__ import annotations

import math

import numpy as np

from aklo.models import build_model
from aklo.models.aklo import AKLO


def _config(**overrides):
    config = {
        "loss": "hinge",
        "meta_loss": "hinge",
        "eta": 1.0,
        "lambda": 0.0,
        "delta_alpha": 0.1,
    }
    config.update(overrides)
    return config


def test_first_task_has_no_meta_hypothesis() -> None:
    model = AKLO(2, "classification", _config())
    model.start_task(0, n_samples=10, task_id="t0", category="D1")
    assert model.meta is None
    assert model.epsilon == 0.0
    assert model.alpha == 1.0
    model.update(np.array([1.0, 0.0]), 1.0)
    assert model.alpha == 0.9
    snapshot = model.end_task()
    assert snapshot.task_id == "t0"
    assert len(model.snapshots) == 1


def test_second_task_uses_meta_hypothesis() -> None:
    model = AKLO(2, "classification", _config())
    model.start_task(0, n_samples=10)
    for _ in range(5):
        model.update(np.array([1.0, 0.0]), 1.0)
    model.end_task()

    model.start_task(1, n_samples=10)
    assert model.meta is not None
    assert model.meta.epsilon == 0.0  # log(t - 1) = log(1) = 0
    # alpha = 1 means the prediction is the meta-prediction alone.
    meta_prediction = model.meta.predict(np.array([1.0, 0.0]))
    assert model.predict(np.array([1.0, 0.0])) == meta_prediction


def test_alpha_decays_and_is_clipped() -> None:
    model = AKLO(1, "classification", _config(delta_alpha=0.3))
    model.start_task(0, n_samples=10)
    for _ in range(5):
        model.update(np.array([1.0]), 1.0)
    assert math.isclose(model.alpha, 0.0, abs_tol=1e-12)


def test_epsilon_uses_log_of_previous_task_count() -> None:
    model = AKLO(1, "classification", _config(delta_alpha=0.1))
    model.start_task(0, n_samples=10)
    model.update(np.array([1.0]), 1.0)
    model.end_task()

    model.start_task(1, n_samples=10)
    model.update(np.array([1.0]), 1.0)
    model.end_task()

    model.start_task(2, n_samples=10)
    expected = math.sqrt(math.log(2.0) / (2.0 * 5.5))
    assert math.isclose(model.epsilon, expected, rel_tol=1e-12)
    assert model.meta is not None
    assert math.isclose(model.meta.epsilon, expected, rel_tol=1e-12)


def test_prediction_is_alpha_combination() -> None:
    model = AKLO(1, "classification", _config(delta_alpha=0.0))
    model.start_task(0, n_samples=10)
    model.update(np.array([1.0]), 1.0)
    model.end_task()
    model.start_task(1, n_samples=10)
    # With delta_alpha = 0 the current predictor contributes nothing.
    assert model.alpha == 1.0
    current = model.current.predict(np.array([1.0]))
    meta = model.meta.predict(np.array([1.0]))
    assert model.predict(np.array([1.0])) == meta
    model.update(np.array([1.0]), 1.0)
    assert model.current.predict(np.array([1.0])) != current


def test_build_model_resolves_task_section() -> None:
    config = {
        "classification": {"eta": 0.01, "meta_loss": "hinge"},
        "regression": {"eta": 0.05, "meta_loss": "squared"},
        "tau": 0.5,
    }
    classifier = build_model("aklo", 2, "classification", config)
    regressor = build_model("aklo", 2, "regression", config)
    assert classifier.eta == 0.01
    assert classifier.meta_loss == "hinge"
    assert regressor.eta == 0.05
    assert regressor.meta_loss == "squared"
    # Overrides are applied after the task section.
    overridden = build_model("aklo", 2, "classification", config, overrides={"eta": 2.0})
    assert overridden.eta == 2.0
