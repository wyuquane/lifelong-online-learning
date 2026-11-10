# Theory checks

This document describes how the reproduction empirically stress-tests the
paper's theoretical claims. The reproduction code is intentionally structured
so that the same stream and the same learners can be instrumented without
changing the experiments. **Status: implemented and run.** The results are
summarized in [`reports/theory/README.md`](../reports/theory/README.md) and in
the per-run Markdown/JSON files under `reports/theory/`.

The three results to check are Theorem 1, Corollary 1.1, and Corollary 1.2.
The assumptions are as important as the inequalities themselves; several of
them are not satisfied by the exact implementation used in Section 6.

## 1. Theorem 1 (accumulating error bound)

For task `t` with `m_t` observations, the paper defines

```
CE_t = sum_i [ alpha_i * e_{t,i}(k_t) + (1 - alpha_i) * l_{t,i}(f_t) ]
```

and claims

```
CE_t <= sum_i alpha_i e_{t,i}(f*)
      + sum_i (1 - alpha_i) l_{t,i}(w*)
      + ( sqrt(2 log(t-1)) * sum_i alpha_i
          + sum_i (1 - alpha_i) K R )
        * sqrt((log(m_t) + 1) / m_t)
```

where

* `f*` is the best previous predictor for the task's meta loss;
* `w*` minimizes the current loss over `||w|| <= R`;
* `K` is the Lipschitz constant of the current loss;
* `lambda = (K/R) * sqrt((log(m_t)+1)/m_t)` and `eta_i = 1/(i lambda)`.

The formula in the PDF extraction has an ambiguity in the placement of
`sqrt((log(m_t)+1)/m_t)` (it may normalize the whole bracket or only the
current-predictor term). A theory-check implementation should evaluate both
readings and report them explicitly instead of silently choosing one.

### What to compute

For each task of a run:

1. Store every prediction made by the current predictor and by the meta
   predictor, before each update.
2. Store the `alpha_i` sequence actually used by the implementation.
3. Compute `CE_t` from those predictions.
4. Compute `e_{t,i}(f_q)` for every previous task predictor `q` and pick the
   empirical `f*` (the minimizer of the cumulative meta loss).
5. Compute `l_{t,i}(w*)` by solving the constrained offline problem over
   `||w|| <= R`. For `syn1`/`syn3` this is a two-dimensional convex problem and
   can be solved accurately with SciPy. For Spam/London, use a subset of
   features or a strong convex solver; the point is a diagnostic, not a
   benchmark.
6. Estimate `R` from the largest weight norm observed in the run, or treat it
   as a sensitivity parameter. The bound grows linearly in `R`, so a single
   arbitrary `R` can make the check vacuous.
7. Compare the empirical `CE_t` with the bound and with each component
   (expert term, current term, regret terms).

## 2. Corollary 1.1 (small interactions)

The corollary assumes `m_t <= i_0`, where

```
i_0 = max { i : alpha_i >= N / (1 + N) }
```

and

```
zeta_e = min_f sum_i e_{t,i}(f) > 0
zeta_l = min_{||w||<=R} sum_i l_{t,i}(w)
N >= (1/gamma) * max( zeta_l / zeta_e, K R / sqrt(2 log(t-1)) )
```

for some `gamma in (0, 1]`. Under those conditions,

```
CE_t <= (1 + gamma) * ( sum_i alpha_i e_{t,i}(f*)
                      + sqrt(2 log(t-1)) * sum_i alpha_i )
```

(again up to the normalization ambiguity).

### What to check

* Compute `i_0` from the actual `alpha` schedule. For `alpha_i = max(0, 1 -
  delta_alpha * i)`, `i_0` is finite and often much smaller than `m_t = 100`
  when `delta_alpha` is large. The corollary is then outside its hypothesis;
  the check should say so rather than treating a violated bound as a
  counterexample.
* Compute `zeta_e` and `zeta_l` on the task and test whether the required `N`
  exists for at least one `gamma in (0, 1]`.
* If the condition holds, compare the empirical `CE_t` with the corollary's
  right-hand side.
* Sweep `delta_alpha` (E4/E5 already do) to see when the small-interaction
  regime is actually reachable.

## 3. Corollary 1.2 (cover-set knowledge)

The modified algorithm uses a `2*tau` packing/cover `Lambda_t` and

```
epsilon_i = sqrt(|Lambda_t| / (2 sum_i alpha_i))
```

The claimed bound replaces the `sqrt(2 log(t-1))` expert term with

```
2 sqrt(N(tau, S_t) log N(tau, S_t)) * sum_i alpha_i
+ 2 tau * sum_i alpha_i
```

where `N(tau, S_t)` is the covering number of the sequential loss.

### What to check

* Use the actual cover size `|Lambda_t|` as a surrogate for `N(tau, S_t)`, or
  compute an empirical packing number from the pairwise prediction differences
  on the task.
* Verify that the implementation's cover is a `2*tau` packing: for every pair
  of models in the cover, there is at least one observation where their
  predictions differ by at least `2*tau`.
* Check the `tau=0` equivalence with AKLO (the code has a dedicated test for
  this).
* Compare the bound with the empirical `CE_t` for several `tau` values. The
  paper's own Figure 7 shows that larger `tau` reduces the cover but hurts
  ACE; the theory check should quantify that trade-off.

## 4. Assumptions that need explicit auditing

The empirical implementation does not satisfy all assumptions literally:

1. **Bounded meta loss in `[0,1]`.** Hinge loss and squared loss are unbounded.
   The paper's Section 6 uses hinge for the current classifier and square loss
   for the meta hypothesis; the theorem assumes a bounded meta loss. This is a
   theory-practice gap worth stating.
2. **`K`-Lipschitz loss.** Hinge and absolute loss are 1-Lipschitz, but the
   squared meta loss is not globally Lipschitz.
3. **`||w|| <= R`.** The online update does not project onto the ball; `R` is
   only a theoretical constant. The check must estimate it or sweep it.
4. **`eta_i = 1/(i lambda)`.** The implementation uses a constant `eta` from
   the paper's Section 6 defaults (`1.0` for classification, `0.05` for
   regression), not the schedule required by Theorem 1. The theorem is
   therefore not directly applicable to the reported runs.
5. **`alpha_1 = 1` and non-increasing `alpha`.** This is satisfied by the
   implementation.
6. **`f*` is chosen from previous task predictors.** The implementation's meta
   hypothesis uses all previous predictors; the theorem's `f*` is the best one
   for the current task, which is an oracle comparator.
7. **`N(tau, S_t)` and `P(tau, S_t)` are defined on loss sequences.** The
   implementation's cover uses prediction differences, not loss differences;
   for Lipschitz losses these are related, but not identical.

## 5. Implementation

The module is `src/aklo/theory.py` with a companion
`scripts/check_theory.py` and a reproducible matrix in
`scripts/run_theory_checks.ps1`. It:

* runs one AKLO/AKLOMS stream and records per-sample predictions, `alpha`,
  cover sizes, and weight norms;
* computes empirical `CE_t` and the Theorem 1 components;
* solves the two-dimensional `w*` problem for `syn1`/`syn3`;
* evaluates Corollary 1.1's condition and, when it holds, its bound;
* computes the cover/packing diagnostic for Corollary 1.2;
* writes a Markdown/JSON report under `reports/theory/`.

The module is deliberately separate from the experiment runner so that the
main reproduction remains comparable to the paper's Section 6 protocol. A
theory check that changes `eta` or the loss is reported as a separate
sensitivity study, not mixed into Table 1. The checks are diagnostics, not
benchmark runs: they are not logged to W&B.

### 5.1 Results at a glance

* **Theorem 1.** The displayed radical is inconsistent with the proof and with
  both stated special cases. The `bound_proof` reading covers 100% of `syn1`
  tasks and 93.9% of `syn3` tasks; the displayed reading covers 0% and 10.2%.
  With `delta_alpha=0.0001` on `syn1`, the proof bound covers only 36.7%,
  because the constant-`eta` Section 6 update violates the theorem's schedule.
* **Corollary 1.1.** The small-interaction condition `m_t <= i_0` is not
  reachable at `m_t=100` in any of the ten runs. For classification,
  `K R / sqrt(2 log(t-1))` forces `N/(1+N) ~ 0.99`, so `alpha` would have to
  stay above 0.99 for all 100 steps. On `syn3`, `i_0` reaches 74, so the
  corollary may become feasible at a smaller `m_t`.
* **Corollary 1.2.** The cover is nearly the whole knowledge base for
  `tau <= 1` and still 45/49 models at `tau=10`. The cover bound is 5.6–10.8×
  the empirical `CE_t`, and is looser than Theorem 1 even at `tau=0`. The
  implementation's cover is a valid prediction-space `2*tau` packing; the
  theory is stated on loss sequences, which creates a small mismatch at large
  `tau`.
