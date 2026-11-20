"""Download and validate the real datasets used by the reproduction.

The three real datasets are distributed as one public Kaggle dataset
(``wyuquane/aklo-real-world-dataset``, MIT licence, version 1).  Kaggle does not
require credentials for this public download.  ``--download`` fetches the
dataset with :mod:`kagglehub` and copies the files into the layout expected by
``configs/data/*.yaml``.  ``--check`` (the default) verifies that every file is
present, has the expected size, and matches the SHA-256 digest recorded in
``data/manifest.json``.

Synthetic datasets ``syn1``-``syn4`` are generated in code and need no files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = ROOT / "data"
MANIFEST_PATH = ROOT / "data" / "manifest.json"
KAGGLE_HANDLE = "wyuquane/aklo-real-world-dataset/versions/1"
KAGGLE_URL = "https://www.kaggle.com/datasets/wyuquane/aklo-real-world-dataset"


def sha256(path: Path) -> str:
    """Return the hexadecimal SHA-256 digest of ``path``."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    """Load the checksum manifest that describes the expected data files."""
    return json.loads(path.read_text(encoding="utf-8"))


def _file_status(path: Path, entry: dict[str, Any]) -> tuple[bool, str]:
    """Compare one file with its manifest entry and return a status message."""
    if not path.exists():
        return False, f"[missing] {path}"
    size = path.stat().st_size
    if size != int(entry["size"]):
        return False, f"[size mismatch] {path}: {size} != {entry['size']}"
    digest = sha256(path)
    if digest != entry["sha256"]:
        return False, f"[checksum mismatch] {path}: {digest}"
    return True, f"[ok] {path.name}: {size} bytes, sha256 {digest[:12]}..."


def check_dataset(
    data_dir: Path = DEFAULT_DATA_DIR,
    manifest: dict[str, Any] | None = None,
) -> bool:
    """Validate every manifest file under ``data_dir`` and print a report."""
    manifest = manifest or load_manifest()
    ok = True
    for relative, entry in manifest["files"].items():
        valid, message = _file_status(data_dir / relative, entry)
        ok = ok and valid
        print(message)
    return ok


def _find_source(download_root: Path, entry: dict[str, Any]) -> Path | None:
    """Locate one dataset file in the extracted Kaggle directory tree.

    The Kaggle archive wraps the London files in a duplicated
    ``london-school/london-school`` directory.  Prefer the recorded source path
    and fall back to a unique basename match so a layout change in a future
    archive does not silently copy the wrong file.
    """
    source = entry.get("source")
    if source:
        candidate = download_root / source
        if candidate.is_file():
            return candidate
    name = Path(source or entry.get("path", "")).name
    matches = [path for path in download_root.rglob(name) if path.is_file()]
    if len(matches) == 1:
        return matches[0]
    return None


def download_dataset(
    data_dir: Path = DEFAULT_DATA_DIR,
    force: bool = False,
    manifest: dict[str, Any] | None = None,
) -> bool:
    """Download the Kaggle archive and copy the expected files into ``data_dir``.

    Existing valid files are left untouched unless ``force`` is true.  A file
    that exists but fails validation is never overwritten silently; rerun with
    ``--force`` to replace it.
    """
    try:
        import kagglehub
    except ImportError:
        print(
            "[error] kagglehub is not installed. Run "
            "`pip install -r requirements.txt` first.",
            file=sys.stderr,
        )
        return False

    manifest = manifest or load_manifest()
    print(f"Downloading {KAGGLE_URL} (version 1) with kagglehub...")
    try:
        download_root = Path(
            kagglehub.dataset_download(
                KAGGLE_HANDLE,
                force_download=force,
            )
        )
    except Exception as exc:  # pragma: no cover - network dependent
        print(f"[error] Kaggle download failed: {exc}", file=sys.stderr)
        print(
            "Check the network connection and retry; the dataset is public "
            "and needs no Kaggle account.",
            file=sys.stderr,
        )
        return False

    data_dir.mkdir(parents=True, exist_ok=True)
    ok = True
    for relative, entry in manifest["files"].items():
        destination = data_dir / relative
        if destination.exists() and not force:
            valid, message = _file_status(destination, entry)
            if valid:
                print(f"[skip] {destination} already matches the manifest")
                continue
            print(
                f"[error] {message}; rerun with --force to replace it",
                file=sys.stderr,
            )
            ok = False
            continue

        source = _find_source(download_root, {**entry, "path": relative})
        if source is None:
            print(
                f"[error] could not find {relative} in {download_root}",
                file=sys.stderr,
            )
            ok = False
            continue

        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        valid, message = _file_status(destination, entry)
        if valid:
            print(f"[copy] {destination}")
        else:
            print(f"[error] {message}", file=sys.stderr)
        ok = ok and valid

    if ok:
        print(f"\nDataset ready under {data_dir}")
    return ok


def check_landmine(data_dir: Path) -> bool:
    """Print the shape and task count of the Landmine dataset."""
    path = data_dir / "landmine-detection.csv"
    if not path.exists():
        print(f"[missing] {path}")
        return False
    frame = pd.read_csv(path)
    tasks = frame["task_id"].nunique()
    print(
        f"[ok] landmine: {frame.shape[0]} rows, "
        f"{frame.shape[1] - 2} features, {tasks} tasks"
    )
    return True


def check_spam(data_dir: Path) -> bool:
    """Print the shape and user count of the spam dataset."""
    path = data_dir / "spam-detection.npz"
    if not path.exists():
        print(f"[missing] {path}")
        return False
    archive = np.load(path, allow_pickle=True)
    users = np.unique(archive["user_ids"])
    shape = tuple(int(value) for value in archive["shape"])
    print(
        f"[ok] spam: shape={shape}, "
        f"{len(users)} users, {archive['data'].size} non-zeros"
    )
    return True


def check_london(data_dir: Path) -> bool:
    """Print the student and school counts of the London dataset."""
    path = data_dir / "london-school" / "ILEA567.DAT"
    if not path.exists():
        print(f"[missing] {path}")
        return False
    lines = [
        line
        for line in path.read_text(encoding="latin-1").splitlines()
        if len(line) == 16
    ]
    schools = {int(line[1:4]) for line in lines}
    print(f"[ok] london: {len(lines)} students, {len(schools)} schools")
    return True


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line options for the data preparation script."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download the public Kaggle dataset and populate the data directory.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate the files and checksums (default action).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download and overwrite existing files (use with --download).",
    )
    parser.add_argument(
        "--data-dir",
        default=str(DEFAULT_DATA_DIR),
        help="Destination directory for the datasets (default: <repo>/data).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the requested download and/or validation action."""
    args = parse_args(argv)
    data_dir = Path(args.data_dir)
    if not data_dir.is_absolute():
        data_dir = ROOT / data_dir
    manifest = load_manifest()

    if args.force and not args.download:
        print("[error] --force requires --download", file=sys.stderr)
        return 2

    if args.download:
        if not download_dataset(data_dir, force=args.force, manifest=manifest):
            return 1
        if not check_dataset(data_dir, manifest):
            return 1

    # ``--check`` is the default; after a successful download the checks above
    # have already run, so avoid printing the same report twice.
    if args.check or not args.download:
        print(f"Repository root: {ROOT}")
        files_ok = check_dataset(data_dir, manifest)
        stats_ok = all(
            [
                check_landmine(data_dir),
                check_spam(data_dir),
                check_london(data_dir),
            ]
        )
        print(
            "\nSynthetic datasets syn1-syn4 are generated deterministically by "
            "src/aklo/data/synthetic.py."
        )
        if not (files_ok and stats_ok):
            print(
                "\nSome real datasets are missing or invalid. Run "
                "`python scripts/prepare_data.py --download` to fetch the "
                "public Kaggle dataset.",
                file=sys.stderr,
            )
            return 1
        print("All real datasets are present and match data/manifest.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
