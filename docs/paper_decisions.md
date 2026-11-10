# Paper decisions and deviations

The reproduction follows the paper's algorithms and Section 6 description,
but several details are ambiguous, underspecified, or impossible to match
exactly with the available data. This file records every material decision so
that the results can be interpreted correctly. The guiding principle is
**pipeline correctness over exact numerical matching**: the goal is a faithful,
inspectable implementation of the method and protocol, not a claim that every
reported digit is reproducible.

## 1. Synthetic data

| Decision | Paper | Reproduction | Why |
| --- | --- | --- | --- |
| Number of tasks | 50 (25 per distribution) in the text; Figure 3 and Figure 7 show up to 200/400 tasks | **200** (100 per distribution) | The text and figures conflict. The 200-task choice follows the axes of Figures 3 and 7 and the user decision; it gives longer streams and more stable task-averaged curves. |
| Observations per task | `m_t = 100` | `m_t = 100` | Matches the paper. |
| `syn2` marginal | Same marginal for all tasks; D1 boundary for D1, flipped labels for D2 | Same mean/std as D1 (`mu=[10,10]`, `sigma=1`), D1 boundary, flipped D2 labels | The paper says "same feature generation distribution" but does not spell out the mean; D1's marginal is the natural reading. |
| `syn4` marginal | Identical settings to `syn2` | Same as `syn2`, with regression targets | Follows the paper's statement that `syn4` is the adversarial version of `syn3`. |
| Task order | Arbitrarily and sequentially provided | Global random shuffle per seed, same order for every method | The paper shuffles task order in each repetition. |
| Example order | Shuffled per task | Shuffled per task per seed, same order for every method | Matches the paper's protocol. |
| Held-out split | Not used for E1/E2/E4-E8 | `test_fraction=0.0` for E1/E2/E4-E8; E3 uses a per-task 80/20 train/test split | All experiments except E3 are pure online streams; E3 needs a held-out set to measure post-task generalization. |

The sample pool per synthetic task is at least 300 observations, and a run
with `m_t < 300` uses the first `m_t` rows of that pool. This makes E2's
different `m_t` values nested prefixes of the same data instead of independent
draws.

## 2. Real datasets

| Decision | Paper | Reproduction | Why |
| --- | --- | --- | --- |
| Landmine features | Nine features | Nine features, **no bias** | User decision. A bias feature would likely reduce the large errors; the paper does not say whether one was added. |
| Landmine sampling | 150 examples per task | 150 examples per task, redrawn for every repetition | Matches the paper's sample count; resampling per repetition is our choice. |
| Spam users | 14 users | **15 users** | The local NPZ contains 15 users; user decision to use all of them. |
| Spam features | ~1.5e5 bag-of-word counts | 152,543 raw counts, no TF-IDF | Matches the paper's "word occurrence frequency"; raw counts were chosen by the user. |
| Spam sampling | 200 samples per task | 200 samples per user, redrawn for every repetition | Matches the paper's sample count. |
| London features | 27 binary features + bias | 28 inputs after one-hot encoding + bias | See below. |
| London target | Examination score | Raw examination score | Matches the paper. |
| Bias feature | London has one bias | Only London has a bias column | User decision; synthetic, Landmine, and Spam inputs do not append a constant feature. |

London preprocessing in `src/aklo/data/london.py`:

* year: one-hot, 3 columns;
* student gender: one binary column;
* VR band: one-hot over `{0,1,2,3}`, 4 columns;
* ethnic group: one-hot over 11 categories;
* school gender: one-hot, 3 columns;
* denomination: one-hot, 3 columns;
* `%FSM/100` and `%VR1/100`: two continuous columns;
* bias: one column.

Total: `3 + 1 + 4 + 11 + 3 + 3 + 2 + 1 = 28`.

## 3. AKLO and AKLOMS details

| Decision | Paper | Reproduction | Why |
| --- | --- | --- | --- |
| First task | Algorithm 1 (no knowledge base) | Task 1 uses Algorithm 1; AKLO starts at task 2 | Matches the paper. |
| `alpha_1` | `alpha_1 = 1` | `alpha_1 = 1` | Matches the paper. |
| `alpha` decay | Non-increasing, `Delta_alpha = 0.001` | Decreases by `delta_alpha` after every observation, clipped at 0 | Matches the algorithm. |
| `epsilon` indexing | `sqrt(log(t-1) / (2 sum_i alpha_i))` | `sqrt(log(max(1, task_index)) / (2 sum_i alpha_i))` | `task_index` is zero-based; paper task number is `task_index + 1`. The second task has `epsilon=0`. |
| Classification prediction | `sign(w^T x)` | `sign(w^T x)`, with `sign(0)=+1` | The paper does not define the tie; this convention is documented in the code and tests. |
| Meta loss, classification | Square loss `(y - y_hat)^2` | **Hinge loss** | Section 6 says square loss, but Algorithm 2, the bounded-loss theory, and the reported numbers point to a classification loss. Squared raw predictions gave about 25% ACE on `syn1`; hinge gave about 12%, close to the paper's 10.10%. The choice is configurable via `meta_loss`. |
| Meta loss, regression | Square loss | Squared loss | Matches the paper. |
| AKLOMS `tau` | Different `tau` per task/dataset | One `tau` per dataset, swept in E6/E7/E8 | The paper says different `tau` values are used for different scenarios but does not give a rule. The **absolute** `tau` values are not comparable across implementations: the cover test uses raw prediction differences, whose scale depends on the weight norm. In our runs the cover stays above 90% until `tau ~ 25` and only falls to 45.5% at `tau=100`; the paper's Figure 7 reports much smaller model ratios but does not give the `tau` values behind panel (b). We therefore compare trends, not the exact `tau` axis. |
| AKLOMS cover | `2*tau` packing, random initial member | One random member at task start; add previous models at least `2*tau` away from the cover | Follows Algorithm 3. The current task's model is appended to the knowledge base after the task, not used in the cover during that task. |
| AKLOMS with `tau=0` | Stated to recover AKLO | Full knowledge base + AKLO's `log(t-1)` epsilon | Algorithm 3's `|Lambda_t|` formula would not reproduce Algorithm 2's epsilon, so the `tau=0` special case follows the paper's stated equivalence. |
| Knowledge base contents | Previous task predictors | Final predictor of each previous task | Matches the algorithm. |

## 4. Baselines

ITOL, TOL, and Unif_Sum are direct implementations of the paper's one-line
descriptions. TranOL and OTB are **approximations** because the paper only
cites the original methods and does not restate their algorithms or
hyperparameters:

* **TranOL**: previous task's final model as source; target initialized from
  the source; prediction is `0.5 * source + 0.5 * target`.
* **OTB**: 10 online linear learners, exponential weights on squared error,
  learners initialized from the previous task's snapshots in round-robin
  order, classification only.

The baselines use the paper's default `eta`/`lambda` values (classification
`1.0/0.001`, regression `0.05/0.25`), except OTB which uses `eta=0.5` for its
ensemble members. These choices are documented in `docs/experiment_protocol.md`
and in the model configs.

## 5. Experiment protocol

| Decision | Paper | Reproduction | Why |
| --- | --- | --- | --- |
| Repetitions | 10 per experiment | **1 seed** (`seed=0`) for the committed results | Compute budget. The configs accept multiple seeds; adding them reproduces the paper's repetition protocol. |
| E1/E2/E4-E8 evaluation | Online ACE | Online ACE, `test_fraction=0` | Matches the paper. |
| E3 evaluation | Table 2, "test samples from previous tasks" | Per-task 80/20 held-out split, evaluated immediately after each task | User decision; the paper does not specify the split or the evaluation instant. See below. |
| Global shuffle | Random task and example order per repetition | Deterministic shuffle per seed; same for every method | Necessary for a controlled comparison. |
| Runtime | Wall-clock scaling | `train_seconds` around the predict/update loop only; one measurement | Excludes data loading and logging so that W&B does not contaminate the measurement. The AKLOMS cover check uses an exact nearest-cover binary search, so distance comparison stays negligible next to prediction, as the paper assumes. |

The first E8 run used a brute-force `|knowledge base| x |cover|` distance
matrix. At small `tau` the cover approaches the full knowledge base, so cover
maintenance dominated the runtime and the paper's negative `tau`/runtime trend
disappeared. The committed implementation replaces it with an exact
nearest-cover binary search (`src/aklo/models/akloms.py`); a unit test compares
it with the pairwise check, and spot checks on E6/E7 reproduce the same ACE and
cover ratio. E8 was rerun after this change. Wall-clock timing on a shared
laptop is still noisy, so the E8 numbers remain indicative.

### E3: per-task held-out test protocol

The paper's Table 2 says it evaluates "test samples from previous tasks" but
does not specify the split or the evaluation instant. Following the user
decision, E3 uses a per-task held-out split:

* each task is split independently into 80% train / 20% test, never globally,
  with a stratified split for classification;
* datasets with a fixed E1 training size draw extra rows so the training split
  keeps the E1 size: syn1-syn4 125 -> 100 train / 25 test, Landmine 188 ->
  150 / 38, Spam 250 -> 200 / 50; London splits each school 80/20;
* training then follows E1 exactly;
* immediately after `end_task()`, `model.predict()` is evaluated on that
  task's test set. For AKLO this is the full
  `alpha * meta + (1 - alpha) * current` predictor, not the stored snapshot;
  Unif_Sum includes the newly appended `f_t`; OTB uses its weighted ensemble;
* the primary metric is `test_ace_task_mean`; `test_ace_pooled` and the
  prequential ACE are reported as secondary context.

The old training-sample probe, its `probe_*` metrics, and its W&B runs were
removed, and E3 was rerun under group `e3_task_test` for all six Table 2
methods. OTB is undefined for regression.

This protocol measures post-task generalization, not retention by the final
model. The paper's Table 2 applies the final model to previous tasks, which is
a different question, so the comparison is qualitative. Cross-task retention
is visible in the prequential ACE and in E1.

## 6. Data acquisition

The current reproduction reads local files under `data/`. The original plan
was to load the real datasets programmatically from Hugging Face or Kaggle;
that is not implemented because the local copies are already prepared and the
public mirrors are not stable enough to guarantee byte-identical files. The
loader API is isolated in `src/aklo/data/`, so a downloader can be added
without touching the models or the runner. `data/README.md` documents the
expected files and provenance.

## 7. Results that do not match the paper

These are known and should be read as empirical findings, not as hidden
failures:

1. **Landmine errors are much larger than the paper's** (AKLO ~30% versus
   7.30%). The most likely cause is the missing bias feature and the
   resampling procedure; the relative ordering of methods is still
   informative.
2. **Regression ACEs are much lower than the paper's** for `syn3`, `syn4`, and
   London. The paper's `syn3` values are worse than predicting zero (e.g.
   Unif_Sum 27.69), which is difficult to reconcile with the stated absolute
   loss and data scale. Our values (e.g. AKLO 1.06 on `syn3`) are internally
   consistent with the generated targets. This remains an unresolved
   inconsistency in the paper's reported numbers.
3. **E3 is not the paper's Table 2 protocol.** The paper applies the final
   model to test samples from previous tasks; our E3 evaluates each task's
   held-out test set immediately after training that task. It therefore
   measures post-task generalization, not the final model's retention of all
   previous tasks. The comparison is qualitative.
4. **OTB and TranOL are approximations**, so their absolute numbers should not
   be compared digit-for-digit with the paper.

## 8. Repository and W&B conventions

* Branch: `repro/aklo`; `main` is not pushed to.
* W&B project: `AKLO-lifelong-online-learning`, entity `AI-Athena-Lab`,
  online mode, no artifacts.
* Every run logs its config, per-task metrics, sample-level running ACE, and
  a task table. Local JSON is always written, even with `--no-wandb`.
* The report generator reads local JSON and adds W&B links when available.
