# Lifelong Online Learning from Accumulated Knowledge

> Repo này được tạo ra với mục đích tái lập và kiểm chứng những vấn đề lý thuyết được nêu trong bài báo [Lifelong Online Learning from Accumulated Knowledge](https://dl.acm.org/doi/10.1145/3563947), thuộc phạm vi môn học Nhập môn Học máy, trường Đại học Khoa học Tự nhiên, đại học Quốc gia TP.HCM, học kỳ HK1/26-27.
> Repo này được xây dựng bởi nhóm 11 - 24TNT1, bao gồm:
> - 24122010 - Đỗ Lê Phong Phú
> - 24122034 - Lê Huy Hoàng

This repository reproduces the Section 6 experiments of the paper
**“Lifelong Online Learning from Accumulated Knowledge”** (Shui et al.,
ACM TKDD 2023) with a small, readable Python implementation. It implements
AKLO (Algorithms 1–2), AKLOMS (Algorithm 3), and the five baselines used in
the paper: ITOL, TOL, Unif_Sum, TranOL, and OTB.

The goal is **pipeline correctness**, not digit-for-digit reproduction of
every table. All approximations and deviations are documented in
[`docs/paper_decisions.md`](docs/paper_decisions.md), and the exact protocol is
in [`docs/experiment_protocol.md`](docs/experiment_protocol.md).

## Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Optional W&B credentials
cp .env.example .env

# Smoke test (2 tasks x 5 samples, no W&B)
python scripts/run.py --experiment e1_main --smoke --no-wandb --limit 2

# Unit tests
python -m pytest -q

# Full matrix with W&B tracking
python scripts/run_matrix.py --experiments e1_main,e2_small_m,e3_catastrophic-forgetting,e4_sensitivity_cls,e5_sensitivity_reg,e6_akloms_tau,e7_akloms_models,e8_runtime

# Build the Markdown report and figures from local JSON
python scripts/make_report.py
```

The real datasets are downloaded from the public Kaggle dataset
[`wyuquane/aklo-real-world-dataset`](https://www.kaggle.com/datasets/wyuquane/aklo-real-world-dataset)
(MIT licence, version 1, no Kaggle account required):

```bash
# Download and copy the files into data/
python scripts/prepare_data.py --download

# Validate sizes and SHA-256 checksums
python scripts/prepare_data.py --check
```

The destination layout and checksums are recorded in
[`data/manifest.json`](data/manifest.json); see
[`data/README.md`](data/README.md) for provenance and preprocessing. Synthetic
`syn1`–`syn4` are generated deterministically and need no files.

## Experiment map

| ID | Paper element | Script / config | W&B (seed-0 run) | One-line finding |
| --- | --- | --- | --- | --- |
| E1 | Table 1: main comparison | `python scripts/run.py --experiment e1_main` · [`e1_main.yaml`](configs/experiments/e1_main.yaml) (39 groups) | [e1_main-landmine-aklo-s0](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/7m870p3k) | AKLO is best on 6/7 datasets; Spam is the exception (OTB 18.34 vs AKLO 20.93). |
| E2 | Figure 3: effect of `m_t` | `python scripts/run.py --experiment e2_small_m` · [`e2_small_m.yaml`](configs/experiments/e2_small_m.yaml) (48 groups) | [e2_small_m-syn1-aklo-m10-s0](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/cc6hi5c1) | On syn1/AKLO, ACE falls from 24.27% at `m_t=10` to 11.20% at `m_t=300`. |
| E3 | Table 2: catastrophic forgetting (per-task snapshots, 10 seeds) | `python scripts/run.py --experiment e3_catastrophic-forgetting` · [`e3_catastrophic-forgetting.yaml`](configs/experiments/e3_catastrophic-forgetting.yaml) (39 groups) | [e3_catastrophic-forgetting-landmine-aklo-s0](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/aky014a7) | Per-task snapshots close most of the gap; AKLO is best on syn2/syn3/syn4/London, OTB on syn1/Landmine/Spam. |
| E4 | Figure 4: classification sensitivity | `python scripts/run.py --experiment e4_sensitivity_cls` · [`e4_sensitivity_cls.yaml`](configs/experiments/e4_sensitivity_cls.yaml) (18 groups) | [e4_sensitivity_cls-syn1-aklo-delta_alpha-0-s0](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/sl2g0j3t) | `delta_alpha=0` gives the lowest ACE (6.65%); `eta=0` is worst (54.34%). |
| E5 | Figure 5: regression sensitivity | `python scripts/run.py --experiment e5_sensitivity_reg` · [`e5_sensitivity_reg.yaml`](configs/experiments/e5_sensitivity_reg.yaml) (18 groups) | [e5_sensitivity_reg-syn3-aklo-delta_alpha-0-s0](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/8cnrsfs1) | Differences are small; `lambda=0` is best (0.76) and the default `eta=0.05` gives 0.96. |
| E6 | Table 3: AKLOMS `tau` | `python scripts/run.py --experiment e6_akloms_tau` · [`e6_akloms_tau.yaml`](configs/experiments/e6_akloms_tau.yaml) (63 groups) | [e6_akloms_tau-landmine-akloms-tau0.001-s0](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/lszloy2z) | `tau <= 0.1` matches AKLO; on syn1 `tau=100` raises ACE from 12.28% to 24.48%. |
| E7 | Figure 7: AKLOMS model selection | `python scripts/run.py --experiment e7_akloms_models` · [`e7_akloms_models.yaml`](configs/experiments/e7_akloms_models.yaml) (60 groups) | [e7_akloms_models-syn1-akloms-T100-tau0-s0](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/hi8v1c88) | The selected-model ratio stays at 97–99.8% for `tau <= 1`; ACE rises mildly with `tau`. |
| E8 | Figure 8: runtime | `python scripts/run.py --experiment e8_runtime` · [`e8_runtime.yaml`](configs/experiments/e8_runtime.yaml) (96 groups) | [e8_runtime-syn1-aklo-aklo-T100-m100-s0](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs/frz5uixj) | Runtime grows with `m_t` and task count; `tau > 0` adds cover-check overhead, so the AKLOMS curves nearly coincide. |

The table above is the quick map. `reports/report.md` contains the full
tables; each number links to the W&B group holding all ten seeds of that
configuration. Every run also has an `experiment-<name>` tag, so the runs
table can be filtered to one experiment even though the `group` field is
reserved for configurations. The experiment configs are expanded by
[`src/aklo/experiments/__init__.py`](src/aklo/experiments/__init__.py); the
runner is [`src/aklo/runner.py`](src/aklo/runner.py). The seed-0 links above
are representative runs; the group link on each report cell opens all ten
seeds.

## Main results

Task-averaged prequential ACE (%) on the E1 runs, mean ± standard deviation
over seeds 0–9. Lower is better. Paper values are from Table 1 of the paper.

| Dataset | ITOL | TOL | Unif_Sum | TranOL | OTB | AKLO (ours) | AKLO (paper) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| syn1 | [37.05 ± 0.47](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-syn1-itol) | [23.86 ± 0.35](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-syn1-tol) | [49.65 ± 0.73](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-syn1-unif_sum) | [36.71 ± 1.67](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-syn1-tranol) | [19.84 ± 0.66](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-syn1-otb) | **[12.29 ± 0.83](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-syn1-aklo)** | 10.10 |
| syn2 | [38.17 ± 0.51](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-syn2-itol) | [37.82 ± 0.63](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-syn2-tol) | [50.36 ± 0.83](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-syn2-unif_sum) | [43.11 ± 1.04](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-syn2-tranol) | [37.79 ± 0.61](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-syn2-otb) | **[10.72 ± 0.78](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-syn2-aklo)** | 10.16 |
| Landmine | [39.35 ± 0.85](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-landmine-itol) | [38.93 ± 1.49](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-landmine-tol) | [51.97 ± 8.85](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-landmine-unif_sum) | [41.03 ± 2.90](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-landmine-tranol) | [33.71 ± 1.73](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-landmine-otb) | **[30.96 ± 1.36](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-landmine-aklo)** | 7.30 |
| Spam | [25.76 ± 0.90](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-spam-itol) | [20.37 ± 0.80](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-spam-tol) | [24.51 ± 3.85](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-spam-unif_sum) | [20.94 ± 1.77](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-spam-tranol) | **[18.34 ± 0.64](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-spam-otb)** | [20.93 ± 1.61](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-spam-aklo) | 17.36 |
| syn3 | [7.94 ± 0.01](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-syn3-itol) | [7.93 ± 0.01](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-syn3-tol) | [1.52 ± 0.11](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-syn3-unif_sum) | [5.17 ± 0.10](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-syn3-tranol) | – | **[0.96 ± 0.10](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-syn3-aklo)** | 4.06 |
| syn4 | [5.17 ± 0.01](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-syn4-itol) | [5.18 ± 0.01](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-syn4-tol) | [1.39 ± 0.09](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-syn4-unif_sum) | [3.61 ± 0.06](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-syn4-tranol) | – | **[1.00 ± 0.10](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-syn4-aklo)** | 2.98 |
| London | [14.81 ± 0.01](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-london-itol) | [12.60 ± 0.03](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-london-tol) | [14.89 ± 0.10](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-london-unif_sum) | [13.21 ± 0.06](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-london-tranol) | – | **[11.77 ± 0.09](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main-london-aklo)** | 10.05 |

AKLO is the best method on six of the seven datasets. The exception is Spam,
where OTB is better (18.34 vs 20.93). The qualitative conclusion of
the paper—AKLO benefits from accumulated knowledge and is competitive with or
better than the baselines—is reproduced. The numerical gaps are discussed
below. The corresponding per-task ACE evolution is reproduced as **Figure 2**
in [`reports/report.md`](reports/report.md): four classification panels
(`syn1`, `syn2`, Landmine, Spam) and three regression panels (`syn3`, `syn4`,
London), each curve averaged over the ten seeds of the E1 runs.

### Known deviations

* **Landmine:** our errors are much larger than the paper's because we do not
  append a bias feature and we sample 150 examples per task. The relative
  method ordering is still informative.
* **Regression:** our ACEs are much lower than the paper's. The paper's `syn3`
  values are worse than predicting zero (e.g. Unif_Sum 27.69), which is hard
  to reconcile with the stated absolute loss and data scale. This is an
  unresolved inconsistency in the paper, not a bug in the metric.
* **Repetitions:** the paper repeats each experiment 10 times. All experiments
  use seeds `0..9` and report mean ± standard deviation. The data and split are
  fixed by `data_seed=0`; only the task and example order changes, matching the
  paper's repetition description.
* **Synthetic task count:** E3 follows the text's 50 tasks (25 per
  distribution). E1/E2 use 200 tasks, while E7 sweeps 50–400 tasks because
  Figure 7 has axes up to 400; this is a deliberate split between the
  Table 1/Table 2 protocol and the scaling figures.
* **Meta loss:** the paper's Section 6 says square loss for the meta
  hypothesis, but Algorithm 2, the bounded-loss theory, and the reported
  numbers point to a classification loss. We use hinge for classification and
  squared loss for regression; this is configurable via `meta_loss`.
* **AKLOMS cover size:** the cover test uses raw prediction differences, so
  its effective scale depends on the dataset and weight norm. On `syn1`/`syn2`
  and the E7 streams the cover stays at 97–99.8% for `tau <= 1` and 83–88% at
  `tau=25`; on London, `syn3` and `syn4` it is already smaller at `tau=1`, and
  `tau=100` drops it to 0.5–50% on most datasets (Spam stays at 93%). The
  paper's Figure 7 reports much smaller model ratios, but does not give the
  `tau` values behind panel (b), so the absolute `tau` axis is not directly
  comparable. The qualitative trade-off (larger `tau` → smaller cover, higher
  ACE) is reproduced.
* **Runtime:** E8 measures `train_seconds` for every seed on a shared Windows
  laptop; the table reports the mean ± standard deviation over the ten seeds.
  The timer excludes data loading and W&B calls, but background uploads can
  still perturb wall-clock timing. The scaling shape is more reliable than the
  absolute seconds. The AKLOMS cover check uses an exact nearest-cover binary
  search, so E8(b) reflects prediction cost rather than a naive pairwise
  distance matrix; E8 was rerun after this change. At the tested `tau` values
  the cover still contains 92–99.8% of the knowledge base, so the `tau > 0`
  curves nearly coincide and sit slightly above `tau=0`, which skips the
  per-sample cover check. The absolute times are much smaller than the paper's
  because of the vectorized implementation and the narrower timing scope.
* **TranOL and OTB** are faithful reimplementations, not the original
  algorithms, because the paper does not restate their full details.

See [`docs/paper_decisions.md`](docs/paper_decisions.md) for the complete list.

## E3: catastrophic forgetting (paper Table 2)

E3 trains once on the whole stream and evaluates each task's test set with a
method-specific predictor. The synthetic datasets use 50 tasks (25 D1 + 25 D2),
100 training samples and 100 separate test samples per task. Landmine uses 150
training rows per task and every remaining row as test; Spam uses 200 training
rows per user and every remaining row as test. London keeps an 80/20 split per
school. The experiment is repeated with seeds `0..9`; the data and split are
fixed by `data_seed=0`, and only the task/example order changes, matching the
paper's repetition description. The matrix contains 390 runs (39
method/dataset combinations per seed).

The predictor for task q is method-specific:

* **ITOL** uses the task-specific snapshot `f_q`.
* **TOL** uses the single final online model.
* **Unif_Sum** averages all task snapshots `f_1..f_T`.
* **TranOL** uses the frozen source/target pair at the end of task q
  (`f_{q-1}` + `f_q`, 0.5/0.5; the first task uses the target only).
* **OTB** uses the frozen weighted ensemble of 10 weak learners and the
  boosting weights at the end of task q.
* **AKLO** uses the frozen snapshot at the end of task q: the knowledge base
  `f_1..f_{q-1}` used during the task, the meta weights `beta` at the end of
  the task, the current predictor `f_q`, and `alpha` at the end of the task.
  The first task uses `f_1` only.

The snapshots are immutable: prediction never calls `update`, so no parameter
changes during the test pass. The primary metric is the task-averaged test ACE
(`final_test_ace_task_mean`), with pooled test ACE (`final_test_ace_pooled`) as
secondary. Classification ACE is multiplied by 100; regression ACE is on the
target scale. OTB is undefined for regression. The old per-task E3 protocol
and its `e3_task_test` W&B runs were removed. The current runs are grouped by
configuration (`e3_catastrophic-forgetting-*`) and tagged
`experiment-e3_catastrophic-forgetting`; use the
[project runs table](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/runs)
to filter them.

Task-averaged test ACE (%), mean ± standard deviation over seeds 0–9. Lower is
better; the best method per dataset is bold. The last column is the paper's
Table 2 AKLO value.

| Dataset | ITOL | TOL | Unif_Sum | TranOL | OTB | AKLO (ours) | AKLO (paper) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| syn1 | [35.87 ± 2.50](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-syn1-itol) | [38.32 ± 10.02](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-syn1-tol) | [50.01 ± 0.20](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-syn1-unif_sum) | [37.07 ± 1.90](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-syn1-tranol) | **[18.37 ± 1.76](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-syn1-otb)** | [19.61 ± 2.93](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-syn1-aklo) | 8.78 |
| syn2 | [33.91 ± 1.89](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-syn2-itol) | [49.87 ± 0.60](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-syn2-tol) | [49.90 ± 0.49](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-syn2-unif_sum) | [42.22 ± 1.86](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-syn2-tranol) | [35.47 ± 1.25](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-syn2-otb) | **[16.50 ± 2.79](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-syn2-aklo)** | 8.34 |
| Landmine | [37.95 ± 1.43](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-landmine-itol) | [46.79 ± 13.53](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-landmine-tol) | [55.44 ± 2.09](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-landmine-unif_sum) | [40.07 ± 2.61](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-landmine-tranol) | **[33.06 ± 1.86](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-landmine-otb)** | [33.25 ± 1.27](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-landmine-aklo) | 6.78 |
| Spam | [20.00 ± 1.75](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-spam-itol) | [22.93 ± 7.81](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-spam-tol) | [20.81 ± 4.85](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-spam-unif_sum) | [18.82 ± 1.70](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-spam-tranol) | **[15.59 ± 1.63](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-spam-otb)** | [19.67 ± 2.70](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-spam-aklo) | 9.97 |
| syn3 | [6.90 ± 0.66](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-syn3-itol) | [6.76 ± 4.16](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-syn3-tol) | [1.77 ± 0.56](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-syn3-unif_sum) | [5.39 ± 0.72](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-syn3-tranol) | – | **[1.40 ± 0.31](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-syn3-aklo)** | 3.58 |
| syn4 | [4.83 ± 0.36](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-syn4-itol) | [4.28 ± 2.99](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-syn4-tol) | [1.29 ± 0.15](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-syn4-unif_sum) | [3.49 ± 0.36](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-syn4-tranol) | – | **[1.28 ± 0.23](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-syn4-aklo)** | 2.34 |
| London | [12.77 ± 0.03](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-london-itol) | [13.86 ± 0.95](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-london-tol) | [14.75 ± 0.03](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-london-unif_sum) | [12.65 ± 0.07](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-london-tranol) | – | **[11.63 ± 0.08](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting-london-aklo)** | 9.57 |

E3 is a hybrid protocol: ITOL, AKLO, TranOL and OTB use per-task snapshots,
while TOL and Unif_Sum use stricter global predictors. Under it AKLO is best on
four of seven datasets (syn2, syn3, syn4, London); OTB wins syn1, Landmine and
Spam. The gap to the paper remains largest for AKLO (e.g. syn1 19.61 vs 8.78),
but the per-task snapshots close most of the previous gap. The comparison with
the paper is qualitative because the paper's Table 2 values are close to its
Table 1 values.

Two properties are worth stating explicitly:

* **TOL is the strictest predictor.** It applies the single final online model
  to every task, so its rows show the full catastrophic forgetting of a shared
  predictor. Unif_Sum averages all snapshots and is also global.
* **syn2 is adversarial.** Its D2 tasks reuse the D1 marginal but flip the
  labels, so a single global linear predictor cannot fit both distributions;
  TOL and Unif_Sum sit near chance. The per-task methods retain task-specific
  models and are therefore much lower.

See [`docs/experiment_protocol.md`](docs/experiment_protocol.md) and
[`docs/paper_decisions.md`](docs/paper_decisions.md#e3-method-specific-catastrophic-forgetting-protocol).

## Other experiments

**E2 (`m_t`).** On `syn1`/AKLO, mean ACE falls from 24.27% at `m_t=10` to
11.20% at `m_t=300` (20.21% at 20, 14.91% at 40, 13.04% at 80, 11.99% at 160,
11.48% at 200, 11.24% at 250). More per-task samples help, matching Figure 3's
qualitative trend; the eight panels match the paper's eight `m_t` values, and
each point is the mean over 10 seeds.

**E4/E5 (hyperparameter sensitivity).** The exact grids from the paper's
figure legends are used. For classification (`syn1`), the default
`eta=1`, `lambda=0.001`, `delta_alpha=0.001` gives 12.29%; `eta=10` gives
17.18% and `eta=0` gives 54.34%, while `delta_alpha=0` gives the lowest ACE
(6.65%) because the meta-hypothesis keeps full weight. For regression
(`syn3`), `eta=0.0005` and the default `eta=0.05` both give 0.96,
`lambda=0` gives 0.76, and `delta_alpha=0` gives 0.83. The figures mirror
paper Figures 4/5: three panels of cumulative ACE against task index, one
line per parameter value, with each curve averaged over 10 seeds. Full tables
are in `reports/report.md`.

**E6 (`tau`).** Small `tau` (≤0.1) is indistinguishable from AKLO. ACE then
rises with `tau`: on `syn1`, 12.28% at `tau=0.001`, 12.66% at 1, 12.85% at 10,
and 24.48% at 100; on `syn2`, 10.76% at the default and 40.53% at `tau=100`.
This is the expected accuracy/compression trade-off, but the useful `tau` range
is much larger than the paper's. Each cell is the mean over 10 seeds.

**E7 (task count).** The same pattern holds for 50–400 tasks: the mean
selected-model ratio is 97–99.8% for `tau <= 1`, 83–88% at `tau=25`, and ACE
increases mildly with `tau` (e.g. 15.72% → 17.14% at 50 tasks). Panel (b)
zooms the model-ratio axis to 0.8–1.0 so this high-ratio region is readable.
The reproduction never reaches the small ratios shown in the paper's
Figure 7(b); see the `tau` deviation above.

## Weights & Biases

All tracked runs are in the public project

* **Project:** `AKLO-lifelong-online-learning`
* **Entity:** `AI-Athena-Lab`
* **Server:** `https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning`

Each run logs its config, per-task ACE, cumulative ACE, model state, E3
per-task diagnostics, the E3 test metrics, and sample-level running ACE. No
artifacts are uploaded. Runs that differ only by seed share one group named
after the configuration (`e1_main-syn1-aklo`, ...); the experiment is kept as
an `experiment-<name>` tag because W&B has no nested groups.
See
[`docs/wandb.md`](docs/wandb.md) for setup, commands, and the run-naming
convention.

## Repository layout

```
configs/
  base.yaml                  # project, entity, seeds, smoke settings
  data/*.yaml                # dataset paths and sizes
  models/*.yaml              # AKLO, AKLOMS, and baseline defaults
  experiments/*.yaml         # E1-E8 matrices
data/                        # local real datasets (not committed) + manifest.json
docs/
  experiment_protocol.md     # exact protocol and hyperparameters
  paper_decisions.md         # ambiguities, deviations, unresolved gaps
  wandb.md                   # tracking guide
  theory_checks.md           # Theorem 1 / Corollaries 1.1-1.2 checks
reports/                     # generated report.md, figures, theory checks
results/                     # generated JSON (git-ignored)
scripts/
  run.py                     # one experiment
  run_matrix.py              # several experiments
  reproduce_all.ps1          # full run + report
  make_report.py             # JSON -> Markdown/figures
  check_theory.py            # Theorem 1 / Corollary diagnostics
  run_theory_checks.ps1      # reproducible theory-check matrix
  prepare_data.py            # Kaggle download + checksum validation
  check_docstrings.py        # docstring coverage check
src/aklo/
  data/                      # loaders and deterministic stream shuffling
  models/                    # AKLO, AKLOMS, baselines, meta hypothesis
  experiments/               # YAML -> run specifications
  runner.py                  # online loop, metrics, JSON/W&B logging
  report.py                  # tables and figures
  theory.py                  # theory instrumentation and analysis
tests/                       # 97 unit tests
```

## Theory checks

The paper's theory assumes a bounded meta loss, a `K`-Lipschitz loss, a
projected `||w|| <= R` comparator, and the schedule `eta_i = 1/(i lambda)`.
The Section 6 implementation uses constant `eta`, an unprojected online
update, and hinge/squared losses, so the theorem is not literally applicable
to the reported runs. [`docs/theory_checks.md`](docs/theory_checks.md) records
the exact statements and the assumption audit; the instrumented checks live in
[`src/aklo/theory.py`](src/aklo/theory.py) and are summarized in
[`reports/theory/README.md`](reports/theory/README.md).

Headline findings from 50-task diagnostic runs (not logged to W&B):

* **Theorem 1:** the PDF's displayed radical is inconsistent with the proof
  and with both stated special cases. The proof reading covers 100% of `syn1`
  tasks and 93.9% of `syn3` tasks; the displayed reading covers 0% and 10.2%.
  With `delta_alpha=0.0001` on `syn1`, the proof bound covers only 36.7%,
  exposing the constant-`eta` mismatch.
* **Corollary 1.1:** the small-interaction condition is not reachable at
  `m_t=100` in any run; the required `N` forces `alpha` to stay above ~0.99
  for all 100 steps. On `syn3`, the condition comes closer (`i_0=74`), so it
  may hold for smaller `m_t`.
* **Corollary 1.2:** the cover is nearly the full knowledge base for
  `tau <= 1` and still 45/49 models at `tau=10`. The bound is 5.6–10.8× the
  empirical error and looser than Theorem 1 even at `tau=0`.

Reproduce with:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_theory_checks.ps1
```

## Reproduction guide

The repository follows the course reproduction guide:
<https://hcmus-cs-ta.github.io/lab-book/intro-ml/project/statement/reproduction/>.

Suggested reading order:

1. [`docs/experiment_protocol.md`](docs/experiment_protocol.md) — what each
   experiment does and how to run it.
2. [`docs/paper_decisions.md`](docs/paper_decisions.md) — what we changed and
   why.
3. [`reports/report.md`](reports/report.md) — generated tables, figures, and
   run links.

## Data, code, and reuse

This repository is an independent course reproduction. **No source code from
the paper's authors or from another AKLO/AKLOMS implementation was copied,
vendored, or adapted.** The method code under `src/aklo/` was written for this
repository from the published algorithm descriptions (Algorithms 1–3) and the
experiment protocol; the paper's pseudocode is used as a specification, not as
executable code. The five baselines are likewise our own implementations.
TranOL and OTB are faithful approximations because the paper does not restate
their full details.

The only third-party code used is the following open-source libraries:

| Library | Use | Licence |
| --- | --- | --- |
| [NumPy](https://numpy.org/) | Arrays and linear algebra | BSD-3-Clause |
| [SciPy](https://scipy.org/) | Sparse matrices and linear programming | BSD-3-Clause |
| [scikit-learn](https://scikit-learn.org/) | Train/test splitting | BSD-3-Clause |
| [pandas](https://pandas.pydata.org/) | Landmine CSV loading | BSD-3-Clause |
| [PyYAML](https://pyyaml.org/) | Experiment configuration | MIT |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | `.env` credentials | BSD-3-Clause |
| [Weights & Biases](https://wandb.ai/) | Experiment tracking | MIT |
| [Matplotlib](https://matplotlib.org/) | Report figures | PSF-based |
| [tqdm](https://tqdm.github.io/) | Progress reporting | MPL-2.0 / MIT |
| [kagglehub](https://github.com/Kaggle/kagglehub) | Public dataset download | Apache-2.0 |
| [pytest](https://pytest.org/) | Unit tests | MIT |

Data sources:

* **Real datasets:** [`wyuquane/aklo-real-world-dataset`](https://www.kaggle.com/datasets/wyuquane/aklo-real-world-dataset)
  on Kaggle (MIT licence, version 1). `scripts/prepare_data.py` downloads it
  without credentials and verifies the files against
  [`data/manifest.json`](data/manifest.json). The original Landmine, Spam, and
  London School sources are described in [`data/README.md`](data/README.md).
* **Synthetic datasets:** `syn1`–`syn4` are generated by
  [`src/aklo/data/synthetic.py`](src/aklo/data/synthetic.py); no external data
  is used.
* **Paper:** Shui et al., *Lifelong Online Learning from Accumulated
  Knowledge*, ACM TKDD 17(4), 2023 (DOI
  [10.1145/3563947](https://doi.org/10.1145/3563947)). The paper is cited as
  the source of the algorithms and protocol; its text and figures are not
  redistributed.

All tables and figures in [`reports/`](reports/) are generated by our code from
our own JSON results. No external table or figure asset is reused.

## Citation

```bibtex
@article{shui2023lifelong,
  title   = {Lifelong Online Learning from Accumulated Knowledge},
  author  = {Shui, Changjian and others},
  journal = {ACM Transactions on Knowledge Discovery from Data},
  volume  = {17},
  number  = {4},
  pages   = {52:1--52:25},
  year    = {2023},
  doi     = {10.1145/3563947}
}
```
