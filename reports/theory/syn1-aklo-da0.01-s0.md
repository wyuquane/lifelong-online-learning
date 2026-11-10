# Theory check: syn1 / aklo, seed 0

This report instruments one run and evaluates the paper's bounds post hoc.  It is a diagnostic, not a benchmark: the Section 6 implementation uses a constant learning rate and does not project the iterates, while Theorem 1 assumes a specific decaying schedule and a fixed norm ball.

## Setup

| quantity | value |
| --- | --- |
| `n_tasks_traced` | 50 |
| `n_tasks_analyzed` | 49 |
| `n_features` | 2 |
| `task_type` | classification |
| `meta_loss` | hinge |
| `current_loss` | hinge |
| `K` | 24.1151 |
| `R` | 44.8084 |
| `R_observed` | 44.8084 |
| `max_meta_loss` | 238.1588 |
| `max_current_loss` | 470.5931 |

## Assumption audit

| assumption | status |
| --- | --- |
| meta loss bounded in [0, 1] | violated (observed [0.0000, 238.1588]) |
| current loss K-Lipschitz | hinge/absolute are K-Lipschitz with `K = max ||x|| = 24.1151` |
| `||w|| <= R` | the implementation does not project; `R` is the post-hoc maximum observed norm (44.8084) |
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
| `median_CE` | 2053.2025 |
| `median_bound_proof` | 12690.1177 |
| `median_bound_display` | 66.7379 |
| `median_ratio_proof` | 6.1834 |
| `median_ratio_display` | 0.0342 |
| `fraction_ce_le_bound_proof` | 1.0000 |
| `fraction_ce_le_bound_display` | 0.0000 |
| `fraction_ce_le_bound_radical_all` | 0.0000 |

A ratio above 1 means the bound covers the empirical error.  The fractions are over all analyzed tasks (task 1 is excluded because the theorem is stated for a task with accumulated knowledge).

### Per-task values

| t | m | CE | expert | current | regret expert | regret current | bound proof | bound display | ratio proof | ratio display |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 100 | 1548.7242 | 76.0944 | 0.4517 | 0.0000 | 12663.3426 | 12739.8887 | 131.3008 | 8.2261 | 0.0848 |
| 5 | 100 | 1022.0629 | 103.5063 | 0.7541 | 11.8328 | 12663.3426 | 12779.4359 | 159.0867 | 12.5036 | 0.1557 |
| 8 | 100 | 1434.5831 | 305.4484 | 0.0000 | 14.0192 | 12663.3426 | 12982.8102 | 360.3036 | 9.0499 | 0.2512 |
| 11 | 100 | 2259.1555 | 352.8303 | 0.0000 | 15.2500 | 12663.3426 | 13031.4228 | 407.7039 | 5.7683 | 0.1805 |
| 14 | 100 | 1538.1605 | 45.3225 | 0.1812 | 16.0953 | 12663.3426 | 12724.9416 | 100.3908 | 8.2728 | 0.0653 |
| 17 | 100 | 3518.6565 | 110.1678 | 0.0000 | 16.7341 | 12663.3426 | 12790.2446 | 165.0657 | 3.6350 | 0.0469 |
| 20 | 100 | 4938.6442 | 30.3806 | 0.5392 | 17.2450 | 12663.3426 | 12711.5075 | 85.8266 | 2.5739 | 0.0174 |
| 23 | 100 | 2852.2880 | 6.6189 | 0.0000 | 17.6690 | 12663.3426 | 12687.6306 | 61.5332 | 4.4482 | 0.0216 |
| 26 | 100 | 1422.3389 | 5.1722 | 0.7862 | 18.0307 | 12663.3426 | 12687.3318 | 60.8793 | 8.9200 | 0.0428 |
| 29 | 100 | 2053.2025 | 12.9564 | 1.0370 | 18.3454 | 12663.3426 | 12695.6814 | 68.9201 | 6.1834 | 0.0336 |
| 32 | 100 | 1741.0282 | 0.8368 | 0.2111 | 18.6234 | 12663.3426 | 12683.0140 | 55.9799 | 7.2848 | 0.0322 |
| 35 | 100 | 1561.4729 | 35.3065 | 0.0000 | 18.8723 | 12663.3426 | 12717.5214 | 90.2432 | 8.1446 | 0.0578 |
| 38 | 100 | 1813.2100 | 16.9692 | 0.4816 | 19.0972 | 12663.3426 | 12699.8907 | 72.3919 | 7.0041 | 0.0399 |
| 41 | 100 | 2254.8467 | 0.8258 | 0.0000 | 19.3022 | 12663.3426 | 12683.4707 | 55.7708 | 5.6250 | 0.0247 |
| 44 | 100 | 1530.4399 | 1.4279 | 0.0000 | 19.4905 | 12663.3426 | 12684.2611 | 56.3767 | 8.2880 | 0.0368 |
| 47 | 100 | 3252.6285 | 4.2977 | 0.4172 | 19.6645 | 12663.3426 | 12687.7221 | 59.6672 | 3.9008 | 0.0183 |
| 50 | 100 | 3085.7734 | 2.5007 | 0.0000 | 19.8261 | 12663.3426 | 12685.6694 | 57.4562 | 4.1110 | 0.0186 |

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
| 3 | 6372.5070 | 1.3812 | 917.7429 | 1 | no | 6536.6597 | 0.9817 |
| 7 | 958.4968 | 0.2227 | 570.8131 | 1 | no | 1054.8691 | 0.4183 |
| 11 | 641.8535 | 0.0000 | 503.5307 | 1 | no | 736.1604 | 0.3259 |
| 15 | 619.0957 | 0.4025 | 470.3372 | 1 | no | 635.6263 | 0.3070 |
| 19 | 6.5095 | 0.4643 | 449.4247 | 1 | no | 43.5470 | 0.0250 |
| 23 | 12.7078 | 0.0000 | 434.5915 | 1 | no | 48.5760 | 0.0170 |
| 27 | 8.0286 | 0.0000 | 423.3034 | 1 | no | 44.7691 | 0.0218 |
| 31 | 19.6332 | 0.0000 | 414.3028 | 1 | no | 52.9203 | 0.0316 |
| 35 | 89.4346 | 0.0000 | 406.8838 | 1 | no | 108.3575 | 0.0694 |
| 39 | 72.2549 | 0.1830 | 400.6149 | 1 | no | 107.2485 | 0.0249 |
| 43 | 2.1189 | 0.4442 | 395.2149 | 1 | no | 40.7254 | 0.0235 |
| 47 | 21.3345 | 0.8174 | 390.4913 | 1 | no | 47.9244 | 0.0147 |
| 50 | 12.0108 | 0.0000 | 387.3088 | 1 | no | 44.6535 | 0.0145 |

## R sensitivity

| R multiplier | R | median ratio (proof) | fraction covered |
| ---: | ---: | ---: | ---: |
| 0.5000 | 22.4042 | 3.0996 | 1.0000 |
| 1.0000 | 44.8084 | 6.1834 | 1.0000 |
| 2.0000 | 89.6167 | 12.3508 | 1.0000 |
| 5.0000 | 224.0418 | 30.8508 | 1.0000 |

The bound grows linearly in `R`, but a larger feasible ball also lowers the current-predictor oracle term.  The sweep makes the dependence explicit instead of hiding it behind one arbitrary `R`.
