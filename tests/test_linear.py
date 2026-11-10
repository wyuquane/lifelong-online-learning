"""Tests for the online linear predictor and its lazy weight decay."""

from __future__ import annotations

import numpy as np
from scipy import sparse

from aklo.models.linear import LinearSnapshot, OnlineLinearModel


def test_initial_prediction_is_zero() -> None:
    model = OnlineLinearModel(3)
    assert model.predict(np.array([1.0, 2.0, 3.0])) == 0.0


def test_hinge_update_without_decay() -> None:
    model = OnlineLinearModel(2, loss="hinge", eta=1.0, lambda_=0.0)
    x = np.array([1.0, 0.0])
    model.update(x, 1.0)
    np.testing.assert_allclose(model.weights, [1.0, 0.0])
    # The margin is now exactly 1, so a second identical update does nothing.
    model.update(x, 1.0)
    np.testing.assert_allclose(model.weights, [1.0, 0.0])


def test_hinge_update_with_decay_matches_closed_form() -> None:
    model = OnlineLinearModel(1, loss="hinge", eta=1.0, lambda_=0.5)
    x = np.array([1.0])
    model.update(x, 1.0)
    np.testing.assert_allclose(model.weights, [1.0])
    model.update(x, -1.0)
    # w <- (1 - lambda*eta) w + eta*y*x
    np.testing.assert_allclose(model.weights, [-0.5])


def test_absolute_loss_update() -> None:
    model = OnlineLinearModel(1, loss="absolute", eta=1.0, lambda_=0.0)
    model.update(np.array([1.0]), 2.0)
    np.testing.assert_allclose(model.weights, [1.0])
    model.update(np.array([1.0]), 0.0)
    np.testing.assert_allclose(model.weights, [0.0])


def test_snapshot_round_trip() -> None:
    model = OnlineLinearModel(2, loss="hinge", eta=1.0, lambda_=0.0)
    model.update(np.array([1.0, -1.0]), 1.0)
    snapshot = model.snapshot("task-a", "D1")
    assert snapshot.task_id == "task-a"
    assert snapshot.category == "D1"
    np.testing.assert_allclose(snapshot.weights, model.weights)
    restored = OnlineLinearModel(2)
    restored.load_snapshot(snapshot)
    np.testing.assert_allclose(restored.weights, model.weights)
    assert restored.n_updates == 0


def test_sparse_and_dense_updates_agree() -> None:
    dense = OnlineLinearModel(4, loss="hinge", eta=0.3, lambda_=0.01)
    sparse_model = OnlineLinearModel(4, loss="hinge", eta=0.3, lambda_=0.01)
    x_dense = np.array([0.0, 1.0, 0.0, -2.0])
    x_sparse = sparse.csr_matrix(x_dense.reshape(1, -1))
    for _ in range(5):
        dense.update(x_dense, 1.0)
        sparse_model.update(x_sparse, 1.0)
    np.testing.assert_allclose(dense.weights, sparse_model.weights)
    assert np.isclose(dense.predict(x_dense), sparse_model.predict(x_sparse))


def test_snapshot_is_immutable_copy() -> None:
    model = OnlineLinearModel(1, loss="hinge", eta=1.0, lambda_=0.0)
    model.update(np.array([1.0]), 1.0)
    snapshot = model.snapshot()
    model.update(np.array([1.0]), -1.0)
    np.testing.assert_allclose(snapshot.weights, [1.0])
    assert not np.allclose(snapshot.weights, model.weights)
    assert isinstance(snapshot, LinearSnapshot)
