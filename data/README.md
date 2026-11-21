# Data

> **Run this before the real-data experiments.** E1, E3 and E6 read files from
> `data/` and do not download them inside the runner. Download and verify the
> files once before the first run:
>
> ```powershell
> python scripts/prepare_data.py --download
> python scripts/prepare_data.py --check
> ```
>
> E2, E4, E5, E7, E8 and the theory checks use synthetic streams only and need
> no Kaggle files.

## Quick start

Windows (PowerShell):

```powershell
# From the repository root, with the virtual environment activated
python scripts/prepare_data.py --download
python scripts/prepare_data.py --check
```

Linux/macOS:

```bash
python scripts/prepare_data.py --download
python scripts/prepare_data.py --check
```

`--download` does three things:

1. Downloads the public Kaggle archive
   [`wyuquane/aklo-real-world-dataset`](https://www.kaggle.com/datasets/wyuquane/aklo-real-world-dataset)
   (version 1, MIT licence, no Kaggle account or API key).
2. Copies the expected files into `data/` in the layout used by the loaders.
3. Verifies every file's size and SHA-256 digest against
   [`manifest.json`](manifest.json).

`--check` is the default action. It validates the files, prints the Landmine
shape/tasks, the Spam shape/users, and the London students/schools, then prints:

```text
All real datasets are present and match data/manifest.json.
```

## What gets downloaded

| File | Size (bytes) | SHA-256 (first 16 hex) | Used by |
| --- | ---: | --- | --- |
| `landmine-detection.csv` | 2,760,835 | `7396407a1a926a08` | E1, E3, E6 |
| `spam-detection.npz` | 1,910,501 | `8b54bcf1ef29534c` | E1, E3, E6 |
| `london-school/ILEA567.DAT` | 276,517 | `57bbbfd28db39a13` | E1, E3, E6 |
| `london-school/ILEA567.ASC` | 2,868 | `8d9d6cf24b1dd17e` | documentation only |
| `london-school/ILEA567.WS` | 650,025 | `8397e63b0f2fc909` | documentation only |

Expected layout:

```text
data/
├── manifest.json                   # committed checksum manifest
├── landmine-detection.csv          # 2,760,835 bytes
├── spam-detection.npz              # 1,910,501 bytes
└── london-school/
    ├── ILEA567.DAT                 # 276,517 bytes, used by the loader
    ├── ILEA567.ASC                 # 2,868 bytes, original documentation
    └── ILEA567.WS                  # 650,025 bytes, original worksheet
```

The raw files are **not committed** to git because of size. Only
`manifest.json` and this README are tracked.

## Verify, repair, and re-download

```powershell
# Validate the current files (default action)
python scripts/prepare_data.py --check

# Re-download and overwrite every file
python scripts/prepare_data.py --download --force

# Use a different destination directory
python scripts/prepare_data.py --download --data-dir D:\datasets\aklo
```

Existing valid files are left untouched by `--download`; a file that exists but
fails validation is never overwritten silently. Use `--force` when the archive
changed or a file is corrupted.

If you use `--data-dir` with a custom location, update the `path` entries in
`configs/data/*.yaml` (the loaders resolve those paths from the repository
root). The default `data/` layout needs no configuration changes.

## When the real data is not needed

The following commands work without the Kaggle download:

```powershell
# Synthetic-only smoke test
python scripts/run.py --experiment e2_small_m --smoke --no-wandb --limit 2

# Synthetic-only experiments
python scripts/run.py --experiment e2_small_m
python scripts/run.py --experiment e4_sensitivity_cls
python scripts/run.py --experiment e5_sensitivity_reg
python scripts/run.py --experiment e7_akloms_models
python scripts/run.py --experiment e8_runtime

# Theory checks (syn1/syn3)
powershell -ExecutionPolicy Bypass -File scripts/run_theory_checks.ps1
```

E2/E4/E5/E7/E8 use `syn1` or `syn3`, which are generated deterministically by
`src/aklo/data/synthetic.py`. E1, E3 and E6 include `landmine`, `spam`, and
`london`, so they need the files above.

## Manual or offline download

If `kagglehub` cannot reach Kaggle, download the archive manually:

1. Open <https://www.kaggle.com/datasets/wyuquane/aklo-real-world-dataset>
   (version 1). The scripted `kagglehub` download needs no account; the Kaggle
   website may still ask you to sign in before downloading.
2. Download and extract the archive.
3. Copy the files into the layout shown above. The archive nests the London
   files under `london-school/london-school/`; the script normally flattens
   that automatically, but a manual copy should put `ILEA567.DAT`,
   `ILEA567.ASC`, and `ILEA567.WS` directly under `data/london-school/`.
4. Run `python scripts/prepare_data.py --check` to verify sizes and checksums.

Do not rename the files: the loaders and `manifest.json` expect the exact names.

## Troubleshooting

| Symptom | Cause / fix |
| --- | --- |
| `FileNotFoundError: data/landmine-detection.csv` | The real datasets are missing. Run `python scripts/prepare_data.py --download`. |
| `[missing] ...` from `--check` | A file is absent or in the wrong directory. Run `--download`; if it still fails, `--download --force`. |
| `checksum mismatch` | The file is stale or from another archive version. Run `--download --force`. |
| `kagglehub is not installed` | Install the environment: `pip install -r requirements.txt`. |
| `Kaggle download failed` | Check the network/proxy and retry. The dataset is public and needs no login. |
| Permission denied while copying | Close programs that hold the files, or run the command in a normal user shell; avoid protected directories for `--data-dir`. |
| `ModuleNotFoundError: pandas`/`numpy` | The environment is not activated or dependencies are missing; reinstall with `pip install -r requirements.txt`. |

## Provenance and preprocessing

### Landmine detection

- **File:** `data/landmine-detection.csv`
- **Shape used:** 14,820 rows, 29 geographical regions (tasks), 9 features,
  binary label.
- **Columns:** `task_id`, `label`, and `feature_0` ... `feature_8`.
- **Preprocessing:** none beyond casting to `float64`; labels are mapped to
  `+1`/`-1`. For each run, 150 examples are sampled without replacement per
  task. No bias feature is appended (a documented deviation).
- **Provenance:** the Landmine detection benchmark introduced by Xue et al. and
  distributed through several public machine-learning repositories. The Kaggle
  archive contains a task-indexed CSV copy of that benchmark. The original
  source and citation are in the paper's references.

### Spam detection

- **File:** `data/spam-detection.npz`
- **Contents:** a sparse `6000 x 152543` CSR matrix (`data`, `indices`,
  `indptr`, `shape`), labels `y`, and `user_ids`.
- **Shape used:** 15 users, 400 messages per user, 200 messages sampled per
  user per run, 152,543 bag-of-word features. Labels are `+1` (spam) and `-1`
  (non-spam).
- **Preprocessing:** raw word counts, no TF-IDF or normalization.
- **Provenance:** ECML-PKDD 2006 Discovery Challenge spam data. The paper uses
  14 users; the Kaggle archive has 15, and all 15 are used (documented
  deviation). The original source and citation are in the paper's references.

### London School

- **File:** `data/london-school/ILEA567.DAT`
- **Contents:** fixed-width records for 15,362 students in 139 schools.
- **Shape used:** 139 tasks (one per school), 28 inputs, raw examination score.
- **Preprocessing:** one-hot year (3), binary student gender (1), one-hot VR
  band including 0 (4), one-hot ethnic group (11), one-hot school gender (3),
  one-hot denomination (3), `%FSM/100`, `%VR1/100`, and a bias column. See
  `src/aklo/data/london.py` for the exact field offsets.
- **Provenance:** the London School / ILEA dataset distributed by the
  Multilevel Modelling Centre and widely mirrored for regression benchmarks.
  The `.ASC` and `.WS` files are the original documentation and worksheet
  shipped with the data; only `ILEA567.DAT` is read by the loader.

### Synthetic data

`syn1`-`syn4` are generated by `src/aklo/data/synthetic.py` with NumPy
`default_rng` streams derived from the run seed. No files are written. The
generator is deterministic for a given `(name, n_tasks, n_samples, seed)` and
uses nested prefixes so that different `m_t` values in E2 share the same
underlying sample pool.

## Why a separate Kaggle archive?

The paper does not appear to distribute the exact task-indexed/preprocessed
files as one public archive. The original sources (Landmine, ECML-PKDD 2006
Spam, London/ILEA) are heterogeneous and the paper's exact preprocessing and
sampling details are partly unstated. The team therefore packaged the exact
files used in this reproduction, with versioned checksums, so that:

* a fresh clone downloads the same bytes that produced the reported numbers;
* `prepare_data.py --check` can detect a changed archive or a corrupted file;
* the experiment runner never performs manual preprocessing or depends on a
  particular Kaggle account.

This is the "prepare the dataset and upload it to your own Kaggle dataset"
path allowed by the course reproduction guide when no single public copy of the
exact working set exists.

## Reproducibility and licensing

The raw files are kept out of version control. If you replace them, keep the
same names/shapes and rerun `python scripts/prepare_data.py --check`. The
loaders are isolated under `src/aklo/data/`, so the downloader populates the
same paths without changing the models or the runner.

The Kaggle packaging is released under the MIT licence. The original Landmine,
Spam, and London School datasets may carry their own terms; check the original
sources before redistributing any raw file. The checksum manifest is committed
so a future archive change is detected instead of silently changing the
experiments.
