"""Tests for the exponential-weights meta-hypothesis."""

from __future__ import annotations

import math

import numpy as np

from aklo.models.linear import LinearSnapshot
from aklo.models.meta import MetaHypothesis


def _snapshot(weight: float) -> LinearSnapshot:
    return LinearSnapshot(u=np.array([weight], dtype=np.float64), s=1.0)


def test_initial_weights_are_uniform() -> None:
    meta = MetaHypothesis([_snapshot(0.0), _snapshot(1.0)])
    np.testing.assert_allclose(meta.beta, [0.5, 0.5])
    assert meta.predict(np.array([1.0])) == 0.5


def test_zero_epsilon_keeps_weights_uniform() -> None:
    meta = MetaHypothesis([_snapshot(0.0), _snapshot(1.0)], epsilon=0.0)
    for _ in range(10):
        meta.update(np.array([1.0]), 1.0)
    np.testing.assert_allclose(meta.beta, [0.5, 0.5])


def test_squared_loss_update() -> None:
    meta = MetaHypothesis([_snapshot(0.0), _snapshot(1.0)], epsilon=0.5, loss="squared")
    meta.update(np.array([1.0]), 1.0)
    np.testing.assert_allclose(meta.E, [1.0, 0.0])
    expected = np.array([math.exp(-0.5), 1.0])
    expected /= expected.sum()
    np.testing.assert_allclose(meta.beta, expected)
    assert meta.predict(np.array([1.0])) == expected[1]


def test_hinge_loss_update() -> None:
    meta = MetaHypothesis([_snapshot(0.0), _snapshot(1.0)], epsilon=1.0, loss="hinge")
    meta.update(np.array([1.0]), 1.0)
    np.testing.assert_allclose(meta.E, [1.0, 0.0])
    expected = np.array([math.exp(-1.0), 1.0])
    expected /= expected.sum()
    np.testing.assert_allclose(meta.beta, expected)


def test_zero_one_loss_uses_sign() -> None:
    meta = MetaHypothesis([_snapshot(0.0), _snapshot(1.0)], epsilon=1.0, loss="zero_one")
    # sign(0) = +1, so both members are correct for y = +1.
    meta.update(np.array([1.0]), 1.0)
    np.testing.assert_allclose(meta.E, [0.0, 0.0])
    # For y = -1 both members are wrong.
    meta.update(np.array([1.0]), -1.0)
    np.testing.assert_allclose(meta.E, [1.0, 1.0])


def test_absolute_loss_update() -> None:
    meta = MetaHypothesis([_snapshot(0.0), _snapshot(1.0)], epsilon=1.0, loss="absolute")
    meta.update(np.array([1.0]), 1.0)
    np.testing.assert_allclose(meta.E, [1.0, 0.0])


def test_reset_clears_history() -> None:
    meta = MetaHypothesis([_snapshot(0.0), _snapshot(1.0)], epsilon=1.0)
    meta.update(np.array([1.0]), 1.0)
    assert not np.allclose(meta.beta, [0.5, 0.5])
    meta.reset([_snapshot(0.0), _snapshot(1.0)], epsilon=0.0)
    np.testing.assert_allclose(meta.E, [0.0, 0.0])
    np.testing.assert_allclose(meta.beta, [0.5, 0.5])


def test_unknown_loss_raises() -> None:
    meta = MetaHypothesis([_snapshot(0.0)], loss="ranking")
    try:
        meta.update(np.array([1.0]), 1.0)
    except ValueError as error:
        assert "ranking" in str(error)
    else:  # pragma: no cover
        raise AssertionError("Expected ValueError")
