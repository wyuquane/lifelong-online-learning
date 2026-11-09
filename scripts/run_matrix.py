"""Run several experiment configurations sequentially.

Examples
--------
python scripts/run_matrix.py
python scripts/run_matrix.py --experiments e1_main,e2_small_m
python scripts/run_matrix.py --smoke --no-wandb --limit-per-experiment 2
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aklo.cli import main  # noqa: E402
from aklo.experiments import experiment_names  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the full experiment matrix.")
    parser.add_argument(
        "--experiments",
        default=",".join(experiment_names()),
        help="Comma-separated experiment names (default: all).",
    )
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--no-wandb", action="store_true")
    parser.add_argument("--limit-per-experiment", type=int, default=None)
    parser.add_argument("--continue-on-error", action="store_true")
    return parser.parse_args()


def main_matrix() -> int:
    args = parse_args()
    experiments = [name.strip() for name in args.experiments.split(",") if name.strip()]
    failures: list[str] = []
    for name in experiments:
        print(f"\n{'=' * 70}\nRunning {name}\n{'=' * 70}")
        argv = ["--experiment", name]
        if args.smoke:
            argv.append("--smoke")
        if args.no_wandb:
            argv.append("--no-wandb")
        if args.limit_per_experiment is not None:
            argv.extend(["--limit", str(args.limit_per_experiment)])
        if args.continue_on_error:
            argv.append("--continue-on-error")
        code = main(argv)
        if code != 0:
            failures.append(name)
            if not args.continue_on_error:
                break
    if failures:
        print(f"\nExperiments with failures: {', '.join(failures)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main_matrix())
