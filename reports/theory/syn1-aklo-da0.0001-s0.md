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
| `max_meta_loss` | 237.7348 |
| `max_current_loss` | 470.5931 |

## Assumption audit

| assumption | status |
| --- | --- |
| meta loss bounded in [0, 1] | violated (observed [0.0000, 237.7348]) |
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
| `median_CE` | 232.5244 |
| `median_bound_proof` | 172.1663 |
| `median_bound_display` | 27.7575 |
| `median_ratio_proof` | 0.9687 |
| `median_ratio_display` | 0.1485 |
| `fraction_ce_le_bound_proof` | 0.3673 |
| `fraction_ce_le_bound_display` | 0.0000 |
| `fraction_ce_le_bound_radical_all` | 0.0000 |

A ratio above 1 means the bound covers the empirical error.  The fractions are over all analyzed tasks (task 1 is excluded because the theorem is stated for a task with accumulated knowledge).

### Per-task values

| t | m | CE | expert | current | regret expert | regret current | bound proof | bound display | ratio proof | ratio display |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 100 | 165.5647 | 150.8384 | 0.0045 | 0.0000 | 126.6334 | 277.4764 | 156.3184 | 1.6759 | 0.9442 |
| 5 | 100 | 253.5447 | 172.5263 | 0.0075 | 16.6098 | 126.6334 | 315.7771 | 179.2751 | 1.2454 | 0.7071 |
| 8 | 100 | 830.0327 | 674.8971 | 0.0000 | 19.6788 | 126.6334 | 821.2093 | 682.0864 | 0.9894 | 0.8218 |
| 11 | 100 | 804.4319 | 638.9632 | 0.0000 | 21.4065 | 126.6334 | 787.0032 | 646.4242 | 0.9783 | 0.8036 |
| 14 | 100 | 232.5244 | 98.0348 | 0.0018 | 22.5932 | 126.6334 | 247.2632 | 105.6912 | 1.0634 | 0.4545 |
| 17 | 100 | 415.9638 | 240.0355 | 0.0000 | 23.4898 | 126.6334 | 390.1587 | 247.8399 | 0.9380 | 0.5958 |
| 20 | 100 | 247.8485 | 65.4021 | 0.0054 | 24.2069 | 126.6334 | 216.2478 | 73.3338 | 0.8725 | 0.2959 |
| 23 | 100 | 268.3687 | 12.6469 | 0.0000 | 24.8022 | 126.6334 | 164.0825 | 20.6757 | 0.6114 | 0.0770 |
| 26 | 100 | 157.5213 | 17.6021 | 0.0079 | 25.3098 | 126.6334 | 169.5533 | 25.7271 | 1.0764 | 0.1633 |
| 29 | 100 | 401.7539 | 19.1561 | 0.0104 | 25.7515 | 126.6334 | 171.5515 | 27.3611 | 0.4270 | 0.0681 |
| 32 | 100 | 111.2037 | 2.0423 | 0.0021 | 26.1419 | 126.6334 | 154.8197 | 10.3080 | 1.3922 | 0.0927 |
| 35 | 100 | 234.1982 | 88.8933 | 0.0000 | 26.4911 | 126.6334 | 242.0179 | 97.2190 | 1.0334 | 0.4151 |
| 38 | 100 | 172.9512 | 28.9004 | 0.0048 | 26.8069 | 126.6334 | 182.3455 | 37.2873 | 1.0543 | 0.2156 |
| 41 | 100 | 147.1161 | 1.6013 | 0.0000 | 27.0947 | 126.6334 | 155.3295 | 10.0352 | 1.0558 | 0.0682 |
| 44 | 100 | 167.5667 | 6.9958 | 0.0000 | 27.3590 | 126.6334 | 160.9882 | 15.4773 | 0.9607 | 0.0924 |
| 47 | 100 | 330.6918 | 21.1642 | 0.0042 | 27.6032 | 126.6334 | 175.4050 | 29.6941 | 0.5304 | 0.0898 |
| 50 | 100 | 324.0918 | 11.9157 | 0.0000 | 27.8300 | 126.6334 | 166.3792 | 20.4827 | 0.5134 | 0.0632 |

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
| 3 | 6372.5070 | 1.3812 | 917.7429 | 11 | no | 12706.2529 | 1.9868 |
| 7 | 958.4968 | 0.2227 | 570.8131 | 18 | no | 1945.8699 | 1.7144 |
| 11 | 641.8535 | 0.0000 | 503.5307 | 20 | no | 1320.7395 | 1.6418 |
| 15 | 619.0957 | 0.4025 | 470.3372 | 22 | no | 1277.6737 | 1.6254 |
| 19 | 6.5095 | 0.4643 | 449.4247 | 23 | no | 60.9498 | 0.3552 |
| 23 | 12.7078 | 0.0000 | 434.5915 | 23 | no | 74.8982 | 0.2791 |
| 27 | 8.0286 | 0.0000 | 423.3034 | 24 | no | 66.9086 | 0.3949 |
| 31 | 19.6332 | 0.0000 | 414.3028 | 25 | no | 91.0658 | 0.6739 |
| 35 | 89.4346 | 0.0000 | 406.8838 | 25 | no | 230.7690 | 0.9854 |
| 39 | 72.2549 | 0.1830 | 400.6149 | 25 | no | 197.5653 | 0.5497 |
| 43 | 2.1189 | 0.4442 | 395.2149 | 26 | no | 58.7607 | 0.3487 |
| 47 | 21.3345 | 0.8174 | 390.4913 | 26 | no | 97.5348 | 0.2949 |
| 50 | 12.0108 | 0.0000 | 387.3088 | 26 | no | 79.4915 | 0.2453 |

## R sensitivity

| R multiplier | R | median ratio (proof) | fraction covered |
| ---: | ---: | ---: | ---: |
| 0.5000 | 22.4042 | 0.6282 | 0.0408 |
| 1.0000 | 44.8084 | 0.9687 | 0.3673 |
| 2.0000 | 89.6167 | 1.5949 | 0.8571 |
| 5.0000 | 224.0418 | 3.2418 | 1.0000 |

The bound grows linearly in `R`, but a larger feasible ball also lowers the current-predictor oracle term.  The sweep makes the dependence explicit instead of hiding it behind one arbitrary `R`.
