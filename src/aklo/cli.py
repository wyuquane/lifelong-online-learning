"""Command-line interface for running reproduction experiments."""

from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path
from typing import Any

from .config import ROOT, load_config
from .experiments import build_specs, experiment_names
from .runner import RunSpec, execute_run


def _resolve_experiment(value: str) -> Path:
    path = Path(value)
    if path.exists():
        return path
    candidate = ROOT / "configs" / "experiments" / f"{value}.yaml"
    if candidate.exists():
        return candidate
    raise FileNotFoundError(
        f"Experiment config not found: {value}. "
        f"Available names: {', '.join(experiment_names())}"
    )


def _filter_specs(
    specs: list[RunSpec],
    dataset: str | None,
    method: str | None,
    seed: int | None,
    limit: int | None,
) -> list[RunSpec]:
    selected = specs
    if dataset:
        selected = [spec for spec in selected if spec.dataset == dataset]
    if method:
        selected = [spec for spec in selected if spec.method == method]
    if seed is not None:
        selected = [spec for spec in selected if spec.seed == seed]
    if limit is not None:
        selected = selected[:limit]
    return selected


def _print_specs(specs: list[RunSpec]) -> None:
    for index, spec in enumerate(specs, start=1):
        overrides = ""
        if spec.data_overrides:
            overrides += f" data={spec.data_overrides}"
        if spec.model_overrides:
            overrides += f" model={spec.model_overrides}"
        print(f"{index:4d}. {spec.run_name}{overrides}")


def _configure_stdout() -> None:
    """Avoid UnicodeEncodeError on consoles using a legacy code page."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass


def main(argv: list[str] | None = None) -> int:
    _configure_stdout()
    parser = argparse.ArgumentParser(
        description="Run AKLO reproduction experiments with W&B tracking."
    )
    parser.add_argument(
        "--experiment",
        "-e",
        required=True,
        help="Experiment name (e.g. e1_main) or path to a YAML file.",
    )
    parser.add_argument("--dataset", help="Only run this dataset.")
    parser.add_argument("--method", help="Only run this method.")
    parser.add_argument("--seed", type=int, help="Only run this seed.")
    parser.add_argument(
        "--limit", type=int, help="Run at most this many specifications."
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Truncate streams to a few tasks and samples.",
    )
    parser.add_argument(
        "--no-wandb",
        action="store_true",
        help="Disable W&B logging (local JSON results are still saved).",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List the selected run specifications without running them.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Keep running after a failed run.",
    )
    args = parser.parse_args(argv)

    experiment_path = _resolve_experiment(args.experiment)
    config = load_config(experiment_path)
    specs = build_specs(config)
    specs = _filter_specs(specs, args.dataset, args.method, args.seed, args.limit)

    if not specs:
        print("No runs selected.")
        return 1

    print(
        f"Experiment {config['experiment']['experiment']}: "
        f"{len(specs)} run(s) selected."
    )
    if args.list:
        _print_specs(specs)
        return 0

    failures: list[tuple[str, str]] = []
    results = []
    for index, spec in enumerate(specs, start=1):
        print(f"\n[{index}/{len(specs)}] {spec.run_name}")
        try:
            result = execute_run(
                spec,
                base=config["base"],
                root=ROOT,
                wandb_enabled=not args.no_wandb,
                smoke=args.smoke,
            )
            if result is not None:
                results.append(result)
                print(
                    f"  ACE={result.summary.get('final_cumulative_ace'):.4f} "
                    f"time={result.summary.get('train_seconds'):.2f}s "
                    f"wandb={result.summary.get('wandb_url')}"
                )
        except Exception as error:  # pragma: no cover - depends on environment
            message = f"{type(error).__name__}: {error}"
            failures.append((spec.run_name, message))
            print(f"  FAILED: {message}")
            if not args.continue_on_error:
                traceback.print_exc()
                break

    print("\nSummary")
    for result in results:
        print(
            f"  {result.run_name}: "
            f"ACE={result.summary.get('final_cumulative_ace')} "
            f"pooled={result.summary.get('pooled_ace')} "
            f"url={result.summary.get('wandb_url')}"
        )
    if failures:
        print("\nFailures:")
        for run_name, message in failures:
            print(f"  {run_name}: {message}")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
