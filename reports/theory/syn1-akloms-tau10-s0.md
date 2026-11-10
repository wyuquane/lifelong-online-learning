# Theory check: syn1 / akloms (tau=10), seed 0

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
| `max_meta_loss` | 562.6120 |
| `max_current_loss` | 470.5931 |

## Assumption audit

| assumption | status |
| --- | --- |
| meta loss bounded in [0, 1] | violated (observed [0.0000, 562.6120]) |
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
| `median_CE` | 453.4861 |
| `median_bound_proof` | 1310.2244 |
| `median_bound_display` | 37.0078 |
| `median_ratio_proof` | 2.8641 |
| `median_ratio_display` | 0.1006 |
| `fraction_ce_le_bound_proof` | 1.0000 |
| `fraction_ce_le_bound_display` | 0.0000 |
| `fraction_ce_le_bound_radical_all` | 0.0000 |

A ratio above 1 means the bound covers the empirical error.  The fractions are over all analyzed tasks (task 1 is excluded because the theorem is stated for a task with accumulated knowledge).

### Per-task values

| t | m | CE | expert | current | regret expert | regret current | bound proof | bound display | ratio proof | ratio display |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 100 | 291.3065 | 144.0435 | 0.0452 | 0.0000 | 1266.3343 | 1410.4230 | 161.4037 | 4.8417 | 0.5541 |
| 5 | 100 | 319.5822 | 166.2517 | 0.0754 | 16.2337 | 1266.3343 | 1448.8951 | 184.0635 | 4.5337 | 0.5760 |
| 8 | 100 | 927.9341 | 641.3108 | 0.0000 | 19.2332 | 1266.3343 | 1926.8783 | 659.2145 | 2.0765 | 0.7104 |
| 11 | 100 | 882.4610 | 612.9512 | 0.0000 | 20.9218 | 1266.3343 | 1900.2072 | 630.9607 | 2.1533 | 0.7150 |
| 14 | 100 | 350.5409 | 93.2428 | 0.0181 | 22.0816 | 1266.3343 | 1381.6768 | 111.3479 | 3.9416 | 0.3176 |
| 17 | 100 | 677.2990 | 228.2293 | 0.0000 | 22.9580 | 1266.3343 | 1517.5216 | 246.3773 | 2.2405 | 0.3638 |
| 20 | 100 | 668.5761 | 62.2184 | 0.0539 | 23.6588 | 1266.3343 | 1352.2653 | 80.4707 | 2.0226 | 0.1204 |
| 23 | 100 | 940.1483 | 12.0989 | 0.0000 | 24.2406 | 1266.3343 | 1302.6738 | 30.3402 | 1.3856 | 0.0323 |
| 26 | 100 | 289.1696 | 16.4721 | 0.0786 | 24.7368 | 1266.3343 | 1307.6218 | 34.8293 | 4.5220 | 0.1204 |
| 29 | 100 | 443.9041 | 18.5925 | 0.1037 | 25.1685 | 1266.3343 | 1310.1990 | 37.0078 | 2.9515 | 0.0834 |
| 32 | 100 | 275.8444 | 1.9327 | 0.0211 | 25.5500 | 1266.3343 | 1293.8381 | 20.2950 | 4.6905 | 0.0736 |
| 35 | 100 | 394.3653 | 84.0218 | 0.0000 | 25.8913 | 1266.3343 | 1376.2474 | 102.3898 | 3.4898 | 0.2596 |
| 38 | 100 | 324.2123 | 27.8157 | 0.0482 | 26.1999 | 1266.3343 | 1320.3981 | 46.2564 | 4.0726 | 0.1427 |
| 41 | 100 | 337.5677 | 1.5308 | 0.0000 | 26.4812 | 1266.3343 | 1294.3463 | 19.9459 | 3.8343 | 0.0591 |
| 44 | 100 | 292.3669 | 6.4896 | 0.0000 | 26.7396 | 1266.3343 | 1299.5634 | 24.9256 | 4.4450 | 0.0853 |
| 47 | 100 | 1028.0019 | 19.6309 | 0.0417 | 26.9782 | 1266.3343 | 1312.9851 | 38.1280 | 1.2772 | 0.0371 |
| 50 | 100 | 700.2575 | 11.0598 | 0.0000 | 27.1999 | 1266.3343 | 1304.5940 | 29.5335 | 1.8630 | 0.0422 |

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
| 3 | 6372.5070 | 1.3812 | 917.7429 | 2 | no | 12145.4631 | 1.8935 |
| 7 | 958.4968 | 0.2227 | 570.8131 | 2 | no | 1865.0021 | 1.4416 |
| 11 | 641.8535 | 0.0000 | 503.5307 | 2 | no | 1267.7459 | 1.4366 |
| 15 | 619.0957 | 0.4025 | 470.3372 | 3 | no | 1219.4663 | 1.2533 |
| 19 | 6.5095 | 0.4643 | 449.4247 | 3 | no | 59.5357 | 0.0795 |
| 23 | 12.7078 | 0.0000 | 434.5915 | 3 | no | 72.6790 | 0.0773 |
| 27 | 8.0286 | 0.0000 | 423.3034 | 3 | no | 65.0744 | 0.2151 |
| 31 | 19.6332 | 0.0000 | 414.3028 | 3 | no | 87.7803 | 0.2924 |
| 35 | 89.4346 | 0.0000 | 406.8838 | 3 | no | 219.8263 | 0.5574 |
| 39 | 72.2549 | 0.1830 | 400.6149 | 3 | no | 189.5432 | 0.2335 |
| 43 | 2.1189 | 0.4442 | 395.2149 | 3 | no | 57.3123 | 0.1796 |
| 47 | 21.3345 | 0.8174 | 390.4913 | 3 | no | 93.2182 | 0.0907 |
| 50 | 12.0108 | 0.0000 | 387.3088 | 3 | no | 76.5194 | 0.1093 |

## Corollary 1.2 (cover-set knowledge)

| metric | value |
| --- | --- |
| `corollary_1_2_median_cover_size` | 25.0000 |
| `corollary_1_2_median_knowledge_size` | 25.0000 |
| `corollary_1_2_median_ratio_cover_size` | 10.7504 |

The bound uses the actual cover size as a surrogate for the covering number `N(tau, S_t)`.  Because the algorithm builds a `2*tau` packing, `|Lambda_t| <= P(2*tau) <= N(tau)`, so this surrogate is optimistic: the true covering number can only make the bound larger.

| t | cover | P(tau) | P(2 tau) | bound cover | ratio cover | ratio P(tau) | loss pairs < 2 tau | pred pairs < 2 tau |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | 4 | 4 | 4 | 3781.3127 | 11.8321 | 11.8321 | 0.0000 | 0.0000 |
| 9 | 8 | 8 | 8 | 4069.1303 | 6.6302 | 6.6302 | 0.0000 | 0.0000 |
| 12 | 11 | 11 | 10 | 4494.2950 | 4.4768 | 4.4768 | 0.0182 | 0.0000 |
| 16 | 14 | 14 | 13 | 4375.5691 | 19.9205 | 19.9205 | 0.0110 | 0.0000 |
| 19 | 18 | 16 | 13 | 4544.8463 | 6.0724 | 5.9320 | 0.0458 | 0.0196 |
| 23 | 22 | 21 | 15 | 4747.0717 | 5.0493 | 4.9986 | 0.0303 | 0.0087 |
| 26 | 25 | 21 | 17 | 4889.1985 | 16.9077 | 16.2670 | 0.0433 | 0.0167 |
| 29 | 28 | 25 | 24 | 5022.2600 | 11.3138 | 11.0189 | 0.0132 | 0.0132 |
| 33 | 31 | 26 | 21 | 5132.8840 | 14.4818 | 13.8844 | 0.0344 | 0.0129 |
| 36 | 35 | 29 | 21 | 5318.1835 | 7.5082 | 7.1665 | 0.0353 | 0.0101 |
| 40 | 37 | 30 | 24 | 5365.4516 | 17.6828 | 16.7697 | 0.0315 | 0.0150 |
| 43 | 41 | 34 | 24 | 5515.0349 | 17.2795 | 16.4519 | 0.0317 | 0.0122 |
| 47 | 45 | 38 | 34 | 5675.0652 | 5.5205 | 5.2743 | 0.0212 | 0.0111 |
| 50 | 45 | 41 | 35 | 5666.4524 | 8.0920 | 7.8886 | 0.0192 | 0.0091 |

## R sensitivity

| R multiplier | R | median ratio (proof) | fraction covered |
| ---: | ---: | ---: | ---: |
| 0.5000 | 22.4042 | 1.5182 | 0.8367 |
| 1.0000 | 44.8084 | 2.8641 | 1.0000 |
| 2.0000 | 89.6167 | 5.6566 | 1.0000 |
| 5.0000 | 224.0418 | 14.0339 | 1.0000 |

The bound grows linearly in `R`, but a larger feasible ball also lowers the current-predictor oracle term.  The sweep makes the dependence explicit instead of hiding it behind one arbitrary `R`.
