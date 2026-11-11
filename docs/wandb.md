# Weights & Biases tracking

Every experiment is tracked in the public W&B project

* **Project:** `AKLO-lifelong-online-learning`
* **Entity:** `AI-Athena-Lab`
* **Mode:** online
* **Artifacts:** none (the project stores metrics, configs, and tables only)

The defaults live in `configs/base.yaml`. Credentials are read from `.env`
(ignored by git) through `python-dotenv`.

## 1. Setup

```bash
cp .env.example .env
# edit .env and set WANDB_API_KEY
pip install -r requirements.txt
wandb login   # optional if WANDB_API_KEY is set in .env
```

`.env.example`:

```dotenv
WANDB_API_KEY=
WANDB_PROJECT=AKLO-lifelong-online-learning
WANDB_ENTITY=AI-Athena-Lab
WANDB_MODE=online
```

`WANDB_MODE` may be set to `offline` or `disabled` for local testing. The
runner still writes local JSON when W&B is disabled.

## 2. Running with tracking

```bash
# One experiment
python scripts/run.py --experiment e1_main

# A subset
python scripts/run.py --experiment e1_main --dataset syn1 --method aklo

# The full matrix
python scripts/run_matrix.py --experiments e1_main,e2_small_m,e3_catastrophic-forgetting,e4_sensitivity_cls,e5_sensitivity_reg,e6_akloms_tau,e7_akloms_models,e8_runtime

# Smoke test, no W&B
python scripts/run_matrix.py --smoke --no-wandb --limit-per-experiment 2

# PowerShell wrapper (runs all experiments and then builds the report)
.\scripts\reproduce_all.ps1
```

`--no-wandb` is useful for debugging and for re-running a result locally. It
does not change the computation.

## 3. What is logged

Each run is named `<experiment>-<dataset>-<method>[-<overrides>]-s<seed>` and
grouped by experiment. Tags include the dataset, method, and seed.

Per-task metrics (step = task index):

* `task/ace`
* `task/cumulative_ace`
* `task/time_seconds`
* `task/n_samples`
* `state/*` (`alpha`, `epsilon`, `kb_size`, `cover_size`, `selected_ratio`,
  `w_norm`, `beta_entropy`, `beta_max`, `n_updates`, ...)
* `test/*` for E3 per-task held-out diagnostics (`ace`, `total_error`,
  `n_samples`)
* `final_test/ace` for each task's final-state E3 evaluation, with
  `final_test/task` as the step metric

Sample-level metrics are logged after the run, using the global sample index:

* `sample/running_ace`
* `sample/task`

Summary fields include `final_cumulative_ace`, `pooled_ace`,
`final_task_ace`, timing, final model state, E3 per-task diagnostics
(`test_ace_task_mean`, `test_ace_pooled`, `test_n_tasks`,
`test_n_samples`), the final-state E3 metrics
(`final_test_ace_task_mean`, `final_test_ace_pooled`,
`final_test_n_tasks`, `final_test_n_samples`), and `wandb_url`.
Per-task values are logged as history metrics; no tables or model checkpoints
are logged, because W&B table logging creates artifacts and this project must
not contain artifacts.

## 4. Finding runs and adding links

Open:

```
https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning
```

The group view for one experiment is:

```
https://forge.coreweave.com/wandb/AI-Athena-Lab/AKLO-lifelong-online-learning/groups/<experiment>
```

for example `.../groups/e1_main` or
`.../groups/e3_catastrophic-forgetting`.

The W&B server used in this environment is `forge.coreweave.com`; the project
and entity names are the ones requested. Filter by `group` (experiment name)
or by the tags. The run URL is stored in each local JSON as
`summary.wandb_url`; `scripts/make_report.py` turns the numbers in the report
into links automatically. The README contains the curated links for the final
runs.

## 5. Offline and failed runs

If W&B cannot initialize (no network, bad key), `WandbLogger.init` prints a
warning and continues without tracking. The run still produces a JSON file.
This is intentional: a network failure should not destroy an experiment.

## 6. Reproducibility notes

* W&B run names are deterministic for a given config and seed.
* Re-running the same run name creates a new W&B run; it does not overwrite the
  old one. Use the `createdAt` field or the group view to distinguish them.
* The committed report is generated from local JSON, so it remains readable
  even if the W&B project is unavailable.
