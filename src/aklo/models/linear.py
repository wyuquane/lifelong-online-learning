"""Online linear predictors with lazy weight decay.

The paper updates the current predictor as

    w_{i+1} = (1 - lambda * eta) w_i - eta * grad(loss)

For sparse data (Spam has 152,543 features), multiplying the full weight
vector by the decay factor at every step is wasteful. We store the effective
weights as ``s * u`` and apply the decay to the scalar ``s`` only. Non-zero
coordinates of ``u`` are updated lazily. The representation is exact.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy import sparse


def _dot(weights: np.ndarray, x: Any) -> float:
    if sparse.issparse(x):
        row = x.tocsr()
        if row.shape[0] != 1:
            row = row.reshape(1, -1)
        return float(row.data @ weights[row.indices])
    return float(np.dot(weights, np.asarray(x).ravel()))


def _nonzero(x: Any) -> tuple[np.ndarray, np.ndarray]:
    if sparse.issparse(x):
        row = x.tocsr()
        if row.shape[0] != 1:
            row = row.reshape(1, -1)
        return row.indices, row.data
    values = np.asarray(x).ravel()
    indices = np.flatnonzero(values)
    return indices, values[indices]


@dataclass
class LinearSnapshot:
    """Immutable copy of a linear predictor."""

    u: np.ndarray
    s: float
    task_id: str | None = None
    category: str | None = None

    def predict(self, x: Any) -> float:
        return self.s * _dot(self.u, x)

    @property
    def weights(self) -> np.ndarray:
        return self.s * self.u


class OnlineLinearModel:
    """Online linear predictor for hinge or absolute loss."""

    def __init__(
        self,
        dim: int,
        loss: str = "hinge",
        eta: float = 1.0,
        lambda_: float = 0.001,
    ) -> None:
        if loss not in {"hinge", "absolute"}:
            raise ValueError(f"Unknown loss: {loss}")
        self.dim = int(dim)
        self.loss = loss
        self.eta = float(eta)
        self.lambda_ = float(lambda_)
        self.u = np.zeros(self.dim, dtype=np.float64)
        self.s = 1.0
        self.n_updates = 0

    def predict(self, x: Any) -> float:
        return self.s * _dot(self.u, x)

    def _apply_decay(self) -> None:
        decay = 1.0 - self.lambda_ * self.eta
        if decay <= 0.0:
            self.u.fill(0.0)
            self.s = 1.0
            return
        self.s *= decay
        if self.s < 1e-12:
            self.u *= self.s
            self.s = 1.0

    def update(self, x: Any, y: float) -> None:
        prediction = self.predict(x)
        if self.loss == "hinge":
            coefficient = -float(y) if float(y) * prediction < 1.0 else 0.0
        else:
            difference = float(y) - prediction
            coefficient = -float(np.sign(difference)) if difference != 0.0 else 0.0

        self._apply_decay()
        if coefficient != 0.0:
            indices, values = _nonzero(x)
            self.u[indices] -= self.eta * coefficient * values / self.s
        self.n_updates += 1

    def snapshot(self, task_id: str | None = None, category: str | None = None) -> LinearSnapshot:
        return LinearSnapshot(
            u=self.u.copy(),
            s=float(self.s),
            task_id=task_id,
            category=category,
        )

    def load_snapshot(self, snapshot: LinearSnapshot) -> None:
        self.u = snapshot.u.copy()
        self.s = float(snapshot.s)
        self.n_updates = 0

    @property
    def weights(self) -> np.ndarray:
        return self.s * self.u

    def norm(self) -> float:
        return abs(self.s) * float(np.linalg.norm(self.u))
