# Theory check: syn1 / akloms (tau=5), seed 0

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
| `median_CE` | 460.8527 |
| `median_bound_proof` | 1310.2244 |
| `median_bound_display` | 37.0078 |
| `median_ratio_proof` | 2.8110 |
| `median_ratio_display` | 0.1046 |
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
| 11 | 100 | 990.2448 | 612.9512 | 0.0000 | 20.9218 | 1266.3343 | 1900.2072 | 630.9607 | 1.9189 | 0.6372 |
| 14 | 100 | 350.5411 | 93.2428 | 0.0181 | 22.0816 | 1266.3343 | 1381.6768 | 111.3479 | 3.9416 | 0.3176 |
| 17 | 100 | 728.2900 | 228.2293 | 0.0000 | 22.9580 | 1266.3343 | 1517.5216 | 246.3773 | 2.0837 | 0.3383 |
| 20 | 100 | 672.9947 | 62.2184 | 0.0539 | 23.6588 | 1266.3343 | 1352.2653 | 80.4707 | 2.0093 | 0.1196 |
| 23 | 100 | 940.1483 | 12.0989 | 0.0000 | 24.2406 | 1266.3343 | 1302.6738 | 30.3402 | 1.3856 | 0.0323 |
| 26 | 100 | 289.1696 | 16.4721 | 0.0786 | 24.7368 | 1266.3343 | 1307.6218 | 34.8293 | 4.5220 | 0.1204 |
| 29 | 100 | 443.9609 | 18.5925 | 0.1037 | 25.1685 | 1266.3343 | 1310.1990 | 37.0078 | 2.9512 | 0.0834 |
| 32 | 100 | 275.8444 | 1.9327 | 0.0211 | 25.5500 | 1266.3343 | 1293.8381 | 20.2950 | 4.6905 | 0.0736 |
| 35 | 100 | 450.6193 | 84.0218 | 0.0000 | 25.8913 | 1266.3343 | 1376.2474 | 102.3898 | 3.0541 | 0.2272 |
| 38 | 100 | 320.5339 | 27.8157 | 0.0482 | 26.1999 | 1266.3343 | 1320.3981 | 46.2564 | 4.1194 | 0.1443 |
| 41 | 100 | 339.7978 | 1.5308 | 0.0000 | 26.4812 | 1266.3343 | 1294.3463 | 19.9459 | 3.8092 | 0.0587 |
| 44 | 100 | 440.2013 | 6.4896 | 0.0000 | 26.7396 | 1266.3343 | 1299.5634 | 24.9256 | 2.9522 | 0.0566 |
| 47 | 100 | 788.3241 | 19.6309 | 0.0417 | 26.9782 | 1266.3343 | 1312.9851 | 38.1280 | 1.6655 | 0.0484 |
| 50 | 100 | 830.1175 | 11.0598 | 0.0000 | 27.1999 | 1266.3343 | 1304.5940 | 29.5335 | 1.5716 | 0.0356 |

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
| 11 | 641.8535 | 0.0000 | 503.5307 | 2 | no | 1267.7459 | 1.2802 |
| 15 | 619.0957 | 0.4025 | 470.3372 | 3 | no | 1219.4663 | 1.3456 |
| 19 | 6.5095 | 0.4643 | 449.4247 | 3 | no | 59.5357 | 0.0976 |
| 23 | 12.7078 | 0.0000 | 434.5915 | 3 | no | 72.6790 | 0.0773 |
| 27 | 8.0286 | 0.0000 | 423.3034 | 3 | no | 65.0744 | 0.2152 |
| 31 | 19.6332 | 0.0000 | 414.3028 | 3 | no | 87.7803 | 0.2924 |
| 35 | 89.4346 | 0.0000 | 406.8838 | 3 | no | 219.8263 | 0.4878 |
| 39 | 72.2549 | 0.1830 | 400.6149 | 3 | no | 189.5432 | 0.2409 |
| 43 | 2.1189 | 0.4442 | 395.2149 | 3 | no | 57.3123 | 0.1227 |
| 47 | 21.3345 | 0.8174 | 390.4913 | 3 | no | 93.2182 | 0.1182 |
| 50 | 12.0108 | 0.0000 | 387.3088 | 3 | no | 76.5194 | 0.0922 |

## Corollary 1.2 (cover-set knowledge)

| metric | value |
| --- | --- |
| `corollary_1_2_median_cover_size` | 25.0000 |
| `corollary_1_2_median_knowledge_size` | 25.0000 |
| `corollary_1_2_median_ratio_cover_size` | 8.1046 |

The bound uses the actual cover size as a surrogate for the covering number `N(tau, S_t)`.  Because the algorithm builds a `2*tau` packing, `|Lambda_t| <= P(2*tau) <= N(tau)`, so this surrogate is optimistic: the true covering number can only make the bound larger.

| t | cover | P(tau) | P(2 tau) | bound cover | ratio cover | ratio P(tau) | loss pairs < 2 tau | pred pairs < 2 tau |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | 4 | 4 | 4 | 2830.8127 | 8.8579 | 8.8579 | 0.0000 | 0.0000 |
| 9 | 8 | 8 | 8 | 3118.6303 | 5.0814 | 5.0814 | 0.0000 | 0.0000 |
| 12 | 11 | 11 | 11 | 3543.7950 | 3.9363 | 3.9363 | 0.0000 | 0.0000 |
| 16 | 15 | 14 | 14 | 3481.1587 | 14.0428 | 13.8166 | 0.0095 | 0.0000 |
| 19 | 18 | 18 | 16 | 3594.3463 | 5.8905 | 5.8905 | 0.0131 | 0.0000 |
| 23 | 22 | 21 | 21 | 3796.5717 | 4.0383 | 3.9876 | 0.0043 | 0.0043 |
| 26 | 25 | 24 | 21 | 3938.6985 | 13.6207 | 13.4648 | 0.0233 | 0.0033 |
| 29 | 28 | 28 | 25 | 4071.7600 | 9.1714 | 9.1714 | 0.0106 | 0.0079 |
| 33 | 32 | 31 | 26 | 4222.9589 | 11.9130 | 11.7986 | 0.0181 | 0.0020 |
| 36 | 35 | 33 | 29 | 4367.6835 | 6.1663 | 6.0554 | 0.0134 | 0.0017 |
| 40 | 39 | 37 | 30 | 4489.9420 | 13.0541 | 12.8361 | 0.0135 | 0.0040 |
| 43 | 42 | 38 | 34 | 4600.6589 | 9.8489 | 9.5346 | 0.0116 | 0.0035 |
| 47 | 45 | 43 | 38 | 4724.5652 | 5.9932 | 5.9038 | 0.0091 | 0.0040 |
| 50 | 47 | 46 | 41 | 4785.1237 | 5.7644 | 5.7229 | 0.0065 | 0.0028 |

## R sensitivity

| R multiplier | R | median ratio (proof) | fraction covered |
| ---: | ---: | ---: | ---: |
| 0.5000 | 22.4042 | 1.4681 | 0.8776 |
| 1.0000 | 44.8084 | 2.8110 | 1.0000 |
| 2.0000 | 89.6167 | 5.5587 | 1.0000 |
| 5.0000 | 224.0418 | 13.8021 | 1.0000 |

The bound grows linearly in `R`, but a larger feasible ball also lowers the current-predictor oracle term.  The sweep makes the dependence explicit instead of hiding it behind one arbitrary `R`.
