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
| E1 | Table 1: main comparison | [`e1_main.yaml`](configs/experiments/e1_main.yaml) | `python scripts/run.py --experiment e1_main` | [group](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main) |
| E2 | Figure 3: effect of `m_t` | [`e2_small_m.yaml`](configs/experiments/e2_small_m.yaml) | `python scripts/run.py --experiment e2_small_m` | [group](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e2_small_m) |
| E3 | Table 2: task-specific training-sample probe | [`e3_forgetting.yaml`](configs/experiments/e3_forgetting.yaml) | `python scripts/run.py --experiment e3_forgetting` | [group](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_forgetting) |
| E4 | Figure 4: classification sensitivity | [`e4_sensitivity_cls.yaml`](configs/experiments/e4_sensitivity_cls.yaml) | `python scripts/run.py --experiment e4_sensitivity_cls` | [group](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e4_sensitivity_cls) |
| E5 | Figure 5: regression sensitivity | [`e5_sensitivity_reg.yaml`](configs/experiments/e5_sensitivity_reg.yaml) | `python scripts/run.py --experiment e5_sensitivity_reg` | [group](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e5_sensitivity_reg) |
| E6 | Table 3: AKLOMS `tau` | [`e6_akloms_tau.yaml`](configs/experiments/e6_akloms_tau.yaml) | `python scripts/run.py --experiment e6_akloms_tau` | [group](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e6_akloms_tau) |
| E7 | Figure 7: AKLOMS model selection | [`e7_akloms_models.yaml`](configs/experiments/e7_akloms_models.yaml) | `python scripts/run.py --experiment e7_akloms_models` | [group](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e7_akloms_models) |
| E8 | Figure 8: runtime | [`e8_runtime.yaml`](configs/experiments/e8_runtime.yaml) | `python scripts/run.py --experiment e8_runtime` | [group](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e8_runtime) |

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

AKLO is the best method on six of the seven datasets. The exception is Spam,
where OTB is slightly better (17.50 vs 19.50). The qualitative conclusion of
the paper—AKLO benefits from accumulated knowledge and is competitive with or
better than the baselines—is reproduced. The numerical gaps are discussed
below.

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
* **AKLOMS cover size:** the cover test uses raw prediction differences, so
  its effective scale depends on the weight norm. With the Section 6 defaults
  the cover stays at 98–99% of the knowledge base for `tau <= 1` and 87–91% at
  `tau=25`; only `tau=100` brings it to 45.5%. The paper's Figure 7 reports
  much smaller model ratios, but does not give the `tau` values behind panel
  (b), so the absolute `tau` axis is not directly comparable. The qualitative
  trade-off (larger `tau` → smaller cover, higher ACE) is reproduced.
* **Runtime:** E8 measures `train_seconds` once on a shared Windows laptop.
  The timer excludes data loading and W&B calls, but background uploads can
  still perturb wall-clock timing. The scaling shape is more reliable than the
  absolute seconds. The AKLOMS cover check uses an exact nearest-cover binary
  search, so E8(b) reflects prediction cost rather than a naive pairwise
  distance matrix; E8 was rerun after this change.
* **TranOL and OTB** are faithful reimplementations, not the original
  algorithms, because the paper does not restate their full details.

See [`docs/paper_decisions.md`](docs/paper_decisions.md) for the complete list.

## E3: task-specific training-sample probe

E3 follows the revised protocol. Every method is trained on the full stream
(`test_fraction: 0.0`). Before training, 20% of each task's training samples
are drawn without replacement with `np.random.default_rng(seed + 7919)`; the
same indices are used for every method. After a task ends, its frozen
task-specific predictor `f_t` is evaluated on that task's probe. The primary
metric is the task-averaged probe ACE; the pooled probe ACE and the
prequential ACE are reported for context. The old current/old/final-test
forgetting metrics were removed, the old E3 W&B runs were deleted, and E3 was
rerun for all methods.

On `syn1`, AKLO's prequential ACE is 11.95% and its probe ACE is 33.53%.
ITOL and Unif_Sum have the same probe ACE because all three share the same
per-task online update; TOL/TransOL reach 20.07% and OTB 14.30%. The protocol
therefore measures how well each task's own predictor fits its training
distribution, not cross-task retention. The paper's Table 2 applies the final
model to previous tasks, so the comparison is qualitative. See
[`docs/paper_decisions.md`](docs/paper_decisions.md#e3-task-specific-training-sample-probe).

## Other experiments

**E2 (`m_t`).** On `syn1`/AKLO, ACE falls from 22.90% at `m_t=10` to 10.70%
at `m_t=200` (13.11% at 40, 13.78% at 80, 13.47% at 160, 11.63% at 300). More
per-task samples help, matching Figure 3's qualitative trend; the curve is
noisy because each point is a single seed.

**E4/E5 (hyperparameter sensitivity).** The exact grids from the paper's
figure legends are used. For classification (`syn1`), the default
`eta=1`, `lambda=0.001`, `delta_alpha=0.001` gives 11.95%; `eta=10` gives
14.47% and `eta=0` gives 54.34%, while `delta_alpha=0` gives the lowest ACE
(6.80%) because the meta-hypothesis keeps full weight. For regression
(`syn3`), `eta=0.0005` gives 0.96, the default `eta=0.05` gives 1.06,
`lambda=0` gives 0.85, and `delta_alpha=0` gives 0.93. The figures mirror
paper Figures 4/5: three panels of cumulative ACE against task index, one
line per parameter value. Full tables are in `reports/report.md`.

**E6 (`tau`).** Small `tau` (≤0.1) is indistinguishable from AKLO. ACE then
rises with `tau`: on `syn1`, 11.84% at `tau=0.001`, 12.16% at 1, 12.61% at 10,
and 23.13% at 100; on `syn2`, 10.32% at the default and 41.16% at `tau=100`.
This is the expected accuracy/compression trade-off, but the useful `tau` range
is much larger than the paper's.

**E7 (task count).** The same pattern holds for 50–400 tasks: the
selected-model ratio is 98–99% for `tau <= 1`, 86.7–91.0% at `tau=25`, and ACE
increases mildly with `tau`. It never reaches the small ratios shown in the
paper's Figure 7(b); see the `tau` deviation above.

## Weights & Biases

All tracked runs are in the public project

* **Project:** `AKLO-lifelong-online-learning`
* **Entity:** `AI-Athena-Lab`
* **Server:** `https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning`

Each run logs its config, per-task ACE, cumulative ACE, model state, E3 probe
metrics, and sample-level running ACE. No artifacts are uploaded. See
[`docs/wandb.md`](docs/wandb.md) for setup, commands, and the run-naming
convention.

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
  prepare_data.py            # validate local data
src/aklo/
  data/                      # loaders and deterministic stream shuffling
  models/                    # AKLO, AKLOMS, baselines, meta hypothesis
  experiments/               # YAML -> run specifications
  runner.py                  # online loop, metrics, JSON/W&B logging
  report.py                  # tables and figures
  theory.py                  # theory instrumentation and analysis
tests/                       # 75 unit tests
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
