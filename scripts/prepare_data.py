"""Validate the local datasets and print basic statistics.

The reproduction currently uses the data files shipped in ``data/``.  This
script does not download anything; it checks that the expected files are
present and readable so that a run fails early with a clear message.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def check_landmine() -> None:
    path = ROOT / "data" / "landmine-detection.csv"
    if not path.exists():
        print(f"[missing] {path}")
        return
    frame = pd.read_csv(path)
    tasks = frame["task_id"].nunique()
    print(
        f"[ok] landmine: {frame.shape[0]} rows, "
        f"{frame.shape[1] - 2} features, {tasks} tasks"
    )


def check_spam() -> None:
    path = ROOT / "data" / "spam-detection.npz"
    if not path.exists():
        print(f"[missing] {path}")
        return
    archive = np.load(path, allow_pickle=True)
    users = np.unique(archive["user_ids"])
    print(
        f"[ok] spam: shape={tuple(archive['shape'])}, "
        f"{len(users)} users, {archive['data'].size} non-zeros"
    )


def check_london() -> None:
    path = ROOT / "data" / "london-school" / "ILEA567.DAT"
    if not path.exists():
        print(f"[missing] {path}")
        return
    lines = [
        line
        for line in path.read_text(encoding="latin-1").splitlines()
        if len(line) == 16
    ]
    schools = {int(line[1:4]) for line in lines}
    print(f"[ok] london: {len(lines)} students, {len(schools)} schools")


def main() -> int:
    print(f"Repository root: {ROOT}")
    check_landmine()
    check_spam()
    check_london()
    print(
        "\nSynthetic datasets syn1-syn4 are generated deterministically by "
        "src/aklo/data/synthetic.py."
    )
    print(
        "The real datasets are expected under data/.  See data/README.md for "
        "provenance and preprocessing notes."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
