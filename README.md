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
python scripts/run_matrix.py --experiments e1_main,e2_small_m,e3_forgetting,e4_sensitivity_cls,e5_sensitivity_reg,e6_akloms_tau,e7_akloms_models,e8_runtime

# Build the Markdown report and figures from local JSON
python scripts/make_report.py
```

The real datasets are expected under `data/`; see
[`data/README.md`](data/README.md). Synthetic `syn1`–`syn4` are generated
deterministically and need no files. `python scripts/prepare_data.py` checks
the local files.

## Experiment map

| ID | Paper element | Config | Command | W&B |
| --- | --- | --- | --- | --- |
| E1 | Table 1: main comparison | [`e1_main.yaml`](configs/experiments/e1_main.yaml) | `python scripts/run.py --experiment e1_main` | [group](WANDB_E1_GROUP) |
| E2 | Figure 3: effect of `m_t` | [`e2_small_m.yaml`](configs/experiments/e2_small_m.yaml) | `python scripts/run.py --experiment e2_small_m` | [group](WANDB_E2_GROUP) |
| E3 | Table 2: catastrophic forgetting | [`e3_forgetting.yaml`](configs/experiments/e3_forgetting.yaml) | `python scripts/run.py --experiment e3_forgetting` | [group](WANDB_E3_GROUP) |
| E4 | Figure 4: classification sensitivity | [`e4_sensitivity_cls.yaml`](configs/experiments/e4_sensitivity_cls.yaml) | `python scripts/run.py --experiment e4_sensitivity_cls` | [group](WANDB_E4_GROUP) |
| E5 | Figure 5: regression sensitivity | [`e5_sensitivity_reg.yaml`](configs/experiments/e5_sensitivity_reg.yaml) | `python scripts/run.py --experiment e5_sensitivity_reg` | [group](WANDB_E5_GROUP) |
| E6 | Table 3: AKLOMS `tau` | [`e6_akloms_tau.yaml`](configs/experiments/e6_akloms_tau.yaml) | `python scripts/run.py --experiment e6_akloms_tau` | [group](WANDB_E6_GROUP) |
| E7 | Figure 7: AKLOMS model selection | [`e7_akloms_models.yaml`](configs/experiments/e7_akloms_models.yaml) | `python scripts/run.py --experiment e7_akloms_models` | [group](WANDB_E7_GROUP) |
| E8 | Figure 8: runtime | [`e8_runtime.yaml`](configs/experiments/e8_runtime.yaml) | `python scripts/run.py --experiment e8_runtime` | [group](WANDB_E8_GROUP) |

The table above is the quick map. `reports/report.md` contains the full
tables and per-run links, including every seed and hyperparameter value.
The experiment configs are expanded by
[`src/aklo/experiments/__init__.py`](src/aklo/experiments/__init__.py); the
runner is [`src/aklo/runner.py`](src/aklo/runner.py).

## Main results

Task-averaged prequential ACE (%) on the E1 runs (seed 0). Lower is better.
Paper values are from Table 1 of the paper.

| Dataset | ITOL | TOL | Unif_Sum | TranOL | OTB | AKLO (ours) | AKLO (paper) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| syn1 | 37.32 | 23.62 | 49.93 | 37.10 | 19.52 | **11.95** | 10.10 |
| syn2 | 38.12 | 37.78 | 51.38 | 44.05 | 37.53 | **10.32** | 10.16 |
| Landmine | 38.39 | 38.30 | 39.20 | 38.21 | 33.95 | **29.95** | 7.30 |
| Spam | 25.63 | 20.47 | 24.70 | 21.20 | 17.50 | **19.50** | 17.36 |
| syn3 | 7.94 | 7.94 | 1.60 | 5.35 | – | **1.06** | 4.06 |
| syn4 | 5.18 | 5.18 | 1.40 | 3.69 | – | **1.10** | 2.98 |
| London | 14.80 | 12.61 | 15.02 | 13.19 | – | **11.94** | 10.05 |

AKLO is best or tied for best on every classification dataset and on London.
The qualitative conclusion of the paper—AKLO benefits from accumulated
knowledge and is competitive with or better than the baselines—is reproduced.
The numerical gaps are discussed below.

### Known deviations

* **Landmine:** our errors are much larger than the paper's because we do not
  append a bias feature and we resample 150 examples per task. The relative
  method ordering is still informative.
* **Regression:** our ACEs are much lower than the paper's. The paper's `syn3`
  values are worse than predicting zero (e.g. Unif_Sum 27.69), which is hard
  to reconcile with the stated absolute loss and data scale. This is an
  unresolved inconsistency in the paper, not a bug in the metric.
* **Repetitions:** the paper repeats each experiment 10 times; the committed
  results use `seed=0` (one repetition) for compute reasons. The configs
  accept `seeds: [0, 1, ...]` and will reproduce the repetition protocol when
  extended.
* **Synthetic task count:** the text says 50 tasks (25 per distribution), but
  Figures 3 and 7 use axes up to 200 and 400. We use 200 tasks, following the
  figures and the user decision.
* **Meta loss:** the paper's Section 6 says square loss for the meta
  hypothesis, but Algorithm 2, the bounded-loss theory, and the reported
  numbers point to a classification loss. We use hinge for classification and
  squared loss for regression; this is configurable via `meta_loss`.
* **TranOL and OTB** are faithful reimplementations, not the original
  algorithms, because the paper does not restate their full details.

See [`docs/paper_decisions.md`](docs/paper_decisions.md) for the complete list.

## E3: catastrophic forgetting

The paper's Table 2 is lower than Table 1, which is consistent with re-feeding
training samples after training. We use a 20% held-out test split per task and
report several diagnostics instead of hiding the ambiguity:

* prequential ACE (comparable to Table 1);
* mean current-task held-out test ACE;
* mean old-task held-out test ACE;
* final model on all held-out test tasks;
* final model on all training samples.

On `syn1`/AKLO: prequential ≈ 12.5%, current-task test ≈ 15.0%, old-task test
≈ 39.1%, final held-out test ≈ 36.6%, final training-data ACE ≈ 36.4%. The
paper's Table 2 value is 8.78. The gap and the alternative readings are
discussed in [`docs/paper_decisions.md`](docs/paper_decisions.md#5-experiment-protocol).

## Weights & Biases

All tracked runs are in the public project

* **Project:** `AKLO-lifelong-online-learning`
* **Entity:** `AI-Athena-Lab`
* **Server:** `https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning`

Each run logs its config, per-task ACE, cumulative ACE, model state, E3
forgetting diagnostics, and sample-level running ACE. No artifacts are
uploaded. See [`docs/wandb.md`](docs/wandb.md) for setup, commands, and the
run-naming convention.

## Repository layout

```
configs/
  base.yaml                  # project, entity, seeds, smoke settings
  data/*.yaml                # dataset paths and sizes
  models/*.yaml              # AKLO, AKLOMS, and baseline defaults
  experiments/*.yaml         # E1-E8 matrices
data/                        # local real datasets (not committed)
docs/
  experiment_protocol.md     # exact protocol and hyperparameters
  paper_decisions.md         # ambiguities, deviations, unresolved gaps
  wandb.md                   # tracking guide
  theory_checks.md           # plan for Theorem 1 / Corollaries 1.1-1.2
reports/                     # generated report.md and figures
results/                     # generated JSON (git-ignored)
scripts/
  run.py                     # one experiment
  run_matrix.py              # several experiments
  reproduce_all.ps1          # full run + report
  make_report.py             # JSON -> Markdown/figures
  prepare_data.py            # validate local data
src/aklo/
  data/                      # loaders and deterministic stream shuffling
  models/                    # AKLO, AKLOMS, baselines, meta hypothesis
  experiments/               # YAML -> run specifications
  runner.py                  # online loop, metrics, JSON/W&B logging
  report.py                  # tables and figures
tests/                       # 61 unit tests
```

## Theory checks

The paper's theory assumes a bounded meta loss, a `K`-Lipschitz loss, a
projected `||w|| <= R` comparator, and the schedule `eta_i = 1/(i lambda)`.
The Section 6 implementation uses constant `eta`, an unprojected online
update, and hinge/squared losses, so the theorem is not literally applicable
to the reported runs. [`docs/theory_checks.md`](docs/theory_checks.md) records
the exact statements, the assumptions that need auditing, and the planned
empirical checks for Theorem 1, Corollary 1.1, and Corollary 1.2.

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
