"""AKLOMS: AKLO with a covering-set knowledge base.

Algorithm 3 keeps a ``2 * tau`` packing of the accumulated knowledge base.
At the beginning of task ``t`` the cover contains one random element of the
knowledge base.  During the task, every previous model whose prediction is at
least ``2 * tau`` away from every model already in the cover is added, and the
meta-hypothesis is restarted.

The current task's predictor is added to the knowledge base at the end of the
task but not to the cover used during that task (this follows the decision
recorded in ``docs/paper_decisions.md``).

``tau = 0`` is a special case: the cover is the whole knowledge base from the
start of the task, which makes AKLOMS identical to AKLO as stated in the
paper.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy import sparse

from ..seeding import rng_for
from .aklo import AKLO
from .linear import LinearSnapshot
from .meta import MetaHypothesis, _predict_rows


def _eligible_additions(
    predictions: np.ndarray,
    cover_indices: list[int],
    tau: float,
) -> np.ndarray:
    """Knowledge-base indices at distance ``>= 2*tau`` from every cover model.

    This is the exact vectorized equivalent of the pairwise check.  The cover
    is a ``2*tau`` packing, so its predictions are separated; the nearest cover
    prediction can therefore be found with a binary search instead of building
    the full ``|knowledge base| x |cover|`` distance matrix.  The latter is
    quadratic and dominates the runtime at small ``tau``, whereas the paper
    treats distance comparison as negligible next to prediction.
    """
    if not cover_indices:
        return np.zeros(0, dtype=np.int64)
    cover_predictions = np.sort(predictions[cover_indices])
    positions = np.searchsorted(cover_predictions, predictions, side="left")
    right = np.clip(positions, 0, cover_predictions.size - 1)
    left = np.clip(positions - 1, 0, cover_predictions.size - 1)
    distance = np.minimum(
        np.abs(predictions - cover_predictions[left]),
        np.abs(predictions - cover_predictions[right]),
    )
    eligible = distance >= 2.0 * tau
    eligible[cover_indices] = False
    return np.flatnonzero(eligible)


class AKLOMS(AKLO):
    """Algorithm 3: keep a 2*tau cover of the previous models."""

    name = "akloms"

    def __init__(
        self,
        dim: int,
        task_type: str,
        config: dict[str, Any],
        seed: int = 0,
    ) -> None:
        super().__init__(dim, task_type, config, seed)
        self.tau = float(self.config.get("tau", 0.001))
        self.knowledge_base: list[LinearSnapshot] = []
        self.cover_indices: list[int] = []
        self._knowledge_matrix: np.ndarray | None = None

    # ------------------------------------------------------------------
    # Knowledge-base helpers
    # ------------------------------------------------------------------
    def _matrix(self) -> np.ndarray:
        if self._knowledge_matrix is None:
            if self.knowledge_base:
                self._knowledge_matrix = np.vstack(
                    [snapshot.weights for snapshot in self.knowledge_base]
                )
            else:
                self._knowledge_matrix = np.zeros((0, self.dim), dtype=np.float64)
        return self._knowledge_matrix

    def _cover_snapshots(self) -> list[LinearSnapshot]:
        return [self.knowledge_base[index] for index in self.cover_indices]

    def _epsilon(self) -> float:
        if not self.cover_indices or self.alpha_sum <= 0.0:
            return 0.0
        if self.tau <= 0.0:
            # The paper states that tau = 0 recovers AKLO.  Algorithm 3's
            # |Lambda_t| formula would not reproduce Algorithm 2's
            # log(t - 1) epsilon, so the full-cover case uses Algorithm 2's
            # epsilon.  This choice is documented in docs/paper_decisions.md.
            return self._full_knowledge_epsilon()
        return math.sqrt(len(self.cover_indices) / (2.0 * self.alpha_sum))

    def _rebuild_meta(self) -> None:
        cover = self._cover_snapshots()
        self.epsilon = self._epsilon()
        if cover:
            matrix = self._matrix()[self.cover_indices]
            self.meta = MetaHypothesis(
                cover, self.epsilon, weights_matrix=matrix, loss=self.meta_loss
            )
        else:
            self.meta = None

    # ------------------------------------------------------------------
    # Task interface
    # ------------------------------------------------------------------
    def start_task(
        self,
        task_index: int,
        n_samples: int,
        task_id: str | None = None,
        category: str | None = None,
    ) -> None:
        super().start_task(task_index, n_samples, task_id, category)
        self.cover_indices = []
        if self.knowledge_base:
            if self.tau <= 0.0:
                # tau = 0 recovers AKLO: use the full knowledge base.
                self.cover_indices = list(range(len(self.knowledge_base)))
            else:
                rng = rng_for(self.seed, 500 + int(task_index))
                self.cover_indices = [int(rng.integers(len(self.knowledge_base)))]
        self._rebuild_meta()

    def update(self, x: Any, y: float) -> None:
        if self.current is None:
            raise RuntimeError("start_task must be called before update")

        if self.tau > 0.0 and self.knowledge_base and self.cover_indices:
            predictions = _predict_rows(self._matrix(), x)
            additions = _eligible_additions(
                predictions, self.cover_indices, self.tau
            )
            if additions.size:
                self.cover_indices.extend(int(index) for index in additions)
                self._rebuild_meta()

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
        self.knowledge_base.append(snapshot)
        self._knowledge_matrix = None
        return snapshot

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------
    def state(self) -> dict[str, float | int | str | None]:
        state = super().state()
        state.update(
            {
                "kb_size": len(self.knowledge_base),
                "cover_size": len(self.cover_indices),
                "selected_ratio": (
                    len(self.cover_indices) / len(self.knowledge_base)
                    if self.knowledge_base
                    else 0.0
                ),
                "tau": self.tau,
            }
        )
        return state

    def selected_models(self) -> list[LinearSnapshot]:
        return self._cover_snapshots()

    def task_predictor(self) -> LinearSnapshot:
        """Task-specific predictor ``f_t`` saved at the end of task ``t``."""
        if not self.knowledge_base:
            raise RuntimeError("No task predictor is available")
        return self.knowledge_base[-1]
