"""AKLO: Accumulating Knowledge for Lifelong Online Learning."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from .linear import LinearSnapshot, OnlineLinearModel
from .meta import MetaHypothesis


@dataclass
class AKLOSnapshotPredictor:
    """Frozen AKLO predictor saved at the end of one task.

    ``meta`` contains the knowledge base used during the task and the beta
    weights reached at the end of the task.  ``current`` is the task's own
    predictor and ``alpha`` the mixing coefficient at the end of the task.
    ``predict`` is read-only: no parameter is updated during evaluation.
    """

    meta: MetaHypothesis | None
    current: LinearSnapshot
    alpha: float

    def predict(self, x: Any) -> float:
        """Predict one observation with the frozen task-end AKLO mixture.

        The meta-hypothesis and current predictor are fixed at the end of the
        task, so this method only evaluates them and never updates parameters.

        Parameters
        ----------
        x : Any
            One feature vector, either a dense array or a single-row sparse
            matrix.

        Returns
        -------
        float
            ``alpha * meta_prediction + (1 - alpha) * current_prediction``.
            When the task had no knowledge base, the current prediction is
            returned directly.
        """
        current_prediction = self.current.predict(x)
        if self.meta is None:
            return current_prediction
        meta_prediction = self.meta.predict(x)
        return self.alpha * meta_prediction + (1.0 - self.alpha) * current_prediction


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
        """Initialize AKLO with the paper's hyperparameters and empty state."""
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
        self.task_snapshots: list[AKLOSnapshotPredictor] = []
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
        """Return ``sum_i max(0, 1 - delta_alpha * i)`` for one task."""
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
        """Prepare AKLO for the next task.

        The current online predictor and ``alpha`` are reset, the cumulative
        alpha normalization is computed for the task, and the meta-hypothesis
        is rebuilt from all previously stored snapshots.  The first task has
        no meta-hypothesis.

        Parameters
        ----------
        task_index : int
            Zero-based position of the task in the stream.
        n_samples : int
            Number of training observations in the task; used to compute
            ``alpha_sum``.
        task_id : str | None, optional
            Identifier stored in the task snapshot.
        category : str | None, optional
            Optional task category (for example ``"D1"`` or ``"D2"``).

        Returns
        -------
        None
            The model is updated in place.
        """
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
        """Predict one observation with the current AKLO mixture.

        Parameters
        ----------
        x : Any
            One feature vector, dense or single-row sparse.

        Returns
        -------
        float
            The alpha-weighted combination of the meta-hypothesis and the
            current task predictor.  Before the second task the current
            prediction is returned directly.

        Raises
        ------
        RuntimeError
            If ``start_task`` has not been called.
        """
        if self.current is None:
            raise RuntimeError("start_task must be called before predict")
        current_prediction = self.current.predict(x)
        if self.meta is None:
            return current_prediction
        meta_prediction = self.meta.predict(x)
        return self.alpha * meta_prediction + (1.0 - self.alpha) * current_prediction

    def update(self, x: Any, y: float) -> None:
        """Update both AKLO components after one labelled example.

        The meta-hypothesis is updated first with the current knowledge base,
        then the current linear predictor receives its online gradient step.
        Finally, ``alpha`` is decayed by ``delta_alpha`` and clipped at zero.

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
        if self.meta is not None:
            self.meta.update(x, y)
        self.current.update(x, y)
        self.alpha = max(0.0, self.alpha - self.delta_alpha)

    def end_task(self) -> LinearSnapshot:
        """Freeze the predictor at the end of the current task.

        The current predictor is snapshotted together with the meta-hypothesis
        and the ``alpha`` value reached after the last update.  The frozen
        snapshot is used by the E3 per-task evaluation, while the live
        knowledge base is extended for the next task.

        Returns
        -------
        LinearSnapshot
            The snapshot also appended to the live knowledge base.

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
        # Freeze the predictor as it stands at the end of this task.  The
        # meta-hypothesis already contains the knowledge base used during the
        # task (tasks 1..q-1) and the beta weights reached after the last
        # observation; f_q is the current predictor.  The live knowledge base
        # is updated only after this snapshot has been taken.
        if self.meta is not None:
            meta = MetaHypothesis(
                self.meta.snapshots,
                epsilon=self.meta.epsilon,
                loss=self.meta.loss,
            )
            meta.beta = self.meta.beta.copy()
            meta.E = self.meta.E.copy()
        else:
            meta = None
        self.task_snapshots.append(
            AKLOSnapshotPredictor(meta, snapshot, float(self.alpha))
        )
        self.snapshots.append(snapshot)
        self._snapshot_matrix = None
        return snapshot

    def state(self) -> dict[str, float | int | str | None]:
        """Return diagnostic scalars for the current model state."""
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
        """Return the full knowledge base (AKLO keeps every model)."""
        return list(self.snapshots)

    def final_predictor(self, task_index: int) -> AKLOSnapshotPredictor:
        """Return the frozen predictor saved at the end of a task.

        Parameters
        ----------
        task_index : int
            Zero-based task index in the stream.

        Returns
        -------
        AKLOSnapshotPredictor
            Read-only predictor containing the knowledge base, beta weights,
            current predictor, and alpha from the end of that task.

        Raises
        ------
        IndexError
            If ``task_index`` is outside the range of saved task snapshots.
        """
        if task_index < 0 or task_index >= len(self.task_snapshots):
            raise IndexError(
                f"AKLO has {len(self.task_snapshots)} task snapshots, "
                f"cannot select index {task_index}"
            )
        return self.task_snapshots[task_index]
