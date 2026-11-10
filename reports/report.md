# AKLO reproduction report

Generated from the JSON files in `results/`. Classification ACE is a
percentage; regression ACE is on the target scale. W&B links are
included when the run was tracked online.

## E1: main comparison (paper Table 1)

| Dataset | ITOL | TOL | UnifSum | TransOL | OTB | AKLO | Paper AKLO |
| --- | --- | --- | --- | --- | --- | --- | --- |
| syn1 | [37.32](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/y13cvc2i) | [23.62](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/asaf0vbr) | [49.93](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/6cbca3qn) | [37.10](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/x5pxxxxj) | [19.52](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/s08ez2i0) | [11.95](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/kx6bqnkp) | 10.10 |
| syn2 | [38.12](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/sjqc7zq8) | [37.78](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/l0fj5k96) | [51.38](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/nqx9a7wa) | [44.05](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/v2wbfxr3) | [37.53](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/l2w8ktjr) | [10.32](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/bxtxygw0) | 10.16 |
| landmine | [38.39](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/3yp2a67x) | [38.30](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/wk23p95u) | [39.20](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/gi7os8oj) | [38.21](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/fc18stmj) | [33.95](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/zl8epa1u) | [29.95](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/cd5tvh9w) | 7.30 |
| spam | [25.63](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/9g42hpby) | [20.47](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/icy5j4de) | [24.70](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/qtes0e7n) | [21.20](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/jzxbrhnu) | [17.50](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/d81jwdb9) | [19.50](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/5guq1ur7) | 17.36 |
| syn3 | [7.94](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/ls764uk9) | [7.94](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/jqqpxl2y) | [1.60](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/16e8k0q0) | [5.35](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/gbfmq2i3) | - | [1.06](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/qconblr2) | 4.06 |
| syn4 | [5.18](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/43z8885r) | [5.18](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/vvckxuoz) | [1.40](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/hqd7ze14) | [3.69](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/q81cb2tv) | - | [1.10](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/uderunnz) | 2.98 |
| london | [14.80](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/cam1xnw6) | [12.61](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/x30uqd9i) | [15.02](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/gt2eqx3d) | [13.19](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/gbauolsp) | - | [11.94](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/pngn5o6m) | 10.05 |

### Paper vs reproduction

| Dataset | Method | Paper | Reproduction |
| --- | --- | --- | --- |
| syn1 | ITOL | 36.18 | [37.32](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/y13cvc2i) |
| syn1 | TOL | 21.16 | [23.62](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/asaf0vbr) |
| syn1 | UnifSum | 49.63 | [49.93](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/6cbca3qn) |
| syn1 | TransOL | 36.40 | [37.10](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/x5pxxxxj) |
| syn1 | OTB | 30.19 | [19.52](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/s08ez2i0) |
| syn1 | AKLO | 10.10 | [11.95](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/kx6bqnkp) |
| syn2 | ITOL | 33.70 | [38.12](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/sjqc7zq8) |
| syn2 | TOL | 33.34 | [37.78](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/l0fj5k96) |
| syn2 | UnifSum | 43.07 | [51.38](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/nqx9a7wa) |
| syn2 | TransOL | 32.97 | [44.05](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/v2wbfxr3) |
| syn2 | OTB | 34.90 | [37.53](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/l2w8ktjr) |
| syn2 | AKLO | 10.16 | [10.32](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/bxtxygw0) |
| landmine | ITOL | 13.86 | [38.39](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/3yp2a67x) |
| landmine | TOL | 11.54 | [38.30](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/wk23p95u) |
| landmine | UnifSum | 7.97 | [39.20](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/gi7os8oj) |
| landmine | TransOL | 8.05 | [38.21](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/fc18stmj) |
| landmine | OTB | 10.94 | [33.95](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/zl8epa1u) |
| landmine | AKLO | 7.30 | [29.95](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/cd5tvh9w) |
| spam | ITOL | 25.00 | [25.63](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/9g42hpby) |
| spam | TOL | 19.51 | [20.47](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/icy5j4de) |
| spam | UnifSum | 19.50 | [24.70](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/qtes0e7n) |
| spam | TransOL | 24.50 | [21.20](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/jzxbrhnu) |
| spam | OTB | 24.10 | [17.50](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/d81jwdb9) |
| spam | AKLO | 17.36 | [19.50](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/5guq1ur7) |
| syn3 | ITOL | 14.54 | [7.94](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/ls764uk9) |
| syn3 | TOL | 7.63 | [7.94](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/jqqpxl2y) |
| syn3 | UnifSum | 27.69 | [1.60](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/16e8k0q0) |
| syn3 | TransOL | 61.61 | [5.35](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/gbfmq2i3) |
| syn3 | AKLO | 4.06 | [1.06](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/qconblr2) |
| syn4 | ITOL | 8.02 | [5.18](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/43z8885r) |
| syn4 | TOL | 9.96 | [5.18](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/vvckxuoz) |
| syn4 | UnifSum | 51.23 | [1.40](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/hqd7ze14) |
| syn4 | TransOL | 54.55 | [3.69](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/q81cb2tv) |
| syn4 | AKLO | 2.98 | [1.10](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/uderunnz) |
| london | ITOL | 20.76 | [14.80](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/cam1xnw6) |
| london | TOL | 20.91 | [12.61](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/x30uqd9i) |
| london | UnifSum | 10.94 | [15.02](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/gt2eqx3d) |
| london | TransOL | 79.58 | [13.19](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/gbauolsp) |
| london | AKLO | 10.05 | [11.94](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/pngn5o6m) |

## E2: number of observations per task (paper Figure 3)

| m_t | ITOL | TOL | UnifSum | TransOL | OTB | AKLO |
| --- | --- | --- | --- | --- | --- | --- |
| 10 | [41.85](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/so3ovu92) | [36.90](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/1r3kvnuv) | [42.65](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/f6lz4fgl) | [41.35](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/6ouyec0o) | [34.10](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/pb5j1tq5) | [22.90](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/ufimbj2n) |
| 20 | [41.67](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/h3lmkjwq) | [34.98](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/lfl3a9dg) | [49.50](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/7rquut0a) | [42.38](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/vbonbri5) | [31.55](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/hxlhes34) | [19.25](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/12q10zh7) |
| 40 | [40.40](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/m2ldmurj) | [29.64](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/ftt13afb) | [50.78](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/3majbtbp) | [38.61](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/n776t2dp) | [25.21](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/uqgzdc6m) | [13.11](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/g033qn4b) |
| 80 | [38.96](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/denef87s) | [24.90](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/i3k5d1ny) | [49.57](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/4qfsd0yy) | [36.77](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/d4ptm0zv) | [21.31](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/akq2aqbs) | [13.78](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/phwqmy7b) |
| 160 | [35.85](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/5cobkqqe) | [21.40](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/7cgz72i0) | [50.11](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/qama8yow) | [36.95](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/mhe7i43p) | [17.59](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/h6gx2tt9) | [13.47](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/j8afes28) |
| 200 | [32.85](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/xjbwl4ot) | [20.42](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/8vuv350g) | [50.09](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/nu4tr04e) | [35.82](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/yao85urg) | [16.48](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/env4g96b) | [10.70](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/wc3bjja7) |
| 300 | [30.79](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/bimk88py) | [19.35](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/8e6ifsow) | [50.15](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/x28itc2z) | [35.93](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/hv78bcsk) | [15.48](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/0ityqqc8) | [11.63](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/6jhk07qe) |

## E3: task-specific predictor on a training-sample probe

| Dataset | Method | Prequential ACE | Probe ACE (task mean) | Probe ACE (pooled) | Probe samples |
| --- | --- | --- | --- | --- | --- |
| syn1 | ITOL | [37.32](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/q1bz576v) | 33.53 | 33.52 | 4000 |
| syn1 | TOL | [23.62](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/k8ynvkij) | 20.07 | 20.08 | 4000 |
| syn1 | UnifSum | [49.93](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/j4atyc74) | 33.53 | 33.52 | 4000 |
| syn1 | TransOL | [37.10](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/sk61dk94) | 20.07 | 20.08 | 4000 |
| syn1 | OTB | [19.52](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/yjq64wya) | 14.30 | 14.30 | 4000 |
| syn1 | AKLO | [11.95](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/9qpdhign) | 33.53 | 33.52 | 4000 |
| syn2 | ITOL | [38.12](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/05t1famj) | 34.17 | 34.17 | 4000 |
| syn2 | TOL | [37.78](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/4ivq0785) | 32.65 | 32.65 | 4000 |
| syn2 | UnifSum | [51.38](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/u89juo8t) | 34.17 | 34.17 | 4000 |
| syn2 | TransOL | [44.05](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/s2jgivf1) | 32.65 | 32.65 | 4000 |
| syn2 | OTB | [37.53](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/nx3z8wgf) | 33.65 | 33.65 | 4000 |
| syn2 | AKLO | [10.32](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/aoabf2pd) | 34.17 | 34.17 | 4000 |
| landmine | ITOL | [38.39](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/wecrjww7) | 34.48 | 34.48 | 870 |
| landmine | TOL | [38.30](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/hkvz21f3) | 32.30 | 32.30 | 870 |
| landmine | UnifSum | [39.20](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/qcmg6w30) | 34.48 | 34.48 | 870 |
| landmine | TransOL | [38.21](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/9gshzzyk) | 32.30 | 32.30 | 870 |
| landmine | OTB | [33.95](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/hvhz6q35) | 28.51 | 28.51 | 870 |
| landmine | AKLO | [29.95](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/yje23s60) | 34.48 | 34.48 | 870 |
| spam | ITOL | [25.63](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/4stuhpdx) | 16.67 | 16.67 | 600 |
| spam | TOL | [20.47](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/49qi2om9) | 13.17 | 13.17 | 600 |
| spam | UnifSum | [24.70](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/qm7lwbc4) | 16.67 | 16.67 | 600 |
| spam | TransOL | [21.20](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/vz5yap4u) | 13.17 | 13.17 | 600 |
| spam | OTB | [17.50](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/e9spuf5n) | 10.67 | 10.67 | 600 |
| spam | AKLO | [19.50](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/8qkklxdn) | 16.67 | 16.67 | 600 |
| syn3 | ITOL | [7.94](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/pv92rwna) | 7.82 | 7.82 | 4000 |
| syn3 | TOL | [7.94](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/6vplir2p) | 8.45 | 8.45 | 4000 |
| syn3 | UnifSum | [1.60](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/2yu433zp) | 7.82 | 7.82 | 4000 |
| syn3 | TransOL | [5.35](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/kequ7wxx) | 8.45 | 8.45 | 4000 |
| syn3 | AKLO | [1.06](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/fdrsuy1l) | 7.82 | 7.82 | 4000 |
| syn4 | ITOL | [5.18](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/w4la5mwa) | 5.31 | 5.31 | 4000 |
| syn4 | TOL | [5.18](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/sfl4u8q4) | 5.65 | 5.65 | 4000 |
| syn4 | UnifSum | [1.40](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/0r1csbpi) | 5.31 | 5.31 | 4000 |
| syn4 | TransOL | [3.69](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/pu5e9vjm) | 5.65 | 5.65 | 4000 |
| syn4 | AKLO | [1.10](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/an1jzt1s) | 5.31 | 5.31 | 4000 |
| london | ITOL | [14.80](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/cfkiwjl9) | 12.70 | 12.41 | 3069 |
| london | TOL | [12.61](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/gcfiz324) | 12.04 | 12.04 | 3069 |
| london | UnifSum | [15.02](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/cr4zdqqi) | 12.70 | 12.41 | 3069 |
| london | TransOL | [13.19](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/o7zx2jq0) | 12.04 | 12.04 | 3069 |
| london | AKLO | [11.94](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/hlw4xa68) | 12.70 | 12.41 | 3069 |

### Paper vs reproduction

| Dataset | Method | Paper Table 2 | Our E3 probe |
| --- | --- | --- | --- |
| syn1 | ITOL | 36.36 | 33.53 |
| syn1 | TOL | 21.54 | 20.07 |
| syn1 | UnifSum | 49.96 | 33.53 |
| syn1 | TransOL | 35.99 | 20.07 |
| syn1 | OTB | 30.24 | 14.30 |
| syn1 | AKLO | 8.78 | 33.53 |
| syn2 | ITOL | 33.51 | 34.17 |
| syn2 | TOL | 33.65 | 32.65 |
| syn2 | UnifSum | 41.32 | 34.17 |
| syn2 | TransOL | 32.56 | 32.65 |
| syn2 | OTB | 35.06 | 33.65 |
| syn2 | AKLO | 8.34 | 34.17 |
| landmine | ITOL | 14.00 | 34.48 |
| landmine | TOL | 11.59 | 32.30 |
| landmine | UnifSum | 6.86 | 34.48 |
| landmine | TransOL | 8.08 | 32.30 |
| landmine | OTB | 11.09 | 28.51 |
| landmine | AKLO | 6.78 | 34.48 |
| spam | ITOL | 25.23 | 16.67 |
| spam | TOL | 17.13 | 13.17 |
| spam | UnifSum | 12.33 | 16.67 |
| spam | TransOL | 26.43 | 13.17 |
| spam | OTB | 23.17 | 10.67 |
| spam | AKLO | 9.97 | 16.67 |
| syn3 | ITOL | 14.53 | 7.82 |
| syn3 | TOL | 7.62 | 8.45 |
| syn3 | UnifSum | 27.60 | 7.82 |
| syn3 | TransOL | 61.54 | 8.45 |
| syn3 | AKLO | 3.58 | 7.82 |
| syn4 | ITOL | 8.05 | 5.31 |
| syn4 | TOL | 9.82 | 5.65 |
| syn4 | UnifSum | 51.36 | 5.31 |
| syn4 | TransOL | 54.57 | 5.65 |
| syn4 | AKLO | 2.34 | 5.31 |
| london | ITOL | 20.80 | 12.70 |
| london | TOL | 20.87 | 12.04 |
| london | UnifSum | 10.42 | 12.70 |
| london | TransOL | 79.58 | 12.04 |
| london | AKLO | 9.57 | 12.70 |

E3 follows the revised protocol: after training all tasks, 20% of each
task's training samples are drawn without replacement and fed to the
task-specific predictor saved at the end of that task. The probe ACE is
the task-averaged error on those samples. This is not the same protocol
as the paper's Table 2, which feeds a test set of previous tasks to the
final model; the comparison is therefore qualitative. See
`docs/experiment_protocol.md`.

Interpretation caveat: AKLO, ITOL and Unif_Sum share the same per-task
online update, so their frozen `f_t` and probe ACE coincide. E3 measures
how well each task's own predictor fits its training distribution, not
how much knowledge is retained across tasks; cross-task retention is
visible in the prequential ACE and in the E1 comparison.

## E4: classification sensitivity (paper Figure 4)

### eta

| eta | ACE (%) | W&B |
| --- | --- | --- |
| 0 | 54.34 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/0qljc1so) |
| 0.0001 | 36.59 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/xmgo3mlf) |
| 0.001 | 35.24 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/ubba0wm0) |
| 0.01 | 25.81 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/b5tdy54j) |
| 1 | 11.95 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/05wz330a) |
| 10 | 14.47 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/xfe4h1mn) |

### lambda

| lambda | ACE (%) | W&B |
| --- | --- | --- |
| 0 | 13.04 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/6wnfn1we) |
| 0.0001 | 12.90 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/0tea43mo) |
| 0.001 | 11.95 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/e11wu5nq) |
| 0.005 | 14.72 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/8d459fk9) |
| 0.01 | 14.56 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/lmkeq1e1) |
| 0.05 | 24.26 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/83zj3b3x) |
| 0.1 | 34.08 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/k0uu20ek) |

### delta_alpha

| delta_alpha | ACE (%) | W&B |
| --- | --- | --- |
| 0 | 6.80 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/ngcotm23) |
| 0.001 | 11.95 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/zbu2ro7r) |
| 0.005 | 24.94 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/3uf320d4) |
| 0.01 | 30.29 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/tg7hdhrh) |
| 1 | 37.34 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/akmzi67i) |

## E5: regression sensitivity (paper Figure 5)

### eta

| eta | ACE | W&B |
| --- | --- | --- |
| 0 | 1.11 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/iz0h9shf) |
| 0.0001 | 0.99 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/viwvzxke) |
| 0.0005 | 0.96 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/0rtbflyb) |
| 0.05 | 1.06 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/0l3zxwts) |
| 0.25 | 4.65 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/wpheyypk) |
| 0.5 | 19.71 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/urmcie4j) |

### lambda

| lambda | ACE | W&B |
| --- | --- | --- |
| 0 | 0.85 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/egwxjfgi) |
| 0.25 | 1.06 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/yf76xydl) |
| 0.625 | 1.27 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/sxehpu6j) |
| 0.75 | 1.27 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/57y2ntf6) |
| 0.875 | 1.32 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/xk9nu8md) |
| 1 | 1.35 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/h3b7z981) |

### delta_alpha

| delta_alpha | ACE | W&B |
| --- | --- | --- |
| 0 | 0.93 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/yv5bi7m4) |
| 0.001 | 1.06 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/chenszh2) |
| 0.005 | 2.31 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/djpyjqky) |
| 0.01 | 4.14 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/3dcjk1io) |
| 0.025 | 6.42 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/xw2i8j8m) |
| 1 | 7.95 | [run](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/1tr04ref) |

## E6: AKLOMS tau sensitivity (paper Table 3)

| tau | syn1 | syn2 | landmine | spam | syn3 | syn4 | london | Paper mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.001 | [11.84](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/bmdqiupp) | [10.32](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/18j02tzy) | [30.30](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/qun6aezh) | [19.60](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/fdunsged) | [1.11](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/9t46j5y6) | [1.13](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/ew34antk) | [11.94](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/swrw4mws) | 9.21 |
| 0.01 | [11.84](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/r0muqh73) | [10.33](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/kiq9kfmp) | [30.30](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/5jarf4vy) | [19.60](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/w8auyb2j) | [1.11](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/li0hlc62) | [1.13](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/7ft90hz0) | [11.95](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/9rj6seak) | 9.79 |
| 0.05 | [11.85](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/9o9eq7wu) | [10.35](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/9pn1t1tx) | [30.23](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/oyuh52sy) | [19.60](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/3tvd8wt2) | [1.12](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/fcfh3gl2) | [1.14](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/wf0cyy0o) | [11.97](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/ttr9y1lz) | 11.20 |
| 0.1 | [11.86](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/y6w731cy) | [10.39](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/67hiijbl) | [30.18](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/xn0agmnb) | [19.60](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/plh8ppjq) | [1.12](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/a7c89pup) | [1.15](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/kv81w93x) | [11.96](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/4103nnzv) | 12.62 |
| 0.5 | [11.95](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/oun1ion7) | [10.66](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/m6vduuj2) | [30.85](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/wzmsfi7r) | [19.60](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/jncja2h2) | [1.12](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/m6ukhpyd) | [1.15](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/aqalr3i5) | [11.95](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/mgdyj1ey) | 19.33 |
| 1 | [12.16](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/4xo9gul3) | [11.12](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/vy6e4vc5) | [30.87](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/9l2nedla) | [19.60](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/9r7nzgor) | [1.14](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/q56rw7ah) | [1.20](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/0oei6kg4) | [11.95](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/fa2b85oo) | 30.05 |
| 5 | [12.46](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/fyp10sd2) | [11.65](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/y49qsqsg) | [33.49](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/ymnzbxz5) | [19.63](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/eo2mkuwu) | [2.57](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/u7u3p725) | [3.06](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/xtj3zx41) | [14.47](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/t3tkob6t) | 31.19 |
| 10 | [12.61](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/j27u3bq4) | [11.73](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/4tmc7own) | [34.71](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/nhh8hs76) | [19.63](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/23w5rsqz) | [5.09](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/abrukegm) | [4.94](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/fu3mxou4) | [15.01](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/qd4kcbuk) | 31.03 |
| 100 | [23.13](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/zwfe2ymp) | [41.16](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/a07l7wn6) | [40.90](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/4t6ryifu) | [19.43](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/y4wd939k) | [6.47](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/c9tbsi1p) | [5.09](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/aezpkei2) | [15.01](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/sajrn92d) | 30.97 |

## E7: AKLOMS model selection (paper Figure 7)

| Tasks | tau=0 | tau=0.001 | tau=0.01 | tau=0.05 | tau=0.1 | tau=0.5 | tau=1 | tau=5 | tau=10 | tau=15 | tau=20 | tau=25 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 50 | 18.90 | 19.36 | 19.36 | 19.36 | 19.38 | 19.40 | 19.46 | 19.42 | 19.56 | 19.54 | 19.66 | 19.58 |
| 100 | 13.98 | 14.10 | 14.10 | 14.10 | 14.10 | 14.13 | 14.23 | 14.45 | 14.70 | 14.51 | 14.89 | 15.04 |
| 150 | 12.51 | 12.71 | 12.71 | 12.71 | 12.73 | 12.85 | 12.95 | 13.23 | 13.27 | 13.39 | 13.43 | 13.76 |
| 200 | 11.95 | 11.84 | 11.84 | 11.85 | 11.86 | 11.95 | 12.16 | 12.46 | 12.61 | 12.90 | 13.33 | 13.69 |
| 400 | 11.04 | 10.94 | 10.94 | 10.96 | 10.99 | 11.27 | 11.57 | 11.45 | 11.45 | 11.84 | 12.35 | 12.75 |

### Selected-model ratio (%)

| Tasks | tau=0 | tau=0.001 | tau=0.01 | tau=0.05 | tau=0.1 | tau=0.5 | tau=1 | tau=5 | tau=10 | tau=15 | tau=20 | tau=25 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 50 | 98.00 | 98.00 | 98.00 | 98.00 | 98.00 | 98.00 | 98.00 | 98.00 | 96.00 | 94.00 | 90.00 | 90.00 |
| 100 | 99.00 | 99.00 | 99.00 | 99.00 | 99.00 | 99.00 | 99.00 | 98.00 | 98.00 | 96.00 | 93.00 | 90.00 |
| 150 | 99.33 | 99.33 | 99.33 | 99.33 | 99.33 | 99.33 | 99.33 | 98.00 | 96.67 | 91.33 | 89.33 | 86.67 |
| 200 | 99.50 | 99.50 | 99.50 | 99.50 | 99.50 | 99.50 | 99.50 | 99.00 | 96.00 | 94.50 | 93.00 | 91.00 |
| 400 | 99.75 | 99.75 | 99.75 | 99.75 | 99.75 | 99.75 | 99.75 | 98.50 | 96.50 | 93.75 | 90.50 | 89.25 |

## E8: runtime scaling (paper Figure 8)

### AKLO runtime (seconds)

| Tasks \ m_t | 50 | 100 | 150 | 200 | 250 | 300 |
| --- | --- | --- | --- | --- | --- | --- |
| 100 | 0.131 | 0.252 | 2.482 | 3.608 | 4.231 | 4.292 |
| 200 | 1.761 | 3.187 | 4.575 | 6.224 | 5.858 | 6.472 |
| 300 | 1.487 | 3.461 | 1.253 | 1.551 | 9.302 | 14.679 |
| 400 | 3.300 | 4.913 | 7.315 | 9.983 | 10.969 | 13.155 |
| 500 | 2.761 | 5.691 | 8.459 | 12.686 | 13.655 | 16.449 |
| 600 | 3.786 | 7.497 | 10.948 | 13.848 | 16.519 | 20.635 |
| 700 | 4.163 | 8.419 | 12.929 | 16.430 | 19.925 | 24.467 |
| 800 | 4.904 | 9.672 | 13.857 | 16.619 | 22.910 | 28.474 |

### AKLOMS runtime (seconds)

| Tasks \ tau | 0 | 0.001 | 0.0025 | 0.005 | 0.01 | 0.025 | 0.05 | 10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 100 | 1.370 | 1.548 | 1.253 | 2.381 | 1.507 | 1.479 | 1.422 | 1.834 |
| 200 | 2.675 | 4.277 | 3.970 | 3.809 | 3.496 | 3.233 | 3.512 | 3.484 |
| 300 | 2.610 | 4.835 | 4.983 | 4.563 | 5.267 | 4.567 | 5.290 | 6.417 |
| 400 | 3.636 | 7.847 | 7.447 | 8.281 | 8.870 | 9.198 | 8.993 | 7.757 |
| 500 | 5.715 | 10.225 | 10.921 | 11.613 | 11.893 | 12.574 | 10.697 | 10.046 |
| 600 | 6.921 | 16.075 | 16.279 | 16.725 | 13.504 | 14.410 | 14.311 | 14.503 |

`train_seconds` covers only the per-sample predict/update loop; data
loading and W&B calls are excluded. The runs still share one Windows
machine, and background W&B uploads can perturb wall-clock timing, so
the absolute seconds are indicative and the scaling shape is the
reliable signal. The small-task-count cells are the noisiest; the
trend is clearest from 400 tasks upward.

At the tested `tau` values the AKLOMS cover stays close to the full
knowledge base (see E6/E7), so the AKLOMS table mainly measures the
cost of a near-full cover. The paper's negative `tau`/runtime trend
requires much larger `tau` in this implementation; `tau=0` is the
AKLO-equivalent special case.

## Theory checks

The empirical checks of Theorem 1, Corollary 1.1, and Corollary 1.2 are
diagnostics, not benchmark runs, and are not logged to W&B. The summary
and per-run reports are in [theory/README.md](theory/README.md).

## Figures

![e1_main.png](e1_main.png)

![e2_small_m.png](e2_small_m.png)

![e3_forgetting.png](e3_forgetting.png)

![e4_sensitivity_cls.png](e4_sensitivity_cls.png)

![e5_sensitivity_reg.png](e5_sensitivity_reg.png)

![e6_akloms_tau.png](e6_akloms_tau.png)

![e7_akloms_models.png](e7_akloms_models.png)

![e8_runtime.png](e8_runtime.png)
