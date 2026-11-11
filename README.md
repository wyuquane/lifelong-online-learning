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

The real datasets are expected under `data/`; see
[`data/README.md`](data/README.md). Synthetic `syn1`–`syn4` are generated
deterministically and need no files. `python scripts/prepare_data.py` checks
the local files.

## Experiment map

| ID | Paper element | Config | Command | W&B |
| --- | --- | --- | --- | --- |
| E1 | Table 1: main comparison | [`e1_main.yaml`](configs/experiments/e1_main.yaml) | `python scripts/run.py --experiment e1_main` | [group](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e1_main) |
| E2 | Figure 3: effect of `m_t` | [`e2_small_m.yaml`](configs/experiments/e2_small_m.yaml) | `python scripts/run.py --experiment e2_small_m` | [group](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e2_small_m) |
| E3 | Table 2: catastrophic forgetting (final state, 10 seeds) | [`e3_catastrophic-forgetting.yaml`](configs/experiments/e3_catastrophic-forgetting.yaml) | `python scripts/run.py --experiment e3_catastrophic-forgetting` | [group](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting) |
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
* **Repetitions:** the paper repeats each experiment 10 times. E3 uses all ten
  seeds (`0..9`) and reports mean ± standard deviation. E1/E2/E4-E8 still use
  `seed=0` for compute reasons; their configs accept `seeds: [0, 1, ...]` and
  will reproduce the repetition protocol when extended.
* **Synthetic task count:** E3 follows the text's 50 tasks (25 per
  distribution). E1/E2/E7 use 200 tasks because Figures 3 and 7 have axes up
  to 200 and 400; this is a deliberate split between the Table 1/Table 2
  protocol and the scaling figures.
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

## E3: catastrophic forgetting (final-state protocol)

E3 follows the paper's Table 2 sentence: train once on the whole stream, then
feed the test sets of all tasks `1..T` to the final model. The synthetic
datasets use 50 tasks (25 D1 + 25 D2), 100 training samples and 100 separate
test samples per task. Landmine uses 150 training rows per task and every
remaining row as test; Spam uses 200 training rows per user and every remaining
row as test. London keeps an 80/20 split per school. The experiment is repeated
with seeds `0..9`; the data and split are fixed by `data_seed=0`, and only the
task/example order changes, matching the paper's repetition description. The
matrix contains 390 runs (39 method/dataset combinations per seed).

The final predictor is method-specific: ITOL uses the task-specific snapshot,
TOL the final online model, Unif_Sum the average of all task snapshots, TranOL
the final target model, OTB the final weighted ensemble, and AKLO the full
`alpha * meta + (1 - alpha) * current` state. The primary metric is the
task-averaged test ACE (`final_test_ace_task_mean`), with pooled test ACE
(`final_test_ace_pooled`) as secondary. Classification ACE is multiplied by
100; regression ACE is on the target scale. OTB is undefined for regression.
The old per-task E3 protocol and its `e3_task_test` W&B runs were removed; the
new group is
[`e3_catastrophic-forgetting`](https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/e3_catastrophic-forgetting).

Task-averaged final-state test ACE (%), mean ± standard deviation over seeds
0–9. Lower is better; the best method per dataset is bold. The last column is
the paper's Table 2 AKLO value.

| Dataset | ITOL | TOL | Unif_Sum | TranOL | OTB | AKLO (ours) | AKLO (paper) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| syn1 | **35.87 ± 2.50** | 38.32 ± 10.02 | 50.01 ± 0.20 | 38.32 ± 10.02 | 37.48 ± 8.62 | 37.73 ± 6.63 | 8.78 |
| syn2 | **33.91 ± 1.89** | 49.87 ± 0.60 | 49.90 ± 0.49 | 49.87 ± 0.60 | 50.01 ± 0.59 | 49.85 ± 0.26 | 8.34 |
| Landmine | 37.95 ± 1.43 | 46.79 ± 13.53 | 55.44 ± 2.09 | 46.79 ± 13.53 | 38.14 ± 11.43 | **37.36 ± 15.04** | 6.78 |
| Spam | 20.00 ± 1.75 | 22.93 ± 7.81 | 20.81 ± 4.85 | 22.93 ± 7.81 | **15.37 ± 4.16** | 22.58 ± 6.81 | 9.97 |
| syn3 | 6.90 ± 0.66 | 6.76 ± 4.16 | **1.77 ± 0.56** | 6.76 ± 4.16 | – | 2.69 ± 0.81 | 3.58 |
| syn4 | 4.83 ± 0.36 | 4.28 ± 2.99 | **1.29 ± 0.15** | 4.28 ± 2.99 | – | 1.40 ± 0.15 | 2.34 |
| London | **12.77 ± 0.03** | 13.86 ± 0.95 | 14.75 ± 0.03 | 13.86 ± 0.95 | – | 13.16 ± 0.71 | 9.57 |

Under this stricter protocol AKLO is best only on Landmine. ITOL wins on
syn1/syn2 because it keeps a separate model per task, OTB wins on Spam, and
Unif_Sum wins on the regression datasets. The gap to the paper is largest for
AKLO (e.g. syn1 37.73 vs 8.78), consistent with the paper's Table 2 values
being very close to its Table 1 values and therefore likely measured per task
rather than only at the end. This is an honest consequence of the chosen
protocol; the comparison with the paper is qualitative.

Two properties of the final-state protocol are worth stating explicitly:

* **TOL and TranOL coincide.** Both perform the same online updates on the
  final target model, and TranOL's source/target blend affects only its
  prediction, not the update. Under the "final target model" rule the two rows
  are therefore identical by construction.
* **syn2 is adversarial.** Its D2 tasks reuse the D1 marginal but flip the
  labels, so no single final linear predictor can fit both distributions;
  every non-ITOL method sits near chance (50%). This is expected, not a bug.

See [`docs/experiment_protocol.md`](docs/experiment_protocol.md) and
[`docs/paper_decisions.md`](docs/paper_decisions.md#e3-catastrophic-forgetting-protocol).

## Other experiments

**E2 (`m_t`).** On `syn1`/AKLO, ACE falls from 22.90% at `m_t=10` to 10.70%
at `m_t=200` (13.11% at 40, 13.78% at 80, 13.47% at 160, 11.58% at 250,
11.63% at 300). More per-task samples help, matching Figure 3's qualitative
trend; the curve is noisy because each point is a single seed. The eight
panels match the paper's eight `m_t` values.

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

Each run logs its config, per-task ACE, cumulative ACE, model state, E3
per-task diagnostics, the final-state E3 test metrics, and sample-level running
ACE. No artifacts are uploaded.
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
tests/                       # 77 unit tests
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
