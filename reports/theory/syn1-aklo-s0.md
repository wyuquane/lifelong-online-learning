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
| `max_meta_loss` | 237.7827 |
| `max_current_loss` | 470.5931 |

## Assumption audit

| assumption | status |
| --- | --- |
| meta loss bounded in [0, 1] | violated (observed [0.0000, 237.7827]) |
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
| `median_CE` | 354.8727 |
| `median_bound_proof` | 1310.2244 |
| `median_bound_display` | 37.0078 |
| `median_ratio_proof` | 3.7322 |
| `median_ratio_display` | 0.1066 |
| `fraction_ce_le_bound_proof` | 1.0000 |
| `fraction_ce_le_bound_display` | 0.0000 |
| `fraction_ce_le_bound_radical_all` | 0.0000 |

A ratio above 1 means the bound covers the empirical error.  The fractions are over all analyzed tasks (task 1 is excluded because the theorem is stated for a task with accumulated knowledge).

### Per-task values

| t | m | CE | expert | current | regret expert | regret current | bound proof | bound display | ratio proof | ratio display |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 100 | 291.3065 | 144.0435 | 0.0452 | 0.0000 | 1266.3343 | 1410.4230 | 161.4037 | 4.8417 | 0.5541 |
| 5 | 100 | 323.4339 | 166.2517 | 0.0754 | 16.2337 | 1266.3343 | 1448.8951 | 184.0635 | 4.4797 | 0.5691 |
| 8 | 100 | 885.0824 | 641.3108 | 0.0000 | 19.2332 | 1266.3343 | 1926.8783 | 659.2145 | 2.1771 | 0.7448 |
| 11 | 100 | 936.5129 | 612.9512 | 0.0000 | 20.9218 | 1266.3343 | 1900.2072 | 630.9607 | 2.0290 | 0.6737 |
| 14 | 100 | 351.1862 | 93.2428 | 0.0181 | 22.0816 | 1266.3343 | 1381.6768 | 111.3479 | 3.9343 | 0.3171 |
| 17 | 100 | 697.9550 | 228.2293 | 0.0000 | 22.9580 | 1266.3343 | 1517.5216 | 246.3773 | 2.1742 | 0.3530 |
| 20 | 100 | 674.3060 | 62.2184 | 0.0539 | 23.6588 | 1266.3343 | 1352.2653 | 80.4707 | 2.0054 | 0.1193 |
| 23 | 100 | 503.2336 | 12.0989 | 0.0000 | 24.2406 | 1266.3343 | 1302.6738 | 30.3402 | 2.5886 | 0.0603 |
| 26 | 100 | 272.5847 | 16.4721 | 0.0786 | 24.7368 | 1266.3343 | 1307.6218 | 34.8293 | 4.7971 | 0.1278 |
| 29 | 100 | 551.9102 | 18.5925 | 0.1037 | 25.1685 | 1266.3343 | 1310.1990 | 37.0078 | 2.3739 | 0.0671 |
| 32 | 100 | 259.3577 | 1.9327 | 0.0211 | 25.5500 | 1266.3343 | 1293.8381 | 20.2950 | 4.9886 | 0.0783 |
| 35 | 100 | 354.8727 | 84.0218 | 0.0000 | 25.8913 | 1266.3343 | 1376.2474 | 102.3898 | 3.8781 | 0.2885 |
| 38 | 100 | 322.0779 | 27.8157 | 0.0482 | 26.1999 | 1266.3343 | 1320.3981 | 46.2564 | 4.0996 | 0.1436 |
| 41 | 100 | 338.7409 | 1.5308 | 0.0000 | 26.4812 | 1266.3343 | 1294.3463 | 19.9459 | 3.8211 | 0.0589 |
| 44 | 100 | 291.3767 | 6.4896 | 0.0000 | 26.7396 | 1266.3343 | 1299.5634 | 24.9256 | 4.4601 | 0.0855 |
| 47 | 100 | 596.3035 | 19.6309 | 0.0417 | 26.9782 | 1266.3343 | 1312.9851 | 38.1280 | 2.2019 | 0.0639 |
| 50 | 100 | 575.1154 | 11.0598 | 0.0000 | 27.1999 | 1266.3343 | 1304.5940 | 29.5335 | 2.2684 | 0.0514 |

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
| 3 | 6372.5070 | 1.3812 | 917.7429 | 2 | no | 12145.4631 | 1.8921 |
| 7 | 958.4968 | 0.2227 | 570.8131 | 2 | no | 1865.0021 | 1.4786 |
| 11 | 641.8535 | 0.0000 | 503.5307 | 2 | no | 1267.7459 | 1.3537 |
| 15 | 619.0957 | 0.4025 | 470.3372 | 3 | no | 1219.4663 | 1.3507 |
| 19 | 6.5095 | 0.4643 | 449.4247 | 3 | no | 59.5357 | 0.1892 |
| 23 | 12.7078 | 0.0000 | 434.5915 | 3 | no | 72.6790 | 0.1444 |
| 27 | 8.0286 | 0.0000 | 423.3034 | 3 | no | 65.0744 | 0.1910 |
| 31 | 19.6332 | 0.0000 | 414.3028 | 3 | no | 87.7803 | 0.3191 |
| 35 | 89.4346 | 0.0000 | 406.8838 | 3 | no | 219.8263 | 0.6195 |
| 39 | 72.2549 | 0.1830 | 400.6149 | 3 | no | 189.5432 | 0.2638 |
| 43 | 2.1189 | 0.4442 | 395.2149 | 3 | no | 57.3123 | 0.1845 |
| 47 | 21.3345 | 0.8174 | 390.4913 | 3 | no | 93.2182 | 0.1563 |
| 50 | 12.0108 | 0.0000 | 387.3088 | 3 | no | 76.5194 | 0.1331 |

## R sensitivity

| R multiplier | R | median ratio (proof) | fraction covered |
| ---: | ---: | ---: | ---: |
| 0.5000 | 22.4042 | 1.9130 | 0.9796 |
| 1.0000 | 44.8084 | 3.7322 | 1.0000 |
| 2.0000 | 89.6167 | 7.3711 | 1.0000 |
| 5.0000 | 224.0418 | 18.1518 | 1.0000 |

The bound grows linearly in `R`, but a larger feasible ball also lowers the current-predictor oracle term.  The sweep makes the dependence explicit instead of hiding it behind one arbitrary `R`.
