"""Exponential-weights meta-hypothesis.

The meta-hypothesis is a weighted linear combination of the predictors stored
in the knowledge base:

    k_t(x) = sum_q beta_q * f_q(x).

Following Section 6 of the paper, the meta-loss is the squared loss
``e_q = (y - f_q(x)) ** 2``.  The weights are updated with the exponential
gradient rule

    beta_q proportional to exp(-epsilon * E_q),

where ``E_q`` is the cumulative squared loss of predictor ``q`` on the current
task.

For speed, predictions for all members are computed with one matrix-vector
product.  This is mathematically identical to calling ``f_q(x)`` in a loop,
but avoids a Python loop over the knowledge base for every observation.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy import sparse

from ..metrics import entropy
from .linear import LinearSnapshot


def _predict_rows(weights: np.ndarray, x: Any) -> np.ndarray:
    """Return ``weights @ x`` for dense or sparse ``x``."""
    if weights.shape[0] == 0:
        return np.zeros(0, dtype=np.float64)
    if sparse.issparse(x):
        row = x.tocsr()
        if row.shape[0] != 1:
            row = row.reshape(1, -1)
        return weights[:, row.indices] @ row.data
    return weights @ np.asarray(x, dtype=np.float64).ravel()


class MetaHypothesis:
    """Weighted combination of previous task predictors."""

    def __init__(
        self,
        snapshots: list[LinearSnapshot],
        epsilon: float = 0.0,
        weights_matrix: np.ndarray | None = None,
        loss: str = "squared",
    ) -> None:
        self.snapshots = list(snapshots)
        self.epsilon = float(epsilon)
        self.loss = loss
        self.E = np.zeros(len(self.snapshots), dtype=np.float64)
        self.beta = (
            np.full(len(self.snapshots), 1.0 / len(self.snapshots))
            if self.snapshots
            else np.zeros(0, dtype=np.float64)
        )
        self._weights_matrix = weights_matrix

    def _matrix(self) -> np.ndarray:
        if self._weights_matrix is None:
            if self.snapshots:
                self._weights_matrix = np.vstack(
                    [snapshot.weights for snapshot in self.snapshots]
                )
            else:
                self._weights_matrix = np.zeros((0, 0), dtype=np.float64)
        return self._weights_matrix

    def _predictions(self, x: Any) -> np.ndarray:
        return _predict_rows(self._matrix(), x)

    def predict(self, x: Any) -> float:
        if not self.snapshots:
            return 0.0
        return float(np.dot(self.beta, self._predictions(x)))

    def _member_loss(self, y: float, predictions: np.ndarray) -> np.ndarray:
        if self.loss == "squared":
            return (y - predictions) ** 2
        if self.loss == "hinge":
            return np.maximum(0.0, 1.0 - y * predictions)
        if self.loss == "absolute":
            return np.abs(y - predictions)
        if self.loss == "zero_one":
            return (
                np.where(predictions >= 0.0, 1.0, -1.0) != y
            ).astype(np.float64)
        raise ValueError(f"Unknown meta loss: {self.loss}")

    def update(self, x: Any, y: float) -> None:
        if not self.snapshots:
            return
        predictions = self._predictions(x)
        self.E += self._member_loss(float(y), predictions)
        logits = -self.epsilon * self.E
        logits = np.nan_to_num(logits, nan=0.0, posinf=0.0, neginf=-1e12)
        maximum = float(np.max(logits))
        exponentials = np.exp(logits - maximum)
        total = float(np.sum(exponentials))
        if total <= 0.0 or not np.isfinite(total):
            self.beta = np.full(len(self.snapshots), 1.0 / len(self.snapshots))
        else:
            self.beta = exponentials / total

    def reset(
        self,
        snapshots: list[LinearSnapshot],
        epsilon: float,
        weights_matrix: np.ndarray | None = None,
        loss: str | None = None,
    ) -> None:
        self.snapshots = list(snapshots)
        self.epsilon = float(epsilon)
        if loss is not None:
            self.loss = loss
        self.E = np.zeros(len(self.snapshots), dtype=np.float64)
        self.beta = (
            np.full(len(self.snapshots), 1.0 / len(self.snapshots))
            if self.snapshots
            else np.zeros(0, dtype=np.float64)
        )
        self._weights_matrix = weights_matrix

    @property
    def beta_entropy(self) -> float:
        return entropy(self.beta)

    @property
    def beta_max(self) -> float:
        return float(np.max(self.beta)) if self.beta.size else 0.0
