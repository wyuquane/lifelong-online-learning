"""Baseline online learners used in Section 6.

ITOL, TOL and Unif_Sum are direct implementations of the paper's
descriptions. TranOL and OTB are faithful online transfer/boosting-style
reimplementations; the paper does not specify their full hyperparameters, so
the approximations are documented in the README.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from ..metrics import entropy
from .linear import LinearSnapshot, OnlineLinearModel


class _Base:
    name = "base"

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
        self.loss = self.config.get(
            "loss", "hinge" if task_type == "classification" else "absolute"
        )
        self.eta = float(self.config.get("eta", 1.0))
        self.lambda_ = float(self.config.get("lambda", 0.001))
        self.current_task_id: str | None = None
        self.current_category: str | None = None

    def _new_model(self, eta: float | None = None) -> OnlineLinearModel:
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
        self.current_task_id = task_id
        self.current_category = category

    def selected_models(self) -> list[LinearSnapshot]:
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
        super().__init__(*args, **kwargs)
        self.current: OnlineLinearModel | None = None
        self.snapshots: list[LinearSnapshot] = []

    def start_task(self, *args, **kwargs) -> None:
        super().start_task(*args, **kwargs)
        self.current = self._new_model()

    def predict(self, x: Any) -> float:
        assert self.current is not None
        return self.current.predict(x)

    def update(self, x: Any, y: float) -> None:
        assert self.current is not None
        self.current.update(x, y)

    def end_task(self) -> LinearSnapshot:
        assert self.current is not None
        snapshot = self.current.snapshot(self.current_task_id, self.current_category)
        self.snapshots.append(snapshot)
        return snapshot

    def state(self) -> dict[str, float | int | str | None]:
        return {
            "kb_size": len(self.snapshots),
            "w_norm": self.current.norm() if self.current is not None else 0.0,
            "n_updates": self.current.n_updates if self.current is not None else 0,
            "task_id": self.current_task_id,
            "category": self.current_category,
        }

    def selected_models(self) -> list[LinearSnapshot]:
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
        super().__init__(*args, **kwargs)
        self.current = self._new_model()
        self.snapshots: list[LinearSnapshot] = []

    def predict(self, x: Any) -> float:
        return self.current.predict(x)

    def update(self, x: Any, y: float) -> None:
        self.current.update(x, y)

    def end_task(self) -> LinearSnapshot:
        snapshot = self.current.snapshot(self.current_task_id, self.current_category)
        self.snapshots.append(snapshot)
        return snapshot

    def state(self) -> dict[str, float | int | str | None]:
        return {
            "kb_size": 1,
            "w_norm": self.current.norm(),
            "n_updates": self.current.n_updates,
            "task_id": self.current_task_id,
            "category": self.current_category,
        }

    def selected_models(self) -> list[LinearSnapshot]:
        return [self.current.snapshot(self.current_task_id, self.current_category)]


class UnifSum(_Base):
    """Uniform average of all previous task predictors.

    A current predictor is still trained online so that it can be added to
    the knowledge base; it is not used for the prediction.
    """

    name = "unif_sum"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.current: OnlineLinearModel | None = None
        self.snapshots: list[LinearSnapshot] = []

    def start_task(self, *args, **kwargs) -> None:
        super().start_task(*args, **kwargs)
        self.current = self._new_model()

    def predict(self, x: Any) -> float:
        if not self.snapshots:
            return 0.0
        return float(np.mean([snapshot.predict(x) for snapshot in self.snapshots]))

    def update(self, x: Any, y: float) -> None:
        assert self.current is not None
        self.current.update(x, y)

    def end_task(self) -> LinearSnapshot:
        assert self.current is not None
        snapshot = self.current.snapshot(self.current_task_id, self.current_category)
        self.snapshots.append(snapshot)
        return snapshot

    def state(self) -> dict[str, float | int | str | None]:
        return {
            "kb_size": len(self.snapshots),
            "w_norm": self.current.norm() if self.current is not None else 0.0,
            "n_updates": self.current.n_updates if self.current is not None else 0,
            "task_id": self.current_task_id,
            "category": self.current_category,
        }

    def selected_models(self) -> list[LinearSnapshot]:
        return list(self.snapshots)


class TranOL(_Base):
    """Online transfer learning from the previous task.

    The previous task's final predictor is used as the source domain. The
    target predictor is initialized from the source and updated online; the
    prediction is the average of the source and target outputs. This is a
    practical OTL-style reimplementation of [Zhao et al., 2014].
    """

    name = "tranol"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.current: OnlineLinearModel | None = None
        self.source: LinearSnapshot | None = None
        self.snapshots: list[LinearSnapshot] = []

    def start_task(self, *args, **kwargs) -> None:
        super().start_task(*args, **kwargs)
        self.current = self._new_model()
        if self.snapshots:
            self.source = self.snapshots[-1]
            self.current.load_snapshot(self.source)
        else:
            self.source = None

    def predict(self, x: Any) -> float:
        assert self.current is not None
        if self.source is None:
            return self.current.predict(x)
        return 0.5 * self.source.predict(x) + 0.5 * self.current.predict(x)

    def update(self, x: Any, y: float) -> None:
        assert self.current is not None
        self.current.update(x, y)

    def end_task(self) -> LinearSnapshot:
        assert self.current is not None
        snapshot = self.current.snapshot(self.current_task_id, self.current_category)
        self.snapshots.append(snapshot)
        # Keep ``source`` pointing at the previous task so that the post-task
        # evaluation uses the same source/target combination as the online
        # prediction. ``start_task`` advances the source for the next task.
        return snapshot

    def state(self) -> dict[str, float | int | str | None]:
        return {
            "kb_size": 1 if self.source is not None else 0,
            "w_norm": self.current.norm() if self.current is not None else 0.0,
            "n_updates": self.current.n_updates if self.current is not None else 0,
            "task_id": self.current_task_id,
            "category": self.current_category,
        }

    def selected_models(self) -> list[LinearSnapshot]:
        return list(self.snapshots)

    def final_predictor(self, task_index: int) -> OnlineLinearModel:
        """The final target model, without the previous-task source blend."""
        if self.current is None:
            raise RuntimeError("start_task must be called before prediction")
        return self.current


class OTB(_Base):
    """Online transfer boosting-style ensemble.

    The paper cites online boosting for anytime transfer and multitask
    learning [Wang & Pineau, 2015]. The exact algorithm is not restated in the
    paper, so this baseline uses an online ensemble of linear learners with
    exponential weights and transfer from the previous task's ensemble.
    """

    name = "otb"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.n_learners = int(self.config.get("n_learners", 10))
        self.learners: list[OnlineLinearModel] = []
        self.weights = np.full(self.n_learners, 1.0 / self.n_learners)
        self.E = np.zeros(self.n_learners, dtype=np.float64)
        self.snapshots: list[LinearSnapshot] = []

    def _make_learners(self) -> list[OnlineLinearModel]:
        learners = []
        for index in range(self.n_learners):
            eta = self.eta * (0.5 + 0.1 * index)
            learners.append(self._new_model(eta=eta))
        return learners

    def start_task(self, *args, **kwargs) -> None:
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
        predictions = np.asarray([learner.predict(x) for learner in self.learners])
        return float(np.dot(self.weights, predictions))

    def update(self, x: Any, y: float) -> None:
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
        self.snapshots = [
            learner.snapshot(self.current_task_id, self.current_category)
            for learner in self.learners
        ]
        return self.snapshots[0]

    def state(self) -> dict[str, float | int | str | None]:
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
        return list(self.snapshots)
