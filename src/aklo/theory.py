"""Empirical checks of the paper's theoretical claims.

The paper proves three results for a task ``t`` with ``m_t`` observations:

* Theorem 1: an accumulating-error bound with an expert-regret term and a
  current-predictor regret term.
* Corollary 1.1: a small-interaction bound that applies when ``m_t <= i_0``.
* Corollary 1.2: a cover-set bound for AKLOMS.

This module deliberately instruments a stream instead of changing the main
experiment runner.  It records, for every observation, the current prediction,
the meta prediction, the final prediction, the ``alpha`` actually used, and the
predictions of every model in the knowledge base.  The analysis then computes
the empirical ``CE_t``, the oracle terms, and the bounds.

Two important caveats are reported by the analysis rather than hidden:

1. The formula displayed in the PDF has a typesetting ambiguity.  The radical
   appears to cover both regret terms while the proof adds two separate terms.
   We evaluate three readings (``bound_proof``, ``bound_display`` and
   ``bound_radical_all``) and show which one is consistent with the paper's own
   special cases.
2. The Section 6 implementation uses a constant ``eta`` and does not project
   the iterates onto ``||w|| <= R``.  The theorem assumes
   ``eta_i = 1 / (i * lambda)`` and a fixed ``R``.  A violated bound is
   therefore expected; the check is a diagnostic, not a falsification.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Iterable

import numpy as np
from scipy import optimize, sparse

from .data.base import TaskStream
from .models import build_model
from .models.meta import _predict_rows
from .seeding import seed_everything


# ---------------------------------------------------------------------------
# Loss helpers
# ---------------------------------------------------------------------------
def loss_values(
    y: Any,
    predictions: Any,
    loss: str,
) -> np.ndarray:
    """Return the pointwise loss for labels ``y`` and predictions.

    ``y`` and ``predictions`` may have different shapes as long as NumPy
    broadcasting produces the intended pairwise matrix (for example,
    ``y[:, None]`` against ``(m, n_models)`` member predictions).
    """
    y = np.asarray(y, dtype=np.float64)
    p = np.asarray(predictions, dtype=np.float64)
    if loss == "hinge":
        return np.maximum(0.0, 1.0 - y * p)
    if loss == "absolute":
        return np.abs(y - p)
    if loss == "squared":
        return (y - p) ** 2
    if loss == "zero_one":
        return (np.where(p >= 0.0, 1.0, -1.0) != y).astype(np.float64)
    raise ValueError(f"Unknown loss: {loss}")


def _row(X: Any, index: int) -> Any:
    if sparse.issparse(X):
        return X.getrow(index)
    return X[index]


def _row_norm(x: Any) -> float:
    if sparse.issparse(x):
        row = x.tocsr()
        return float(np.sqrt(row.data @ row.data))
    return float(np.linalg.norm(np.asarray(x, dtype=np.float64).ravel()))


def _max_row_norm(X: Any) -> float:
    if sparse.issparse(X):
        return float(np.sqrt(X.multiply(X).sum(axis=1)).max())
    return float(np.linalg.norm(np.asarray(X, dtype=np.float64), axis=1).max())


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
@dataclass
class TaskTrace:
    """Everything the theory checks need from one task."""

    task_index: int
    task_id: str
    X: Any
    y: np.ndarray
    alpha: np.ndarray
    current_pred: np.ndarray
    meta_pred: np.ndarray
    final_pred: np.ndarray
    current_loss: np.ndarray
    meta_loss: np.ndarray
    member_pred: np.ndarray
    member_loss: np.ndarray
    weight_norm: np.ndarray
    cover_size: np.ndarray
    cover_indices: list[int]
    knowledge_size: int
    n_features: int

    @property
    def n_samples(self) -> int:
        return int(len(self.y))

    @property
    def n_members(self) -> int:
        return int(self.member_pred.shape[1])


def trace_stream(
    stream: TaskStream,
    method: str,
    model_config: dict[str, Any],
    seed: int = 0,
    model_overrides: dict[str, Any] | None = None,
    max_tasks: int | None = None,
    track_norms: bool | None = None,
) -> list[TaskTrace]:
    """Run one learner on ``stream`` and record per-sample theory quantities."""
    seed_everything(seed)
    model = build_model(
        method,
        stream.n_features,
        stream.task_type,
        model_config,
        seed=seed,
        overrides=model_overrides,
    )
    tasks = stream.tasks[:max_tasks] if max_tasks is not None else stream.tasks
    if track_norms is None:
        # Computing the norm of a very high-dimensional sparse weight vector
        # at every sample is expensive.  The theory checks target the 2-D
        # synthetic datasets; for larger feature spaces the caller can pass R.
        track_norms = stream.n_features <= 2000

    traces: list[TaskTrace] = []
    for task_index, task in enumerate(tasks):
        model.start_task(
            task_index,
            task.n_train,
            task_id=task.task_id,
            category=task.category,
        )

        # The knowledge base used during the task.  For AKLOMS this is the
        # full base, not only the current cover.
        if hasattr(model, "knowledge_base"):
            members = list(model.knowledge_base)
        else:
            members = list(getattr(model, "snapshots", []))
        if members:
            member_matrix = np.vstack([snapshot.weights for snapshot in members])
        else:
            member_matrix = np.zeros((0, stream.n_features), dtype=np.float64)

        m = task.n_train
        y = np.asarray(task.y_train, dtype=np.float64)
        alpha = np.empty(m, dtype=np.float64)
        current_pred = np.empty(m, dtype=np.float64)
        meta_pred = np.empty(m, dtype=np.float64)
        final_pred = np.empty(m, dtype=np.float64)
        member_pred = np.empty((m, len(members)), dtype=np.float64)
        weight_norm = np.zeros(m, dtype=np.float64)
        cover_size = np.zeros(m, dtype=np.int64)

        for index in range(m):
            x = _row(task.X_train, index)
            current_pred[index] = model.current.predict(x)
            meta_pred[index] = (
                model.meta.predict(x) if model.meta is not None else 0.0
            )
            alpha[index] = model.alpha
            final_pred[index] = (
                alpha[index] * meta_pred[index]
                + (1.0 - alpha[index]) * current_pred[index]
            )
            if len(members):
                member_pred[index] = _predict_rows(member_matrix, x)

            norm_before = model.current.norm() if track_norms else 0.0
            model.update(x, y[index])
            norm_after = model.current.norm() if track_norms else 0.0
            weight_norm[index] = max(norm_before, norm_after)
            cover_size[index] = len(getattr(model, "cover_indices", []))

        model.end_task()

        current_loss = loss_values(y, current_pred, model.loss)
        meta_loss = loss_values(y, meta_pred, model.meta_loss)
        if len(members):
            member_loss = loss_values(y[:, None], member_pred, model.meta_loss)
        else:
            member_loss = np.zeros((m, 0), dtype=np.float64)

        traces.append(
            TaskTrace(
                task_index=task_index,
                task_id=task.task_id,
                X=task.X_train,
                y=y,
                alpha=alpha,
                current_pred=current_pred,
                meta_pred=meta_pred,
                final_pred=final_pred,
                current_loss=current_loss,
                meta_loss=meta_loss,
                member_pred=member_pred,
                member_loss=member_loss,
                weight_norm=weight_norm,
                cover_size=cover_size,
                cover_indices=list(getattr(model, "cover_indices", [])),
                knowledge_size=len(members),
                n_features=stream.n_features,
            )
        )
    return traces


# ---------------------------------------------------------------------------
# Constrained current-predictor optimum
# ---------------------------------------------------------------------------
def _loss_sum(w: np.ndarray, X: np.ndarray, y: np.ndarray, loss: str) -> float:
    return float(loss_values(y, X @ w, loss).sum())


def _lad_solution(X: np.ndarray, y: np.ndarray) -> np.ndarray | None:
    """Solve unconstrained least-absolute-deviations via a linear program."""
    m, d = X.shape
    # Variables: [w (d), t (m)], minimise sum(t)
    c = np.concatenate([np.zeros(d), np.ones(m)])
    A_ub = np.vstack(
        [
            np.hstack([-X, -np.eye(m)]),
            np.hstack([X, -np.eye(m)]),
        ]
    )
    b_ub = np.concatenate([-y, y])
    bounds = [(None, None)] * d + [(0.0, None)] * m
    try:
        result = optimize.linprog(
            c,
            A_ub=A_ub,
            b_ub=b_ub,
            bounds=bounds,
            method="highs",
        )
    except (ValueError, optimize.OptimizeWarning):
        return None
    if not result.success:
        return None
    return np.asarray(result.x[:d], dtype=np.float64)


def _boundary_search(
    X: np.ndarray,
    y: np.ndarray,
    loss: str,
    R: float,
    n_grid: int = 720,
    n_refine: int = 101,
) -> tuple[np.ndarray, float]:
    """Minimise a 2-D loss on the circle ``||w|| = R``.

    The hinge and absolute losses are piecewise linear, so a dense angular grid
    followed by local refinement is more reliable than a gradient-based solver
    at the kinks.
    """
    angles = np.linspace(0.0, 2.0 * math.pi, n_grid, endpoint=False)
    values = np.empty(n_grid, dtype=np.float64)
    for index, theta in enumerate(angles):
        w = R * np.array([math.cos(theta), math.sin(theta)])
        values[index] = _loss_sum(w, X, y, loss)
    best = int(np.argmin(values))
    best_theta = float(angles[best])
    best_value = float(values[best])
    step = 2.0 * math.pi / n_grid
    for _ in range(2):
        local = np.linspace(best_theta - step, best_theta + step, n_refine)
        local_values = np.empty(n_refine, dtype=np.float64)
        for index, theta in enumerate(local):
            w = R * np.array([math.cos(theta), math.sin(theta)])
            local_values[index] = _loss_sum(w, X, y, loss)
        local_best = int(np.argmin(local_values))
        if local_values[local_best] < best_value:
            best_value = float(local_values[local_best])
            best_theta = float(local[local_best])
        step /= n_refine
    w = R * np.array([math.cos(best_theta), math.sin(best_theta)])
    return w, best_value


def solve_constrained_loss(
    X: Any,
    y: Any,
    loss: str,
    R: float,
) -> tuple[np.ndarray, float]:
    """Solve ``min_{||w|| <= R} sum_i loss(y_i, w^T x_i)``.

    For two-dimensional data the boundary is searched densely and the
    unconstrained LAD solution is used when it is feasible.  For higher
    dimensions a constrained SLSQP solve is used; that path is a diagnostic
    approximation and is documented as such.
    """
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64).ravel()
    d = X.shape[1]
    zero = np.zeros(d, dtype=np.float64)
    if R <= 0.0:
        return zero, _loss_sum(zero, X, y, loss)

    candidates: list[tuple[np.ndarray, float]] = [(zero, _loss_sum(zero, X, y, loss))]

    if d == 2:
        w_boundary, value_boundary = _boundary_search(X, y, loss, R)
        candidates.append((w_boundary, value_boundary))

        if loss == "absolute":
            w_unconstrained = _lad_solution(X, y)
            if w_unconstrained is not None and np.linalg.norm(w_unconstrained) <= R:
                candidates.append(
                    (w_unconstrained, _loss_sum(w_unconstrained, X, y, loss))
                )
        else:
            # A gradient-based interior candidate helps when the unconstrained
            # optimum lies strictly inside the ball.
            result = optimize.minimize(
                lambda w: _loss_sum(w, X, y, loss),
                zero,
                method="SLSQP",
                options={"maxiter": 200, "ftol": 1e-10},
            )
            if result.success and np.linalg.norm(result.x) <= R:
                candidates.append(
                    (np.asarray(result.x), _loss_sum(result.x, X, y, loss))
                )
    else:
        constraints = [
            {
                "type": "ineq",
                "fun": lambda w: R * R - float(w @ w),
                "jac": lambda w: -2.0 * w,
            }
        ]
        starts = [zero]
        rng = np.random.default_rng(0)
        for _ in range(4):
            direction = rng.normal(size=d)
            norm = np.linalg.norm(direction)
            if norm > 0:
                starts.append(0.5 * R * direction / norm)
        for start in starts:
            result = optimize.minimize(
                lambda w: _loss_sum(w, X, y, loss),
                start,
                method="SLSQP",
                constraints=constraints,
                options={"maxiter": 300, "ftol": 1e-9},
            )
            if result.success and np.linalg.norm(result.x) <= R * (1.0 + 1e-8):
                candidates.append(
                    (np.asarray(result.x), _loss_sum(result.x, X, y, loss))
                )

    best_w, best_value = min(candidates, key=lambda item: item[1])
    return best_w, float(best_value)


# ---------------------------------------------------------------------------
# Packing and cover diagnostics
# ---------------------------------------------------------------------------
def greedy_packing(loss_matrix: np.ndarray, tau: float) -> list[int]:
    """Return a greedy ``tau``-packing of the columns of ``loss_matrix``.

    The packing condition is ``max_i |e_i(p) - e_i(q)| >= tau`` for every pair.
    Greedy selection is a lower bound on the packing number and is used as a
    transparent surrogate for the covering number.
    """
    n_models = loss_matrix.shape[1]
    selected: list[int] = []
    for candidate in range(n_models):
        if not selected:
            selected.append(candidate)
            continue
        differences = np.max(
            np.abs(loss_matrix[:, [candidate]] - loss_matrix[:, selected]),
            axis=0,
        )
        if float(np.min(differences)) >= tau:
            selected.append(candidate)
    return selected


def cover_packing_check(
    trace: TaskTrace,
    tau: float,
) -> dict[str, Any]:
    """Check whether the AKLOMS cover is a ``2*tau`` packing.

    The implementation adds models based on prediction differences, while the
    paper defines the packing on the loss sequence.  We report both quantities
    so the gap is visible.
    """
    cover = [index for index in trace.cover_indices if index < trace.n_members]
    if len(cover) < 2:
        return {
            "cover_size": len(cover),
            "loss_pair_fraction_below_2tau": None,
            "prediction_pair_fraction_below_2tau": None,
            "min_loss_pair_distance": None,
            "min_prediction_pair_distance": None,
        }

    loss_cover = trace.member_loss[:, cover]
    pred_cover = trace.member_pred[:, cover]
    n_pairs = 0
    loss_below = 0
    pred_below = 0
    min_loss = math.inf
    min_pred = math.inf
    for i in range(len(cover)):
        for j in range(i + 1, len(cover)):
            loss_distance = float(
                np.max(np.abs(loss_cover[:, i] - loss_cover[:, j]))
            )
            pred_distance = float(
                np.max(np.abs(pred_cover[:, i] - pred_cover[:, j]))
            )
            min_loss = min(min_loss, loss_distance)
            min_pred = min(min_pred, pred_distance)
            n_pairs += 1
            if loss_distance < 2.0 * tau:
                loss_below += 1
            if pred_distance < 2.0 * tau:
                pred_below += 1
    return {
        "cover_size": len(cover),
        "loss_pair_fraction_below_2tau": loss_below / n_pairs,
        "prediction_pair_fraction_below_2tau": pred_below / n_pairs,
        "min_loss_pair_distance": min_loss,
        "min_prediction_pair_distance": min_pred,
    }


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
def _task_number(trace: TaskTrace) -> int:
    """One-based task number ``t`` used in the paper's formulas."""
    return trace.task_index + 1


def _corollary_11(
    alpha: np.ndarray,
    expert: float,
    zeta_e: float,
    zeta_l: float,
    K: float,
    R: float,
    m: int,
    t: int,
    gamma_values: Iterable[float],
) -> dict[str, Any]:
    """Evaluate the condition and bound of Corollary 1.1 for one task."""
    log_t = math.log(t - 1) if t > 2 else 0.0
    if t <= 2:
        return {
            "applicable": False,
            "reason": "Corollary 1.1 uses log(t-1); task t=2 has log(1)=0.",
        }
    if not math.isfinite(zeta_e) or zeta_e <= 0.0:
        return {
            "applicable": True,
            "feasible": False,
            "reason": "zeta_e is zero or undefined; the condition cannot be evaluated.",
            "zeta_e": zeta_e,
            "zeta_l": zeta_l,
        }

    best: dict[str, Any] | None = None
    checked: list[dict[str, Any]] = []
    for gamma in gamma_values:
        gamma = float(gamma)
        if gamma <= 0.0 or gamma > 1.0:
            continue
        N_required = (1.0 / gamma) * max(
            zeta_l / zeta_e,
            K * R / math.sqrt(2.0 * log_t),
        )
        threshold = N_required / (1.0 + N_required)
        inside = alpha >= threshold
        i0 = int(np.sum(inside))
        feasible = m <= i0
        bound = (1.0 + gamma) * (
            expert + math.sqrt(2.0 * log_t * float(alpha.sum()))
        )
        entry = {
            "gamma": gamma,
            "N_required": N_required,
            "threshold": threshold,
            "i0": i0,
            "feasible": feasible,
            "bound": bound,
        }
        checked.append(entry)
        if feasible and (best is None or bound < best["bound"]):
            best = entry

    result: dict[str, Any] = {
        "applicable": True,
        "zeta_e": zeta_e,
        "zeta_l": zeta_l,
        "feasible": best is not None,
        "checked_gamma": checked,
    }
    if best is not None:
        result.update(best)
    else:
        # Report the most favourable gamma (largest gamma gives the smallest N
        # and therefore the largest i0) so the reason for failure is visible.
        result.update(checked[-1] if checked else {})
    return result


def analyze_trace(
    traces: list[TaskTrace],
    task_type: str,
    meta_loss: str,
    current_loss: str,
    R: float | None = None,
    R_multipliers: tuple[float, ...] = (0.5, 1.0, 2.0, 5.0),
    gamma_values: tuple[float, ...] = (0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 1.0),
    tau: float | None = None,
    packing_task_indices: set[int] | None = None,
) -> dict[str, Any]:
    """Compute Theorem 1, Corollary 1.1 and Corollary 1.2 diagnostics."""
    if not traces:
        raise ValueError("No task traces")

    K = max(_max_row_norm(trace.X) for trace in traces)
    R_observed = max(
        (float(np.max(trace.weight_norm)) for trace in traces if trace.weight_norm.size),
        default=0.0,
    )
    if R is None:
        R = R_observed
    if R <= 0.0:
        raise ValueError("R must be positive; pass --R for high-dimensional data")

    max_meta_loss = max(float(np.max(trace.meta_loss)) for trace in traces)
    min_meta_loss = min(float(np.min(trace.meta_loss)) for trace in traces)
    max_current_loss = max(float(np.max(trace.current_loss)) for trace in traces)

    task_records: list[dict[str, Any]] = []
    for trace in traces:
        t = _task_number(trace)
        if t < 2:
            continue
        m = trace.n_samples
        alpha = trace.alpha
        A = float(alpha.sum())
        B = float((1.0 - alpha).sum())
        CE = float(
            np.sum(alpha * trace.meta_loss + (1.0 - alpha) * trace.current_loss)
        )

        if trace.n_members:
            member_totals = trace.member_loss.sum(axis=0)
            fstar = int(np.argmin(member_totals))
            zeta_e = float(member_totals[fstar])
            expert = float(np.sum(alpha * trace.member_loss[:, fstar]))
            weighted_fstar = int(np.argmin((alpha[:, None] * trace.member_loss).sum(axis=0)))
            weighted_expert = float(
                np.sum(alpha * trace.member_loss[:, weighted_fstar])
            )
        else:
            fstar = None
            zeta_e = math.nan
            expert = 0.0
            weighted_fstar = None
            weighted_expert = 0.0

        w_star, zeta_l = solve_constrained_loss(
            trace.X, trace.y, current_loss, R
        )
        l_star = loss_values(trace.y, np.asarray(trace.X) @ w_star, current_loss)
        current = float(np.sum((1.0 - alpha) * l_star))

        log_t = math.log(t - 1) if t > 2 else 0.0
        log_m = math.log(m) + 1.0
        regret_expert = math.sqrt(2.0 * log_t * A) if log_t > 0.0 else 0.0
        regret_current = B * K * R * math.sqrt(log_m / m)
        bound_proof = expert + current + regret_expert + regret_current
        bound_display = expert + current + math.sqrt(
            2.0 * log_t * A + B * K * R
        ) * math.sqrt(log_m / m)
        bound_radical_all = expert + current + math.sqrt(
            2.0 * log_t * A + B * K * R * math.sqrt(log_m / m)
        )

        record: dict[str, Any] = {
            "task_index": trace.task_index,
            "t": t,
            "task_id": trace.task_id,
            "m": m,
            "A": A,
            "B": B,
            "CE": CE,
            "expert": expert,
            "current": current,
            "regret_expert": regret_expert,
            "regret_current": regret_current,
            "bound_proof": bound_proof,
            "bound_display": bound_display,
            "bound_radical_all": bound_radical_all,
            "ratio_proof": bound_proof / CE if CE > 0 else None,
            "ratio_display": bound_display / CE if CE > 0 else None,
            "ratio_radical_all": bound_radical_all / CE if CE > 0 else None,
            "fstar_index": fstar,
            "weighted_fstar_index": weighted_fstar,
            "weighted_expert": weighted_expert,
            "zeta_e": zeta_e,
            "zeta_l": zeta_l,
            "w_star_norm": float(np.linalg.norm(w_star)),
            "max_weight_norm": float(np.max(trace.weight_norm))
            if trace.weight_norm.size
            else None,
            "cover_size": int(len(trace.cover_indices)),
            "max_cover_size": int(np.max(trace.cover_size))
            if trace.cover_size.size
            else 0,
            "knowledge_size": trace.knowledge_size,
        }

        record["corollary_1_1"] = _corollary_11(
            alpha,
            expert,
            zeta_e,
            zeta_l,
            K,
            R,
            m,
            t,
            gamma_values,
        )

        if tau is not None:
            cover_size = max(record["cover_size"], 1)
            bound_cover = (
                expert
                + current
                + 2.0
                * math.sqrt(cover_size * math.log(cover_size))
                * A
                + 2.0 * tau * A
                + regret_current
            )
            record["corollary_1_2"] = {
                "tau": tau,
                "cover_size": record["cover_size"],
                "max_cover_size": record["max_cover_size"],
                "bound_cover_size": bound_cover,
                "ratio_cover_size": bound_cover / CE if CE > 0 else None,
                "packing_check": cover_packing_check(trace, tau),
            }

            if (
                packing_task_indices is not None
                and trace.task_index in packing_task_indices
                and trace.n_members >= 2
            ):
                packing = greedy_packing(trace.member_loss, tau)
                packing_2tau = greedy_packing(trace.member_loss, 2.0 * tau)
                N_packing = max(len(packing), 1)
                bound_packing = (
                    expert
                    + current
                    + 2.0
                    * math.sqrt(N_packing * math.log(N_packing))
                    * A
                    + 2.0 * tau * A
                    + regret_current
                )
                record["corollary_1_2"].update(
                    {
                        "packing_tau": len(packing),
                        "packing_2tau": len(packing_2tau),
                        "bound_packing_tau": bound_packing,
                        "ratio_packing_tau": bound_packing / CE if CE > 0 else None,
                    }
                )

        task_records.append(record)

    # Sensitivity to R: the theorem assumes a fixed R, but the implementation
    # never projects.  A sweep shows whether the conclusion depends on the
    # post-hoc estimate.
    sensitivity: list[dict[str, Any]] = []
    for multiplier in R_multipliers:
        R_value = R * float(multiplier)
        ratios = []
        for trace in traces:
            t = _task_number(trace)
            if t < 2:
                continue
            alpha = trace.alpha
            m = trace.n_samples
            A = float(alpha.sum())
            B = float((1.0 - alpha).sum())
            CE = float(
                np.sum(alpha * trace.meta_loss + (1.0 - alpha) * trace.current_loss)
            )
            if trace.n_members:
                member_totals = trace.member_loss.sum(axis=0)
                fstar = int(np.argmin(member_totals))
                expert = float(np.sum(alpha * trace.member_loss[:, fstar]))
            else:
                expert = 0.0
            w_star, _ = solve_constrained_loss(
                trace.X, trace.y, current_loss, R_value
            )
            l_star = loss_values(
                trace.y, np.asarray(trace.X) @ w_star, current_loss
            )
            current = float(np.sum((1.0 - alpha) * l_star))
            log_t = math.log(t - 1) if t > 2 else 0.0
            log_m = math.log(m) + 1.0
            regret_expert = math.sqrt(2.0 * log_t * A) if log_t > 0.0 else 0.0
            regret_current = B * K * R_value * math.sqrt(log_m / m)
            bound = expert + current + regret_expert + regret_current
            ratios.append(bound / CE if CE > 0 else math.nan)
        sensitivity.append(
            {
                "R_multiplier": float(multiplier),
                "R": R_value,
                "median_ratio": float(np.nanmedian(ratios)) if ratios else None,
                "fraction_ce_le_bound": float(
                    np.mean([ratio >= 1.0 for ratio in ratios])
                )
                if ratios
                else None,
            }
        )

    def _fraction(key: str) -> float:
        values = [
            record[key] >= 1.0
            for record in task_records
            if record[key] is not None
        ]
        return float(np.mean(values)) if values else math.nan

    def _median(key: str) -> float:
        values = [
            record[key]
            for record in task_records
            if record[key] is not None and math.isfinite(record[key])
        ]
        return float(np.median(values)) if values else math.nan

    corollary_11_records = [
        record["corollary_1_1"]
        for record in task_records
        if record["corollary_1_1"].get("applicable")
    ]
    corollary_11_feasible = [
        record for record in corollary_11_records if record.get("feasible")
    ]
    corollary_11_ratios = [
        record["corollary_1_1"]["bound"] / record["CE"]
        for record in task_records
        if record["corollary_1_1"].get("feasible") and record["CE"] > 0
    ]

    corollary_12_records = [
        record["corollary_1_2"]
        for record in task_records
        if "corollary_1_2" in record
    ]

    summary = {
        "n_tasks_traced": len(traces),
        "n_tasks_analyzed": len(task_records),
        "n_features": traces[0].n_features,
        "task_type": task_type,
        "meta_loss": meta_loss,
        "current_loss": current_loss,
        "K": K,
        "R": R,
        "R_observed": R_observed,
        "max_meta_loss": max_meta_loss,
        "min_meta_loss": min_meta_loss,
        "max_current_loss": max_current_loss,
        "median_CE": _median("CE"),
        "median_bound_proof": _median("bound_proof"),
        "median_bound_display": _median("bound_display"),
        "median_ratio_proof": _median("ratio_proof"),
        "median_ratio_display": _median("ratio_display"),
        "fraction_ce_le_bound_proof": _fraction("ratio_proof"),
        "fraction_ce_le_bound_display": _fraction("ratio_display"),
        "fraction_ce_le_bound_radical_all": _fraction("ratio_radical_all"),
        "corollary_1_1_applicable": len(corollary_11_records),
        "corollary_1_1_feasible": len(corollary_11_feasible),
        "corollary_1_1_feasible_fraction": (
            len(corollary_11_feasible) / len(corollary_11_records)
            if corollary_11_records
            else None
        ),
        "corollary_1_1_median_ratio_when_feasible": (
            float(np.median(corollary_11_ratios))
            if corollary_11_ratios
            else None
        ),
        "corollary_1_2_median_ratio_cover_size": (
            float(
                np.median(
                    [
                        record["ratio_cover_size"]
                        for record in corollary_12_records
                        if record["ratio_cover_size"] is not None
                    ]
                )
            )
            if corollary_12_records
            else None
        ),
        "corollary_1_2_median_cover_size": (
            float(np.median([record["cover_size"] for record in corollary_12_records]))
            if corollary_12_records
            else None
        ),
        "corollary_1_2_median_knowledge_size": (
            float(
                np.median(
                    [record["knowledge_size"] for record in task_records]
                )
            )
            if task_records
            else None
        ),
        "R_sensitivity": sensitivity,
    }

    return {
        "summary": summary,
        "tasks": task_records,
    }


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------
def _format(value: Any, digits: int = 4) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        if math.isnan(value):
            return "nan"
        if math.isinf(value):
            return "inf"
        return f"{value:.{digits}f}"
    return str(value)


def render_markdown(analysis: dict[str, Any], title: str) -> str:
    """Render the analysis as a human-readable Markdown report."""
    summary = analysis["summary"]
    tasks = analysis["tasks"]
    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(
        "This report instruments one run and evaluates the paper's bounds "
        "post hoc.  It is a diagnostic, not a benchmark: the Section 6 "
        "implementation uses a constant learning rate and does not project "
        "the iterates, while Theorem 1 assumes a specific decaying schedule "
        "and a fixed norm ball."
    )
    lines.append("")
    lines.append("## Setup")
    lines.append("")
    lines.append("| quantity | value |")
    lines.append("| --- | --- |")
    for key in (
        "n_tasks_traced",
        "n_tasks_analyzed",
        "n_features",
        "task_type",
        "meta_loss",
        "current_loss",
        "K",
        "R",
        "R_observed",
        "max_meta_loss",
        "max_current_loss",
    ):
        lines.append(f"| `{key}` | {_format(summary[key])} |")
    lines.append("")

    lines.append("## Assumption audit")
    lines.append("")
    lines.append("| assumption | status |")
    lines.append("| --- | --- |")
    bounded_meta = (
        summary["min_meta_loss"] >= 0.0 and summary["max_meta_loss"] <= 1.0
    )
    lines.append(
        f"| meta loss bounded in [0, 1] | {'satisfied' if bounded_meta else 'violated'} "
        f"(observed [{_format(summary['min_meta_loss'])}, {_format(summary['max_meta_loss'])}]) |"
    )
    lines.append(
        "| current loss K-Lipschitz | hinge/absolute are K-Lipschitz with "
        f"`K = max ||x|| = {_format(summary['K'])}` |"
    )
    lines.append(
        "| `||w|| <= R` | the implementation does not project; "
        f"`R` is the post-hoc maximum observed norm ({_format(summary['R_observed'])}) |"
    )
    lines.append(
        "| `eta_i = 1/(i lambda)` | **violated**: the Section 6 configuration uses a constant `eta` |"
    )
    lines.append(
        "| `alpha_1 = 1`, non-increasing | satisfied by the implementation |"
    )
    lines.append("")

    lines.append("## Theorem 1")
    lines.append("")
    lines.append(
        "The PDF displays one radical over both regret terms, while the proof "
        "adds two separate terms.  We report three readings:"
    )
    lines.append("")
    lines.append(
        "* `bound_proof`: `expert + current + sqrt(2 log(t-1) A) + "
        "B K R sqrt((log m+1)/m)` (the two propositions added)."
    )
    lines.append(
        "* `bound_display`: `expert + current + sqrt(2 log(t-1) A + B K R) * "
        "sqrt((log m+1)/m)` (the displayed formula)."
    )
    lines.append(
        "* `bound_radical_all`: `expert + current + sqrt(2 log(t-1) A + "
        "B K R sqrt((log m+1)/m))` (small radical inside the large one)."
    )
    lines.append("")
    lines.append(
        "Only `bound_proof` reproduces both special cases stated in the paper: "
        "`alpha == 1` gives `sqrt(2 m log(t-1))`, and `alpha == 0` gives "
        "`K R sqrt(m (log m+1))`."
    )
    lines.append("")
    lines.append("| metric | value |")
    lines.append("| --- | --- |")
    for key in (
        "median_CE",
        "median_bound_proof",
        "median_bound_display",
        "median_ratio_proof",
        "median_ratio_display",
        "fraction_ce_le_bound_proof",
        "fraction_ce_le_bound_display",
        "fraction_ce_le_bound_radical_all",
    ):
        lines.append(f"| `{key}` | {_format(summary[key])} |")
    lines.append("")
    lines.append(
        "A ratio above 1 means the bound covers the empirical error.  The "
        "fractions are over all analyzed tasks (task 1 is excluded because the "
        "theorem is stated for a task with accumulated knowledge)."
    )
    lines.append("")

    lines.append("### Per-task values")
    lines.append("")
    lines.append(
        "| t | m | CE | expert | current | regret expert | regret current | "
        "bound proof | bound display | ratio proof | ratio display |"
    )
    lines.append("| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    selected = tasks
    if len(tasks) > 20:
        stride = max(1, len(tasks) // 15)
        selected = tasks[::stride]
        if tasks[-1] not in selected:
            selected = selected + [tasks[-1]]
    for record in selected:
        lines.append(
            "| {t} | {m} | {ce} | {expert} | {current} | {re} | {rc} | "
            "{bp} | {bd} | {rp} | {rd} |".format(
                t=record["t"],
                m=record["m"],
                ce=_format(record["CE"]),
                expert=_format(record["expert"]),
                current=_format(record["current"]),
                re=_format(record["regret_expert"]),
                rc=_format(record["regret_current"]),
                bp=_format(record["bound_proof"]),
                bd=_format(record["bound_display"]),
                rp=_format(record["ratio_proof"]),
                rd=_format(record["ratio_display"]),
            )
        )
    lines.append("")

    lines.append("## Corollary 1.1 (small interactions)")
    lines.append("")
    lines.append(
        "| metric | value |"
    )
    lines.append("| --- | --- |")
    for key in (
        "corollary_1_1_applicable",
        "corollary_1_1_feasible",
        "corollary_1_1_feasible_fraction",
        "corollary_1_1_median_ratio_when_feasible",
    ):
        lines.append(f"| `{key}` | {_format(summary[key])} |")
    lines.append("")
    lines.append(
        "The condition is `m_t <= i_0(N)`, where `i_0` is the last index with "
        "`alpha_i >= N/(1+N)` and `N` is the corollary's required interaction "
        "parameter.  When the condition fails, the corollary is outside its "
        "hypothesis and a violated inequality is not a counterexample."
    )
    lines.append("")

    condition_rows = [
        record
        for record in tasks
        if record["corollary_1_1"].get("applicable")
    ]
    if condition_rows:
        lines.append(
            "| t | zeta_e | zeta_l | N (gamma=1) | i0 | feasible | bound | ratio |"
        )
        lines.append("| ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |")
        selected_conditions = condition_rows
        if len(condition_rows) > 15:
            stride = max(1, len(condition_rows) // 12)
            selected_conditions = condition_rows[::stride]
            if condition_rows[-1] not in selected_conditions:
                selected_conditions = selected_conditions + [condition_rows[-1]]
        for record in selected_conditions:
            info = record["corollary_1_1"]
            checked = info.get("checked_gamma", [])
            most_favourable = checked[-1] if checked else {}
            if info.get("feasible"):
                displayed = {
                    "N_required": info.get("N_required"),
                    "i0": info.get("i0"),
                    "gamma": info.get("gamma"),
                }
            else:
                displayed = most_favourable
            bound = info.get("bound")
            lines.append(
                "| {t} | {ze} | {zl} | {N} | {i0} | {feasible} | {bound} | {ratio} |".format(
                    t=record["t"],
                    ze=_format(info.get("zeta_e")),
                    zl=_format(info.get("zeta_l")),
                    N=_format(displayed.get("N_required")),
                    i0=_format(displayed.get("i0")),
                    feasible=_format(info.get("feasible")),
                    bound=_format(bound),
                    ratio=_format(bound / record["CE"] if bound and record["CE"] > 0 else None),
                )
            )
        lines.append("")

    if summary.get("corollary_1_2_median_cover_size") is not None:
        lines.append("## Corollary 1.2 (cover-set knowledge)")
        lines.append("")
        lines.append("| metric | value |")
        lines.append("| --- | --- |")
        for key in (
            "corollary_1_2_median_cover_size",
            "corollary_1_2_median_knowledge_size",
            "corollary_1_2_median_ratio_cover_size",
        ):
            lines.append(f"| `{key}` | {_format(summary[key])} |")
        lines.append("")
        lines.append(
            "The bound uses the actual cover size as a surrogate for the "
            "covering number `N(tau, S_t)`.  Because the algorithm builds a "
            "`2*tau` packing, `|Lambda_t| <= P(2*tau) <= N(tau)`, so this "
            "surrogate is optimistic: the true covering number can only make "
            "the bound larger."
        )
        lines.append("")
        packing_records = [
            record
            for record in tasks
            if "packing_tau" in record.get("corollary_1_2", {})
        ]
        if packing_records:
            lines.append(
                "| t | cover | P(tau) | P(2 tau) | bound cover | ratio cover | "
                "ratio P(tau) | loss pairs < 2 tau | pred pairs < 2 tau |"
            )
            lines.append(
                "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"
            )
            for record in packing_records:
                info = record["corollary_1_2"]
                check = info["packing_check"]
                lines.append(
                    "| {t} | {cover} | {p} | {p2} | {bc} | {rc} | {rp} | "
                    "{loss} | {pred} |".format(
                        t=record["t"],
                        cover=info["cover_size"],
                        p=info["packing_tau"],
                        p2=info["packing_2tau"],
                        bc=_format(info["bound_cover_size"]),
                        rc=_format(info["ratio_cover_size"]),
                        rp=_format(info["ratio_packing_tau"]),
                        loss=_format(check["loss_pair_fraction_below_2tau"]),
                        pred=_format(check["prediction_pair_fraction_below_2tau"]),
                    )
                )
            lines.append("")

    lines.append("## R sensitivity")
    lines.append("")
    lines.append("| R multiplier | R | median ratio (proof) | fraction covered |")
    lines.append("| ---: | ---: | ---: | ---: |")
    for entry in summary["R_sensitivity"]:
        lines.append(
            f"| {_format(entry['R_multiplier'])} | {_format(entry['R'])} | "
            f"{_format(entry['median_ratio'])} | "
            f"{_format(entry['fraction_ce_le_bound'])} |"
        )
    lines.append("")
    lines.append(
        "The bound grows linearly in `R`, but a larger feasible ball also "
        "lowers the current-predictor oracle term.  The sweep makes the "
        "dependence explicit instead of hiding it behind one arbitrary `R`."
    )
    lines.append("")
    return "\n".join(lines)
