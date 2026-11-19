"""Baseline online learners used in Section 6.

ITOL, TOL and Unif_Sum are direct implementations of the paper's
descriptions. TranOL and OTB are faithful online transfer/boosting-style
reimplementations; the paper does not specify their full hyperparameters, so
the approximations are documented in the README.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from ..metrics import entropy
from .linear import LinearSnapshot, OnlineLinearModel


class _Base:
    """Shared configuration and task bookkeeping for the baselines."""

    name = "base"

    def __init__(
        self,
        dim: int,
        task_type: str,
        config: dict[str, Any],
        seed: int = 0,
    ) -> None:
        """Store the shared loss, learning rate, and regularization settings."""
        self.dim = int(dim)
        self.task_type = task_type
        self.config = dict(config)
        self.seed = int(seed)
        self.loss = self.config.get(
            "loss", "hinge" if task_type == "classification" else "absolute"
        )
        self.eta = float(self.config.get("eta", 1.0))
        self.lambda_ = float(self.config.get("lambda", 0.001))
        self.current_task_id: str | None = None
        self.current_category: str | None = None

    def _new_model(self, eta: float | None = None) -> OnlineLinearModel:
        """Create an online linear model with the shared settings."""
        return OnlineLinearModel(
            self.dim,
            loss=self.loss,
            eta=self.eta if eta is None else eta,
            lambda_=self.lambda_,
        )

    def start_task(
        self,
        task_index: int,
        n_samples: int,
        task_id: str | None = None,
        category: str | None = None,
    ) -> None:
        """Record the task metadata shared by all baseline implementations."""
        self.current_task_id = task_id
        self.current_category = category

    def selected_models(self) -> list[LinearSnapshot]:
        """Return the retained models; the base class retains none."""
        return []

    def final_predictor(self, task_index: int) -> Any:
        """Predictor used for task ``task_index`` after the whole stream.

        Most methods keep one final online model, so the default is ``self``.
        ITOL and TranOL override this because their final prediction rule is
        method-specific.
        """
        return self


class ITOL(_Base):
    """Independent task online learning."""

    name = "itol"

    def __init__(self, *args, **kwargs) -> None:
        """Initialize ITOL with an empty task-snapshot list."""
        super().__init__(*args, **kwargs)
        self.current: OnlineLinearModel | None = None
        self.snapshots: list[LinearSnapshot] = []

    def start_task(self, *args, **kwargs) -> None:
        """Start a fresh predictor for the new task."""
        super().start_task(*args, **kwargs)
        self.current = self._new_model()

    def predict(self, x: Any) -> float:
        """Predict with the current task's independent model."""
        assert self.current is not None
        return self.current.predict(x)

    def update(self, x: Any, y: float) -> None:
        """Update only the current task's independent model."""
        assert self.current is not None
        self.current.update(x, y)

    def end_task(self) -> LinearSnapshot:
        """Freeze the task model and append it to the snapshot list."""
        assert self.current is not None
        snapshot = self.current.snapshot(self.current_task_id, self.current_category)
        self.snapshots.append(snapshot)
        return snapshot

    def state(self) -> dict[str, float | int | str | None]:
        """Return ITOL diagnostics for the current task."""
        return {
            "kb_size": len(self.snapshots),
            "w_norm": self.current.norm() if self.current is not None else 0.0,
            "n_updates": self.current.n_updates if self.current is not None else 0,
            "task_id": self.current_task_id,
            "category": self.current_category,
        }

    def selected_models(self) -> list[LinearSnapshot]:
        """Return every task-specific snapshot."""
        return list(self.snapshots)

    def final_predictor(self, task_index: int) -> LinearSnapshot:
        """ITOL keeps a separate task-specific model for every task."""
        if task_index < 0 or task_index >= len(self.snapshots):
            raise IndexError(
                f"ITOL has {len(self.snapshots)} task snapshots, "
                f"cannot select index {task_index}"
            )
        return self.snapshots[task_index]


class TOL(_Base):
    """Task online learning: one model over the concatenated stream."""

    name = "tol"

    def __init__(self, *args, **kwargs) -> None:
        """Initialize the single model shared by every task."""
        super().__init__(*args, **kwargs)
        self.current = self._new_model()
        self.snapshots: list[LinearSnapshot] = []

    def predict(self, x: Any) -> float:
        """Predict with the single shared online model."""
        return self.current.predict(x)

    def update(self, x: Any, y: float) -> None:
        """Update the shared online model."""
        self.current.update(x, y)

    def end_task(self) -> LinearSnapshot:
        """Save a snapshot of the shared model at the end of the task."""
        snapshot = self.current.snapshot(self.current_task_id, self.current_category)
        self.snapshots.append(snapshot)
        return snapshot

    def state(self) -> dict[str, float | int | str | None]:
        """Return TOL diagnostics for the shared model."""
        return {
            "kb_size": 1,
            "w_norm": self.current.norm(),
            "n_updates": self.current.n_updates,
            "task_id": self.current_task_id,
            "category": self.current_category,
        }

    def selected_models(self) -> list[LinearSnapshot]:
        """Return a snapshot of the single shared model."""
        return [self.current.snapshot(self.current_task_id, self.current_category)]


class UnifSum(_Base):
    """Uniform average of all previous task predictors.

    A current predictor is still trained online so that it can be added to
    the knowledge base; it is not used for the prediction.
    """

    name = "unif_sum"

    def __init__(self, *args, **kwargs) -> None:
        """Initialize the knowledge base and the unused current predictor."""
        super().__init__(*args, **kwargs)
        self.current: OnlineLinearModel | None = None
        self.snapshots: list[LinearSnapshot] = []

    def start_task(self, *args, **kwargs) -> None:
        """Start the auxiliary current predictor for the new task."""
        super().start_task(*args, **kwargs)
        self.current = self._new_model()

    def predict(self, x: Any) -> float:
        """Return the uniform average of all previous task predictors."""
        if not self.snapshots:
            return 0.0
        return float(np.mean([snapshot.predict(x) for snapshot in self.snapshots]))

    def update(self, x: Any, y: float) -> None:
        """Update only the auxiliary current predictor."""
        assert self.current is not None
        self.current.update(x, y)

    def end_task(self) -> LinearSnapshot:
        """Append the auxiliary predictor to the knowledge base."""
        assert self.current is not None
        snapshot = self.current.snapshot(self.current_task_id, self.current_category)
        self.snapshots.append(snapshot)
        return snapshot

    def state(self) -> dict[str, float | int | str | None]:
        """Return Unif_Sum diagnostics for the auxiliary predictor."""
        return {
            "kb_size": len(self.snapshots),
            "w_norm": self.current.norm() if self.current is not None else 0.0,
            "n_updates": self.current.n_updates if self.current is not None else 0,
            "task_id": self.current_task_id,
            "category": self.current_category,
        }

    def selected_models(self) -> list[LinearSnapshot]:
        """Return every snapshot in the uniform average."""
        return list(self.snapshots)


@dataclass
class TransOLSnapshotPredictor:
    """Frozen source/target predictor for one task.

    The source is the previous task's final model and the target is the model
    trained online on the current task.  Prediction is the fixed 0.5/0.5
    combination used during training; it never updates either model.
    """

    source: LinearSnapshot | None
    target: LinearSnapshot

    def predict(self, x: Any) -> float:
        """Return the fixed 0.5/0.5 source/target prediction."""
        if self.source is None:
            return self.target.predict(x)
        return 0.5 * self.source.predict(x) + 0.5 * self.target.predict(x)


class TranOL(_Base):
    """Online transfer learning from the previous task.

    The previous task's final predictor is used as the source domain. The
    target predictor is initialized from the source and updated online; the
    prediction is the average of the source and target outputs. This is a
    practical OTL-style reimplementation of [Zhao et al., 2014].
    """

    name = "tranol"

    def __init__(self, *args, **kwargs) -> None:
        """Initialize TranOL with no source and an empty snapshot list."""
        super().__init__(*args, **kwargs)
        self.current: OnlineLinearModel | None = None
        self.source: LinearSnapshot | None = None
        self.snapshots: list[LinearSnapshot] = []
        self.task_predictors: list[TransOLSnapshotPredictor] = []

    def start_task(self, *args, **kwargs) -> None:
        """Initialize the target predictor from the previous task's model."""
        super().start_task(*args, **kwargs)
        self.current = self._new_model()
        if self.snapshots:
            self.source = self.snapshots[-1]
            self.current.load_snapshot(self.source)
        else:
            self.source = None

    def predict(self, x: Any) -> float:
        """Average the source and target predictions for one observation."""
        assert self.current is not None
        if self.source is None:
            return self.current.predict(x)
        return 0.5 * self.source.predict(x) + 0.5 * self.current.predict(x)

    def update(self, x: Any, y: float) -> None:
        """Update the target predictor online."""
        assert self.current is not None
        self.current.update(x, y)

    def end_task(self) -> LinearSnapshot:
        """Freeze the target model and the source/target pair."""
        assert self.current is not None
        snapshot = self.current.snapshot(self.current_task_id, self.current_category)
        self.snapshots.append(snapshot)
        # Freeze the source/target pair as it stands at the end of this task.
        # ``source`` still points at the previous task here; ``start_task``
        # advances it only for the next task.
        self.task_predictors.append(
            TransOLSnapshotPredictor(self.source, snapshot)
        )
        return snapshot

    def state(self) -> dict[str, float | int | str | None]:
        """Return TranOL diagnostics for the target predictor."""
        return {
            "kb_size": 1 if self.source is not None else 0,
            "w_norm": self.current.norm() if self.current is not None else 0.0,
            "n_updates": self.current.n_updates if self.current is not None else 0,
            "task_id": self.current_task_id,
            "category": self.current_category,
        }

    def selected_models(self) -> list[LinearSnapshot]:
        """Return every task-specific target snapshot."""
        return list(self.snapshots)

    def final_predictor(self, task_index: int) -> TransOLSnapshotPredictor:
        """Frozen source/target predictor saved at the end of ``task_index``."""
        if task_index < 0 or task_index >= len(self.task_predictors):
            raise IndexError(
                f"TranOL has {len(self.task_predictors)} task predictors, "
                f"cannot select index {task_index}"
            )
        return self.task_predictors[task_index]


@dataclass
class OTBSnapshotPredictor:
    """Frozen weighted ensemble of weak learners for one task.

    ``learners`` are the weak learners at the end of the task and ``weights``
    are the boosting weights at the same instant.  ``predict`` is read-only.
    """

    learners: list[LinearSnapshot]
    weights: np.ndarray

    def predict(self, x: Any) -> float:
        """Return the frozen weighted ensemble prediction."""
        predictions = np.asarray([learner.predict(x) for learner in self.learners])
        return float(np.dot(self.weights, predictions))


class OTB(_Base):
    """Online transfer boosting-style ensemble.

    The paper cites online boosting for anytime transfer and multitask
    learning [Wang & Pineau, 2015]. The exact algorithm is not restated in the
    paper, so this baseline uses an online ensemble of linear learners with
    exponential weights and transfer from the previous task's ensemble.
    """

    name = "otb"

    def __init__(self, *args, **kwargs) -> None:
        """Initialize the weak-learner ensemble and its uniform weights."""
        super().__init__(*args, **kwargs)
        self.n_learners = int(self.config.get("n_learners", 10))
        self.learners: list[OnlineLinearModel] = []
        self.weights = np.full(self.n_learners, 1.0 / self.n_learners)
        self.E = np.zeros(self.n_learners, dtype=np.float64)
        self.snapshots: list[LinearSnapshot] = []
        self.task_predictors: list[OTBSnapshotPredictor] = []

    def _make_learners(self) -> list[OnlineLinearModel]:
        """Create weak learners with a spread of learning rates."""
        learners = []
        for index in range(self.n_learners):
            eta = self.eta * (0.5 + 0.1 * index)
            learners.append(self._new_model(eta=eta))
        return learners

    def start_task(self, *args, **kwargs) -> None:
        """Initialize learners from the previous ensemble or from scratch."""
        super().start_task(*args, **kwargs)
        if self.snapshots:
            self.learners = []
            for index in range(self.n_learners):
                eta = self.eta * (0.5 + 0.1 * index)
                learner = self._new_model(eta=eta)
                learner.load_snapshot(self.snapshots[index % len(self.snapshots)])
                self.learners.append(learner)
        else:
            self.learners = self._make_learners()
        self.weights = np.full(self.n_learners, 1.0 / self.n_learners)
        self.E = np.zeros(self.n_learners, dtype=np.float64)

    def predict(self, x: Any) -> float:
        """Return the current weighted ensemble prediction."""
        predictions = np.asarray([learner.predict(x) for learner in self.learners])
        return float(np.dot(self.weights, predictions))

    def update(self, x: Any, y: float) -> None:
        """Update boosting weights and every weak learner."""
        predictions = np.asarray([learner.predict(x) for learner in self.learners])
        self.E += (float(y) - predictions) ** 2
        logits = -self.E
        logits = np.nan_to_num(logits, nan=0.0, posinf=0.0, neginf=-1e12)
        maximum = float(np.max(logits))
        exponentials = np.exp(logits - maximum)
        total = float(np.sum(exponentials))
        self.weights = (
            exponentials / total
            if total > 0.0 and np.isfinite(total)
            else np.full(self.n_learners, 1.0 / self.n_learners)
        )
        for learner in self.learners:
            learner.update(x, y)

    def end_task(self) -> LinearSnapshot:
        """Freeze the ensemble and its boosting weights for this task."""
        self.snapshots = [
            learner.snapshot(self.current_task_id, self.current_category)
            for learner in self.learners
        ]
        # Freeze the ensemble and its boosting weights at the end of this
        # task.  The snapshots are immutable copies, so the predictor remains
        # valid when ``self.snapshots`` is overwritten by the next task.
        self.task_predictors.append(
            OTBSnapshotPredictor(list(self.snapshots), self.weights.copy())
        )
        return self.snapshots[0]

    def state(self) -> dict[str, float | int | str | None]:
        """Return OTB diagnostics for the weak-learner ensemble."""
        return {
            "kb_size": len(self.snapshots),
            "n_learners": self.n_learners,
            "weight_entropy": entropy(self.weights),
            "weight_max": float(np.max(self.weights)),
            "w_norm": float(np.mean([learner.norm() for learner in self.learners])),
            "n_updates": int(np.sum([learner.n_updates for learner in self.learners])),
            "task_id": self.current_task_id,
            "category": self.current_category,
        }

    def selected_models(self) -> list[LinearSnapshot]:
        """Return the weak-learner snapshots saved for this task."""
        return list(self.snapshots)

    def final_predictor(self, task_index: int) -> OTBSnapshotPredictor:
        """Frozen weighted ensemble saved at the end of ``task_index``."""
        if task_index < 0 or task_index >= len(self.task_predictors):
            raise IndexError(
                f"OTB has {len(self.task_predictors)} task predictors, "
                f"cannot select index {task_index}"
            )
        return self.task_predictors[task_index]
