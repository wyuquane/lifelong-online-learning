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
    """Find knowledge-base models that can extend the covering set.

    A model is eligible when its prediction differs from every prediction
    currently in the cover by at least ``2 * tau``.  The cover is a ``2 * tau``
    packing, so checking the nearest sorted cover prediction is equivalent to
    the full pairwise comparison while avoiding a quadratic distance matrix.

    Parameters
    ----------
    predictions : np.ndarray
        Predictions of every knowledge-base model on the current observation.
    cover_indices : list[int]
        Indices of the models currently in the covering set.
    tau : float
        Cover radius from the AKLOMS configuration.

    Returns
    -------
    np.ndarray
        Integer indices of eligible knowledge-base models, in ascending order.
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
        """Initialize AKLOMS with the cover threshold ``tau`` and empty state."""
        super().__init__(dim, task_type, config, seed)
        self.tau = float(self.config.get("tau", 0.001))
        self.knowledge_base: list[LinearSnapshot] = []
        self.cover_indices: list[int] = []
        self._knowledge_matrix: np.ndarray | None = None

    # ------------------------------------------------------------------
    # Knowledge-base helpers
    # ------------------------------------------------------------------
    def _matrix(self) -> np.ndarray:
        """Stack the full knowledge base into a weight matrix."""
        if self._knowledge_matrix is None:
            if self.knowledge_base:
                self._knowledge_matrix = np.vstack(
                    [snapshot.weights for snapshot in self.knowledge_base]
                )
            else:
                self._knowledge_matrix = np.zeros((0, self.dim), dtype=np.float64)
        return self._knowledge_matrix

    def _cover_snapshots(self) -> list[LinearSnapshot]:
        """Return the snapshots currently in the covering set."""
        return [self.knowledge_base[index] for index in self.cover_indices]

    def _epsilon(self) -> float:
        """Return the Algorithm 3 epsilon for the current cover."""
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
        """Rebuild the meta-hypothesis from the current covering set."""
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
        """Prepare AKLOMS for the next task and initialize its cover.

        The method reuses AKLO's task setup, then either includes the full
        knowledge base (``tau = 0``, the AKLO-equivalent case) or draws one
        random model as the initial cover.

        Parameters
        ----------
        task_index : int
            Zero-based position of the task in the stream.
        n_samples : int
            Number of training observations in the task.
        task_id : str | None, optional
            Identifier stored in the task snapshot.
        category : str | None, optional
            Optional task category.

        Returns
        -------
        None
            The model is updated in place.
        """
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
        """Update AKLOMS after one labelled example.

        Before the gradient step, the method checks whether any knowledge-base
        model is far enough from the current cover; eligible models are added
        and the meta-hypothesis is rebuilt.  The meta and current predictors
        are then updated and ``alpha`` is decayed as in AKLO.

        Parameters
        ----------
        x : Any
            One feature vector, dense or single-row sparse.
        y : float
            Observed label (classification) or target (regression).

        Returns
        -------
        None
            The model is updated in place.

        Raises
        ------
        RuntimeError
            If ``start_task`` has not been called.
        """
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
        """Freeze the task predictor and extend the knowledge base.

        Unlike AKLO, AKLOMS does not save a per-task mixture snapshot; the E3
        comparison excludes AKLOMS.  The new snapshot becomes available to the
        cover starting with the next task.

        Returns
        -------
        LinearSnapshot
            The snapshot appended to the full knowledge base.

        Raises
        ------
        RuntimeError
            If ``start_task`` has not been called.
        """
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
        """Return AKLO diagnostics plus cover size and retention ratio."""
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
        """Return the snapshots retained in the covering set."""
        return self._cover_snapshots()

    def final_predictor(self, task_index: int) -> "AKLOMS":
        """AKLOMS is not part of the Table 2 comparison.

        The E3 per-task snapshot protocol is defined for the six Table 2
        methods only.  Returning the live model preserves the previous
        behaviour for diagnostic use.
        """
        return self
