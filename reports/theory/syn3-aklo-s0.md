# Theory check: syn3 / aklo, seed 0

This report instruments one run and evaluates the paper's bounds post hoc.  It is a diagnostic, not a benchmark: the Section 6 implementation uses a constant learning rate and does not project the iterates, while Theorem 1 assumes a specific decaying schedule and a fixed norm ball.

## Setup

| quantity | value |
| --- | --- |
| `n_tasks_traced` | 50 |
| `n_tasks_analyzed` | 49 |
| `n_features` | 2 |
| `task_type` | regression |
| `meta_loss` | squared |
| `current_loss` | absolute |
| `K` | 24.1151 |
| `R` | 1.4530 |
| `R_observed` | 1.4530 |
| `max_meta_loss` | 138.1375 |
| `max_current_loss` | 25.7612 |

## Assumption audit

| assumption | status |
| --- | --- |
| meta loss bounded in [0, 1] | violated (observed [0.0000, 138.1375]) |
| current loss K-Lipschitz | hinge/absolute are K-Lipschitz with `K = max ||x|| = 24.1151` |
| `||w|| <= R` | the implementation does not project; `R` is the post-hoc maximum observed norm (1.4530) |
| `eta_i = 1/(i lambda)` | **violated**: the Section 6 configuration uses a constant `eta` |
| `alpha_1 = 1`, non-increasing | satisfied by the implementation |

## Theorem 1

The PDF displays one radical over both regret terms, while the proof adds two separate terms.  We report three readings:

* `bound_proof`: `expert + current + sqrt(2 log(t-1) A) + B K R sqrt((log m+1)/m)` (the two propositions added).
* `bound_display`: `expert + current + sqrt(2 log(t-1) A + B K R) * sqrt((log m+1)/m)` (the displayed formula).
* `bound_radical_all`: `expert + current + sqrt(2 log(t-1) A + B K R sqrt((log m+1)/m))` (small radical inside the large one).

Only `bound_proof` reproduces both special cases stated in the paper: `alpha == 1` gives `sqrt(2 m log(t-1))`, and `alpha == 0` gives `K R sqrt(m (log m+1))`.

| metric | value |
| --- | --- |
| `median_CE` | 216.0824 |
| `median_bound_proof` | 253.3003 |
| `median_bound_display` | 192.5533 |
| `median_ratio_proof` | 1.1148 |
| `median_ratio_display` | 0.8977 |
| `fraction_ce_le_bound_proof` | 0.9388 |
| `fraction_ce_le_bound_display` | 0.1020 |
| `fraction_ce_le_bound_radical_all` | 0.2857 |

A ratio above 1 means the bound covers the empirical error.  The fractions are over all analyzed tasks (task 1 is excluded because the theorem is stated for a task with accumulated knowledge).

### Per-task values

| t | m | CE | expert | current | regret expert | regret current | bound proof | bound display | ratio proof | ratio display |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 100 | 3716.6532 | 3691.6049 | 0.0000 | 0.0000 | 41.0643 | 3732.6692 | 3694.7229 | 1.0043 | 0.9941 |
| 5 | 100 | 2937.1215 | 2962.5068 | 0.0000 | 16.2337 | 41.0643 | 3019.8048 | 2967.4559 | 1.0282 | 1.0103 |
| 8 | 100 | 1518.7356 | 1527.8156 | 0.0000 | 19.2332 | 41.0643 | 1588.1131 | 1533.3343 | 1.0457 | 1.0096 |
| 11 | 100 | 876.3272 | 872.2993 | 0.0000 | 20.9218 | 41.0643 | 934.2854 | 878.1523 | 1.0661 | 1.0021 |
| 14 | 100 | 239.4261 | 344.7813 | 0.0000 | 22.0816 | 41.0643 | 407.9272 | 350.8683 | 1.7038 | 1.4655 |
| 17 | 100 | 275.1445 | 256.4165 | 0.0000 | 22.9580 | 41.0643 | 320.4388 | 262.6827 | 1.1646 | 0.9547 |
| 20 | 100 | 143.9735 | 81.6635 | 0.0000 | 23.6588 | 41.0643 | 146.3865 | 88.0741 | 1.0168 | 0.6117 |
| 23 | 100 | 207.8250 | 155.5988 | 0.0000 | 24.2406 | 41.0643 | 220.9037 | 162.1301 | 1.0629 | 0.7801 |
| 26 | 100 | 210.0813 | 196.6621 | 0.0000 | 24.7368 | 41.0643 | 262.4631 | 203.2969 | 1.2493 | 0.9677 |
| 29 | 100 | 232.8113 | 174.1583 | 0.0000 | 25.1685 | 41.0643 | 240.3911 | 180.8835 | 1.0326 | 0.7770 |
| 32 | 100 | 203.2482 | 158.2900 | 0.0000 | 25.5500 | 41.0643 | 224.9043 | 165.0954 | 1.1066 | 0.8123 |
| 35 | 100 | 207.2191 | 175.4591 | 0.0000 | 25.8913 | 41.0643 | 242.4148 | 182.3364 | 1.1698 | 0.8799 |
| 38 | 100 | 223.5165 | 184.9635 | 0.0000 | 26.1999 | 41.0643 | 252.2277 | 191.9059 | 1.1285 | 0.8586 |
| 41 | 100 | 234.7109 | 216.5044 | 0.0000 | 26.4812 | 41.0643 | 284.0500 | 223.5065 | 1.2102 | 0.9523 |
| 44 | 100 | 216.0824 | 185.4964 | 0.0000 | 26.7396 | 41.0643 | 253.3003 | 192.5533 | 1.1722 | 0.8911 |
| 47 | 100 | 98.2038 | 37.5278 | 0.0000 | 26.9782 | 41.0643 | 105.5703 | 44.6354 | 1.0750 | 0.4545 |
| 50 | 100 | 101.1532 | 40.2968 | 0.0000 | 27.1999 | 41.0643 | 108.5610 | 47.4516 | 1.0732 | 0.4691 |

## Corollary 1.1 (small interactions)

| metric | value |
| --- | --- |
| `corollary_1_1_applicable` | 48 |
| `corollary_1_1_feasible` | 0 |
| `corollary_1_1_feasible_fraction` | 0.0000 |
| `corollary_1_1_median_ratio_when_feasible` | — |

The condition is `m_t <= i_0(N)`, where `i_0` is the last index with `alpha_i >= N/(1+N)` and `N` is the corollary's required interaction parameter.  When the condition fails, the corollary is outside its hypothesis and a violated inequality is not a counterexample.

| t | zeta_e | zeta_l | N (gamma=1) | i0 | feasible | bound | ratio |
| ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| 3 | 6474.6701 | 0.0000 | 29.7603 | 33 | no | 12322.6833 | 1.9813 |
| 7 | 4408.6755 | 0.0000 | 18.5102 | 52 | no | 8422.3400 | 1.9809 |
| 11 | 917.9086 | 0.0000 | 16.3283 | 58 | no | 1786.4422 | 2.0386 |
| 15 | 230.6206 | 0.0000 | 15.2520 | 62 | no | 484.0581 | 1.9062 |
| 19 | 152.2230 | 0.0000 | 14.5738 | 65 | no | 335.0840 | 1.9400 |
| 23 | 163.9540 | 0.0000 | 14.0928 | 67 | no | 359.6787 | 1.7307 |
| 27 | 185.8729 | 0.0000 | 13.7268 | 68 | no | 403.3959 | 1.9736 |
| 31 | 253.5121 | 0.0000 | 13.4349 | 70 | no | 534.1634 | 2.1597 |
| 35 | 183.8851 | 0.0000 | 13.1943 | 71 | no | 402.7010 | 1.9434 |
| 39 | 30.2286 | 0.0000 | 12.9910 | 72 | no | 110.0288 | 1.2385 |
| 43 | 238.6693 | 0.0000 | 12.8159 | 73 | no | 508.4322 | 2.0539 |
| 47 | 39.2709 | 0.0000 | 12.6627 | 74 | no | 129.0120 | 1.3137 |
| 50 | 42.4728 | 0.0000 | 12.5595 | 74 | no | 134.9933 | 1.3345 |

## R sensitivity

| R multiplier | R | median ratio (proof) | fraction covered |
| ---: | ---: | ---: | ---: |
| 0.5000 | 0.7265 | 1.0339 | 0.6122 |
| 1.0000 | 1.4530 | 1.1148 | 0.9388 |
| 2.0000 | 2.9061 | 1.3607 | 1.0000 |
| 5.0000 | 7.2652 | 1.9147 | 1.0000 |

The bound grows linearly in `R`, but a larger feasible ball also lowers the current-predictor oracle term.  The sweep makes the dependence explicit instead of hiding it behind one arbitrary `R`.
