# Experiment protocol

This document records exactly how the Section 6 experiments are implemented.
It is the reference for the numbers in `reports/report.md` and for the
deviations listed in `docs/paper_decisions.md`.

## 1. What a run is

One run is one tuple

```
(experiment, dataset, method, seed, data overrides, model overrides)
```

The common runner is `src/aklo/runner.py`. The CLI entry points are
`scripts/run.py` (one experiment) and `scripts/run_matrix.py` (several
experiments). Each run writes a JSON file to
`results/<experiment>/<run_name>.json` and, unless `--no-wandb` is used, logs
the same information to W&B.

A run always follows this order:

1. Load the dataset (or generate it deterministically).
2. Shuffle the task order once with the run seed.
3. Shuffle the examples inside every task with the same seed.
4. For each task: call `start_task`, stream the training examples online,
   predict before every update, call `end_task`.
5. Save the prequential per-task ACE, the cumulative ACE, the model state, and
   optional post-task diagnostics.

All methods receive exactly the same task order and example order for a given
`(dataset, seed)`. The task and example shuffles are independent RNG streams
(`src/aklo/data/stream.py`).

## 2. Datasets and task construction

### Synthetic datasets (`syn1`-`syn4`)

Generator: `src/aklo/data/synthetic.py`. Defaults: **200 tasks**, **100
training observations per task**, two features.

| Dataset | Task type | D1 | D2 |
| --- | --- | --- | --- |
| `syn1` | classification | `x ~ N([10,10], I)`, `y = sign(a^T x)`, `a = [-1+eps, 1+eps]` | `x ~ N([20,5], I)`, `a = [-0.25+eps, 1+eps]` |
| `syn2` | classification | same as `syn1` D1 | same marginal as D1; labels are `sign(-a^T x)` |
| `syn3` | regression | same `x` and `a` as `syn1` D1, `y = a^T x` | same `x` and `a` as `syn1` D2, `y = a^T x` |
| `syn4` | regression | same as `syn3` D1 | same marginal and flipped score as `syn2` D2 |

`eps ~ N(0, 1e-3)` is drawn independently per task. The first half of the
generated tasks is D1 and the second half is D2; the runner then shuffles the
whole task sequence, so D1 and D2 are interleaved arbitrarily. The sample pool
is at least 300 observations per task so that E2 can use nested prefixes of the
same data for different `m_t`.

> The paper text says 50 synthetic tasks (25 per distribution), but Figures 3
> and 7 show axes up to 200 and 400 tasks. This reproduction uses 200 tasks and
> one seed by default; the 200-task choice follows the figures. See
> `docs/paper_decisions.md`.

### Landmine

Loader: `src/aklo/data/landmine.py`. File:
`data/landmine-detection.csv`. There are 29 geographical regions (tasks) and
nine features. For each run, 150 examples are sampled without replacement from
each region. Labels are `+1` (landmine) and `-1` (clutter). The paper samples
150 examples per task; resampling every repetition is our choice.

### Spam

Loader: `src/aklo/data/spam.py`. File: `data/spam-detection.npz`, a sparse
6000 x 152543 matrix with 15 users and 400 messages per user. We use the first
15 users, sample 200 messages per user without replacement, and keep the raw
bag-of-word counts. Labels are `+1` (spam) and `-1` (non-spam). The paper
mentions 14 users; the local archive contains 15 and all 15 are used.

### London School

Loader: `src/aklo/data/london.py`. File:
`data/london-school/ILEA567.DAT`. Each school is one regression task (139
tasks). Features are one-hot year (3), binary student gender (1), one-hot VR
band (4, including band 0), one-hot ethnic group (11), one-hot school gender
(3), one-hot denomination (3), `%FSM/100`, `%VR1/100`, and a bias column, for
28 inputs. The target is the raw examination score.

## 3. Metric

The paper's Average Cumulative Error (ACE) is

```
ACE = (1/T) * sum_t (1/m_t) * sum_i error(y_hat_{t,i}, y_{t,i})
```

* Classification: `error = 1` if `sign(w^T x) != y`, else `0`, with
  `sign(0) = +1`.
* Regression: `error = |w^T x - y|`.

Predictions are always made **before** the corresponding update (prequential
evaluation). `final_cumulative_ace` in the JSON is the task-averaged ACE over
all tasks, which is the number reported in the tables. `pooled_ace` weights
tasks by their number of samples and is kept as a secondary diagnostic.
`cumulative_ace` at task `t` is the mean of the per-task ACEs seen so far.

## 4. Hyperparameters

Defaults are in `configs/models/*.yaml`. The same values are used for every
dataset unless an experiment sweeps them.

| Method | Classification | Regression |
| --- | --- | --- |
| ITOL, TOL, Unif_Sum, TranOL | hinge, `eta=1.0`, `lambda=0.001` | absolute, `eta=0.05`, `lambda=0.25` |
| OTB | hinge, `eta=0.5`, `lambda=0.001`, 10 learners | not supported |
| AKLO, AKLOMS | hinge current loss, hinge meta loss, `eta=1.0`, `lambda=0.001`, `delta_alpha=0.001` | absolute current loss, squared meta loss, `eta=0.05`, `lambda=0.25`, `delta_alpha=0.001` |

AKLO's `epsilon` at task `t` (zero-based `task_index`) is

```
epsilon = sqrt(log(max(1, task_index)) / (2 * sum_i alpha_i))
```

so the second task has `epsilon = 0`, matching `log(t-1)` in Algorithm 2.
The current predictor starts at zero for every task. `alpha` starts at 1 and
decreases by `delta_alpha` after every observation, clipped at 0.

AKLOMS uses `tau=0.001` by default. At the start of a task it keeps one random
member of the knowledge base in the cover; during the task it adds every
previous model whose predictions differ by at least `2*tau` from all models
already in the cover, then restarts the meta-hypothesis. The current task's
model is appended to the knowledge base after the task but is not added to the
cover used during that task. `tau=0` uses the full knowledge base and AKLO's
`log(t-1)` epsilon, so AKLOMS reduces exactly to AKLO.

The E4/E5 sweeps use the exact paper figure legends:

* Classification (`syn1`): `eta in [10, 1, 0.01, 0.001, 0.0001, 0]`,
  `lambda in [0, 0.0001, 0.001, 0.005, 0.01, 0.05, 0.1]`,
  `delta_alpha in [0, 0.001, 0.005, 0.01, 1]`.
* Regression (`syn3`): `eta in [0.5, 0.25, 0.05, 0.0005, 0.0001, 0]`,
  `lambda in [0, 0.25, 0.625, 0.75, 0.875, 1]`,
  `delta_alpha in [0, 0.001, 0.005, 0.01, 0.025, 1]`.

## 5. Baselines

* **ITOL**: a fresh online linear model per task, no transfer.
* **TOL**: one online linear model trained on the concatenated stream.
* **Unif_Sum**: prediction is the uniform average of all previous task
  predictors. A current predictor is still trained and appended after the
  task, but it is not used in the prediction during the task.
* **TranOL**: the previous task's final predictor is the source. The target
  predictor is initialized from the source and updated online; the prediction
  is the average of source and target outputs. This is an OTL-style
  approximation because the paper does not restate the full TranOL algorithm.
* **OTB**: an online ensemble of 10 linear learners with exponential weights
  on squared error. At the start of a task the learners are initialized from
  the previous task's snapshots in round-robin order. This is an OTB-style
  approximation; the paper only cites the original boosting method.
* **AKLO**: Algorithm 1 for task 1 and Algorithm 2 afterwards. The prediction
  is `alpha * meta + (1-alpha) * current`.
* **AKLOMS**: Algorithm 3, described above.

## 6. Experiments

| ID | Paper element | Config | Script | What it measures |
| --- | --- | --- | --- | --- |
| E1 | Table 1 | `configs/experiments/e1_main.yaml` | `python scripts/run.py --experiment e1_main` | Main comparison on all 7 datasets |
| E2 | Figure 3 | `configs/experiments/e2_small_m.yaml` | `python scripts/run.py --experiment e2_small_m` | ACE versus `m_t` on `syn1` |
| E3 | Table 2 | `configs/experiments/e3_catastrophic-forgetting.yaml` | `python scripts/run.py --experiment e3_catastrophic-forgetting` | Final-state test ACE on the union of all task test sets (10 seeds) |
| E4 | Figure 4 | `configs/experiments/e4_sensitivity_cls.yaml` | `python scripts/run.py --experiment e4_sensitivity_cls` | Classification sensitivity to `eta`, `lambda`, `delta_alpha` |
| E5 | Figure 5 | `configs/experiments/e5_sensitivity_reg.yaml` | `python scripts/run.py --experiment e5_sensitivity_reg` | Regression sensitivity to `eta`, `lambda`, `delta_alpha` |
| E6 | Table 3 | `configs/experiments/e6_akloms_tau.yaml` | `python scripts/run.py --experiment e6_akloms_tau` | AKLOMS ACE versus `tau` |
| E7 | Figure 7 | `configs/experiments/e7_akloms_models.yaml` | `python scripts/run.py --experiment e7_akloms_models` | AKLOMS selected-model ratio versus task count and `tau` |
| E8 | Figure 8 | `configs/experiments/e8_runtime.yaml` | `python scripts/run.py --experiment e8_runtime` | Runtime versus task count, `m_t`, and `tau` |

E1/E2/E4-E8 use `test_fraction: 0.0`: every task is a pure online stream, as
in the paper's ACE definition. E3 is the exception: each task has a separate
held-out test set, and the final model is evaluated on all of them.

### E3 protocol

E3 implements the paper's final-state reading of Table 2: train once on the
whole stream, then feed the test sets of every task `1..T` to the final model.
The datasets and splits are:

| Dataset | Tasks | Train per task | Test per task |
| --- | ---: | ---: | ---: |
| syn1-syn4 | 50 (25 D1 + 25 D2) | 100 | 100 separate samples |
| Landmine | 29 | 150 | all remaining rows |
| Spam | 15 users | 200 | all remaining rows |
| London | 139 schools | 80% | 20% |

The synthetic train and test rows are disjoint blocks of the same task pool.
Landmine and Spam sample the training rows and use every non-training row of
the task as test. London keeps a per-school 80/20 split. Training then follows
E1 exactly: same online loop, same hyperparameters, and the same task/example
shuffles for every method.

After the last task, each method uses its method-specific final predictor:

* **ITOL**: the task-specific snapshot for the evaluated task.
* **TOL**: the single final online model.
* **Unif_Sum**: the uniform average of all task snapshots.
* **TranOL**: the final target model (without the source blend).
* **OTB**: the final weighted ensemble.
* **AKLO**: the full `alpha * meta + (1 - alpha) * current` final state.
* **AKLOMS**: the final AKLO predictor over the selected knowledge base
  (AKLOMS is not part of Table 2).

The primary metric is `final_test_ace_task_mean`, the mean over tasks of the
final-state test ACE. `final_test_ace_pooled` is secondary and prequential ACE
is reported for context. Classification ACE is multiplied by 100; regression
ACE is on the target scale. OTB is undefined for regression.

Two properties follow from this design. TOL and TranOL have identical
final-state rows: both apply the same online updates to the final target model,
and TranOL's source/target blend changes only the prediction, not the update.
On syn2 (and the regression variant syn4) the D2 tasks reuse the D1 marginal
but flip the labels, so a single final predictor cannot fit both distributions;
syn2's classification methods therefore sit near chance.

The paper's Table 2 values are close to its Table 1 values, which suggests the
original implementation may have evaluated each task shortly after training
rather than only at the end. The final-state protocol requested for this
reproduction is a stricter catastrophic-forgetting test, so the comparison is
qualitative. The old per-task E3 protocol and its `e3_task_test` W&B runs were
removed.

## 7. Repetitions and seeds

The paper repeats every experiment 10 times with fresh task and example
shuffles. E3 uses all ten seeds (`0..9`), with the underlying data and split
fixed by `data_seed: 0` and only the task/example order changing per seed. The
other experiments still use `seed: 0` for the committed results because of the
compute budget; their configs accept `seeds: [0, 1, ...]` and will reproduce
the paper's repetition protocol when extended. Runtime in E8 is measured once
on the machine that ran the experiment.

## 8. Runtime measurement

`train_seconds` wraps only the per-sample `predict` + `update` loop. Data
loading, model construction, E3 final-state evaluation, JSON serialization,
and W&B logging are excluded. `total_seconds` includes all of the run after data
loading. E8 reports `train_seconds`.

AKLOMS updates its cover inside the timed loop. The cover check uses an exact
nearest-cover binary search rather than a `|knowledge base| x |cover|` distance
matrix; this keeps the distance comparison negligible, as assumed by the
paper, and preserves the selected models exactly.

## 9. Smoke mode

`--smoke` truncates every stream to `runtime.smoke_tasks` tasks and
`runtime.smoke_samples` observations per task (defaults: 2 and 5). It is only
a wiring test and must not be compared with the paper.

## 10. Local results and report

`results/` is git-ignored. `reports/report.md` and the figures are generated
from the JSON files with

```bash
python scripts/make_report.py
```

The report tool is offline and independent of W&B; W&B links are added to the
tables only when the JSON contains a `wandb_url`.
