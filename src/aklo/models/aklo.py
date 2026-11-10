"""AKLO: Accumulating Knowledge for Lifelong Online Learning."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from .linear import LinearSnapshot, OnlineLinearModel
from .meta import MetaHypothesis


class AKLO:
    """Algorithm 1 for the first task and Algorithm 2 for later tasks.

    The first task has no knowledge base and therefore trains only the current
    predictor. From the second task onward, the prediction is

        alpha * meta_prediction + (1 - alpha) * current_prediction

    and ``alpha`` decays by ``delta_alpha`` after every observation.
    """

    name = "aklo"

    def __init__(
        self,
        dim: int,
        task_type: str,
        config: dict[str, Any],
        seed: int = 0,
    ) -> None:
        self.dim = int(dim)
        self.task_type = task_type
        self.config = dict(config)
        self.seed = int(seed)
        self.loss = self.config.get("loss", "hinge" if task_type == "classification" else "absolute")
        self.eta = float(self.config.get("eta", 1.0))
        self.lambda_ = float(self.config.get("lambda", 0.001))
        self.delta_alpha = float(self.config.get("delta_alpha", 0.001))
        self.meta_loss = str(self.config.get("meta_loss", "squared"))

        self.snapshots: list[LinearSnapshot] = []
        self.current: OnlineLinearModel | None = None
        self.meta: MetaHypothesis | None = None
        self.alpha = 1.0
        self.alpha_sum = 0.0
        self.epsilon = 0.0
        self.task_index = 0
        self.current_task_id: str | None = None
        self.current_category: str | None = None
        self._snapshot_matrix: np.ndarray | None = None

    def _matrix(self) -> np.ndarray:
        """Effective weights of all previous predictors, one row each."""
        if self._snapshot_matrix is None:
            if self.snapshots:
                self._snapshot_matrix = np.vstack(
                    [snapshot.weights for snapshot in self.snapshots]
                )
            else:
                self._snapshot_matrix = np.zeros((0, self.dim), dtype=np.float64)
        return self._snapshot_matrix

    def _alpha_sum(self, n_samples: int) -> float:
        return float(
            sum(max(0.0, 1.0 - self.delta_alpha * i) for i in range(n_samples))
        )

    def _full_knowledge_epsilon(self) -> float:
        """epsilon used by Algorithm 2 with the full knowledge base.

        ``task_index`` is zero-based. The paper's task number is
        ``task_index + 1``, so the paper's ``log(t - 1)`` becomes
        ``log(task_index)``. The second task (``task_index = 1``) therefore
        has epsilon zero, as in Algorithm 2.
        """
        if self.alpha_sum <= 0.0 or self.task_index < 1:
            return 0.0
        return math.sqrt(
            math.log(max(1, self.task_index)) / (2.0 * self.alpha_sum)
        )

    def start_task(
        self,
        task_index: int,
        n_samples: int,
        task_id: str | None = None,
        category: str | None = None,
    ) -> None:
        """Reset the current predictor and build the meta-hypothesis."""
        self.task_index = int(task_index)
        self.current_task_id = task_id
        self.current_category = category
        self.current = OnlineLinearModel(
            self.dim, loss=self.loss, eta=self.eta, lambda_=self.lambda_
        )
        self.alpha = 1.0
        self.alpha_sum = self._alpha_sum(n_samples)

        if self.snapshots:
            # Task 1 uses Algorithm 1. For task t >= 2 the paper uses
            # log(t - 1), which is zero when only one previous model exists.
            self.epsilon = self._full_knowledge_epsilon()
            self.meta = MetaHypothesis(
                self.snapshots,
                self.epsilon,
                weights_matrix=self._matrix(),
                loss=self.meta_loss,
            )
        else:
            self.epsilon = 0.0
            self.meta = None

    def predict(self, x: Any) -> float:
        if self.current is None:
            raise RuntimeError("start_task must be called before predict")
        current_prediction = self.current.predict(x)
        if self.meta is None:
            return current_prediction
        meta_prediction = self.meta.predict(x)
        return self.alpha * meta_prediction + (1.0 - self.alpha) * current_prediction

    def update(self, x: Any, y: float) -> None:
        if self.current is None:
            raise RuntimeError("start_task must be called before update")
        if self.meta is not None:
            self.meta.update(x, y)
        self.current.update(x, y)
        self.alpha = max(0.0, self.alpha - self.delta_alpha)

    def end_task(self) -> LinearSnapshot:
        if self.current is None:
            raise RuntimeError("start_task must be called before end_task")
        snapshot = self.current.snapshot(
            task_id=self.current_task_id, category=self.current_category
        )
        self.snapshots.append(snapshot)
        self._snapshot_matrix = None
        return snapshot

    def state(self) -> dict[str, float | int | str | None]:
        return {
            "alpha": self.alpha,
            "epsilon": self.epsilon,
            "kb_size": len(self.snapshots),
            "beta_entropy": self.meta.beta_entropy if self.meta is not None else 0.0,
            "beta_max": self.meta.beta_max if self.meta is not None else 0.0,
            "w_norm": self.current.norm() if self.current is not None else 0.0,
            "n_updates": self.current.n_updates if self.current is not None else 0,
            "task_id": self.current_task_id,
            "category": self.current_category,
        }

    def selected_models(self) -> list[LinearSnapshot]:
        return list(self.snapshots)

    def task_predictor(self) -> LinearSnapshot:
        """Task-specific predictor ``f_t`` saved at the end of task ``t``."""
        if not self.snapshots:
            raise RuntimeError("No task predictor is available")
        return self.snapshots[-1]
