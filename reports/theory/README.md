# Theory checks

These reports test the paper's three theoretical claims on the same online
stream used by the reproduction:

* **Theorem 1** — the accumulating-error bound;
* **Corollary 1.1** — the small-interaction bound;
* **Corollary 1.2** — the cover-set bound used by AKLOMS.

The checks are **diagnostics, not benchmark runs**. They instrument one
learner, compute the empirical quantities after the stream, and compare them
with the paper's right-hand sides. They are deliberately kept out of the
Section 6 result tables and are **not logged to W&B**.

## How to reproduce

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_theory_checks.ps1
```

The script writes one JSON and one Markdown file per run to `reports/theory/`.
Individual checks:

```bash
python scripts/check_theory.py --dataset syn1 --method aklo --tasks 50
python scripts/check_theory.py --dataset syn3 --method aklo --tasks 50
python scripts/check_theory.py --dataset syn1 --method akloms --tau 0.1 --tasks 50
python scripts/check_theory.py --dataset syn1 --method aklo --tasks 50 --delta-alpha 0.01
```

`--tasks 50` keeps the constrained `w*` solves and packing computations
tractable; the paper's Section 6 uses 200 tasks. `--R` fixes the norm bound
explicitly; by default the largest observed weight norm is used.

## What is recorded

For every observation the tracer records the current prediction, the meta
prediction, the final prediction, the `alpha` actually used, the predictions
and losses of every model in the knowledge base, the current weight norm, and
the current cover size. The analysis then computes, for each task `t`:

```
CE_t = sum_i alpha_i * e_{t,i}(meta) + (1 - alpha_i) * l_{t,i}(current)
```

together with the expert term, the current-predictor oracle term, both regret
terms, and the empirical `CE_t`.

The two-dimensional oracle problem

```
w* = argmin_{||w|| <= R} sum_i l_{t,i}(w)
```

is solved by a dense boundary search plus the unconstrained LAD candidate for
absolute loss, or a local SLSQP candidate for hinge loss. For higher dimensions
the code uses a multi-start constrained SLSQP solve and labels the result as an
approximation.

## Assumption audit

The paper's proof assumes more than the Section 6 implementation provides:

| Assumption | Paper | This implementation |
| --- | --- | --- |
| Meta loss bounded in `[0, 1]` | yes | **no** — hinge and squared losses are unbounded |
| Current loss `K`-Lipschitz | yes | yes — hinge/absolute are 1-Lipschitz, `K = max ||x||` |
| `||w|| <= R` | projection | **no projection**; `R` is a post-hoc observed norm |
| `eta_i = 1/(i lambda)` | yes | **no** — constant `eta` from the Section 6 defaults |
| `alpha_1 = 1`, non-increasing | yes | yes |
| `f*` is an oracle previous model | yes | yes — best previous model on the task |
| Cover/packing defined on losses | yes | Algorithm 3 uses **prediction** differences |

The mismatch is the point of the exercise: the reported experiments are a
stress test of the theory, not a literal instantiation of its hypotheses. A
violated bound is therefore evidence about the gap between theory and the
Section 6 protocol, not a falsification of the theorem.

## Theorem 1

The PDF displays one radical over both regret terms, while the proof adds two
separate terms. Three readings are evaluated:

* `bound_proof` — `expert + current + sqrt(2 log(t-1) A) + B K R sqrt((log m + 1)/m)`;
* `bound_display` — `expert + current + sqrt(2 log(t-1) A + B K R) * sqrt((log m + 1)/m)`;
* `bound_radical_all` — `expert + current + sqrt(2 log(t-1) A + B K R sqrt((log m + 1)/m))`.

Only `bound_proof` reproduces **both** special cases stated in the paper:
`alpha == 1` gives `sqrt(2 m log(t-1))`, and `alpha == 0` gives
`K R sqrt(m (log m + 1))`. The displayed formula reproduces neither.

| Run | `K` | `R` | Median `CE_t` | Median proof bound | Median ratio | Proof covers | Display covers |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `syn1` / AKLO | 24.115 | 44.808 | 354.87 | 1310.22 | 3.732 | 100.0% | 0.0% |
| `syn3` / AKLO | 24.115 | 1.453 | 216.08 | 253.30 | 1.115 | 93.9% | 10.2% |
| `syn1` / AKLO, `delta_alpha=0.0001` | 24.115 | 44.808 | 232.52 | 172.17 | 0.969 | 36.7% | 0.0% |
| `syn1` / AKLO, `delta_alpha=0.01` | 24.115 | 44.808 | 2053.20 | 12690.12 | 6.183 | 100.0% | 0.0% |

Ratios are `bound / CE_t`; a ratio above 1 means the bound covers the observed
error. The `bound_proof` reading is the only one that is broadly consistent
with the empirical error. It is not uniformly valid: with
`delta_alpha=0.0001` the meta term stays large for longer and the bound covers
only 36.7% of tasks, which is expected because the constant-`eta` update does
not satisfy the theorem's schedule. On `syn3`, the few uncovered tasks are
driven by the unbounded squared meta loss.

The `R` sweep in each JSON shows that the conclusion is not an artifact of the
post-hoc `R`: on `syn1`, the median ratio is 1.91 at `0.5 R`, 3.73 at `R`, and
18.15 at `5 R`, with coverage rising from 98% to 100%. On `syn3`, coverage rises
from 61.2% at `0.5 R` to 100% at `2 R`.

## Corollary 1.1

The corollary applies when `m_t <= i_0`, where
`i_0 = max{i : alpha_i >= N/(1+N)}` and

```
N >= (1/gamma) * max{ zeta_l / zeta_e, K R / sqrt(2 log(t-1)) }.
```

In all ten runs, **0 of 48** analyzed tasks satisfy the condition at
`m_t = 100`. The reason is visible in the required `N`:

| Run | Largest `i_0` | Task | `N` at `gamma=1` |
| --- | ---: | ---: | ---: |
| `syn1` / AKLO | 3 | 12 | 493.4 |
| `syn1` / AKLO, `delta_alpha=0.0001` | 26 | 41 | 397.8 |
| `syn1` / AKLO, `delta_alpha=0.01` | 1 | 3 | 917.7 |
| `syn3` / AKLO | 74 | 47 | 12.7 |

For classification, `K R / sqrt(2 log(t-1))` is of order `10^2`–`10^3`, so
`N/(1+N)` is essentially 1: `alpha` would have to stay above roughly `0.99`
for all 100 observations. The default `delta_alpha=0.001` reaches that
threshold for at most 3 steps. Even `delta_alpha=0.0001` reaches only 26 steps,
and `delta_alpha=0.01` reaches 1 step. On `syn3`, the much smaller `R=1.45`
brings `i_0` up to 74, but 74 is still below `m_t=100`; the corollary could
become feasible at a smaller `m_t`.

This is a **scope limitation**, not a counterexample: the corollary explicitly
targets the small-interaction regime, and `m_t=100` with a fast-decaying
`alpha` is outside it. The practical message is that the Section 6 defaults
put the corollary's hypothesis out of reach.

## Corollary 1.2

AKLOMS builds a `2*tau` packing from prediction differences. The bound replaces
the expert regret with

```
2 sqrt(N(tau, S_t) log N(tau, S_t)) * sum_i alpha_i + 2 tau * sum_i alpha_i
```

The table uses the actual cover size as a surrogate for `N(tau, S_t)`. Because
the algorithm builds a `2*tau` packing, `|Lambda_t| <= P(2*tau) <= N(tau)`, so
this surrogate is **optimistic**: the true covering number can only make the
bound larger.

| `tau` | Median cover | Final cover at `t=50` | Knowledge at `t=50` | Median bound/CE | Final bound/CE |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 25.0 | 49 | 49 | 6.786 | 6.786 |
| 0.01 | 25.0 | 49 | 49 | 6.168 | 5.576 |
| 0.1 | 25.0 | 49 | 49 | 6.205 | 5.600 |
| 1 | 25.0 | 49 | 49 | 6.583 | 5.877 |
| 5 | 25.0 | 47 | 49 | 8.105 | 5.764 |
| 10 | 25.0 | 45 | 49 | 10.750 | 8.092 |

The cover barely shrinks on this stream: for `tau <= 1` it contains the whole
knowledge base, and even `tau=10` keeps 45 of 49 models. The paper's Figure 7
shows a much stronger reduction, so this is a meaningful discrepancy. Two
factors are visible in the traces:

* the models' raw predictions differ by far more than `2*tau` because the
  constant-`eta` updates produce very different weight vectors across tasks;
* the shuffled 200-task stream visits very different regions, so most old
  models remain "far" from the current cover.

The packing check confirms that the cover is a valid prediction-space
`2*tau` packing: for `tau=0.1`, none of the sampled task/model pairs fall below
`2*tau` in either prediction or loss space. For `tau=10`, up to 5% of
loss-space pairs fall below `2*tau` even though prediction-space pairs do not,
which reflects the difference between the algorithm's prediction criterion and
the theory's loss criterion.

The cover bound is looser than Theorem 1's bound even at `tau=0` (median ratio
6.79 versus 3.73), because the `2 sqrt(N log N) * sum alpha` term is much larger
than `sqrt(2 log(t-1) * sum alpha)` at these cover sizes.

### Cross-check against E6/E7

The theory trace uses 50 tasks; E6/E7 run the full 200-task stream. The
cover-size pattern is the same. In E6 (`syn1`, 200 tasks, `seed=0`):

| `tau` | ACE (%) | Cover / knowledge base |
| ---: | ---: | ---: |
| 0.001 | 11.84 | 199 / 200 |
| 1 | 12.16 | 199 / 200 |
| 10 | 12.61 | 192 / 200 |
| 100 | 23.13 | 91 / 200 (45.5%) |

E7 shows the same trend for 50–400 tasks: the selected-model ratio is 98–99%
for `tau <= 1`, 86.7–91.0% at `tau=25`, and never approaches the 0–20% region
that the paper's Figure 7 highlights. The paper's `tau` axis is therefore not
directly comparable to ours: the cover test uses raw prediction differences,
so the effective threshold depends on the weight norm. The qualitative
trade-off (larger `tau` → smaller cover, higher ACE) is reproduced, but the
absolute model-ratio range is not.

## Files

Each run produces:

* `reports/theory/<dataset>-<method>[-tau...][-da...]-s<seed>.json` — full
  per-task records, including the three Theorem 1 readings and the `R` sweep;
* `reports/theory/<dataset>-<method>[-tau...][-da...]-s<seed>.md` — the
  human-readable version of the same analysis.

The implementation is in [`src/aklo/theory.py`](../../src/aklo/theory.py) and
[`scripts/check_theory.py`](../../scripts/check_theory.py); tests are in
[`tests/test_theory.py`](../../tests/test_theory.py).
