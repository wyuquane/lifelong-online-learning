"""Empirically check Theorem 1, Corollary 1.1 and Corollary 1.2.

Examples
--------
python scripts/check_theory.py --dataset syn1 --method aklo --tasks 50
python scripts/check_theory.py --dataset syn3 --method aklo --tasks 50
python scripts/check_theory.py --dataset syn1 --method akloms --tau 0.1 --tasks 50

The script writes a JSON file and a Markdown report under ``reports/theory``.
It never logs to W&B: the theory checks are diagnostics, not benchmark runs.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402

from aklo.config import load_yaml  # noqa: E402
from aklo.data import load_dataset  # noqa: E402
from aklo.data.stream import prepare_stream  # noqa: E402
from aklo.theory import (  # noqa: E402
    analyze_trace,
    render_markdown,
    trace_stream,
)


def _label(value: float) -> str:
    return f"{value:g}"


def _packing_indices(n_tasks: int, count: int) -> set[int]:
    """Choose evenly spaced task indices, excluding the first task."""
    candidates = list(range(1, n_tasks))
    if not candidates or count <= 0:
        return set()
    if count >= len(candidates):
        return set(candidates)
    positions = np.linspace(0, len(candidates) - 1, count)
    return {candidates[int(round(position))] for position in positions}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check the paper's theory on one instrumented stream."
    )
    parser.add_argument("--dataset", default="syn1", help="Dataset name.")
    parser.add_argument("--method", default="aklo", choices=["aklo", "akloms"])
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--tasks",
        type=int,
        default=50,
        help="Number of tasks to trace (the paper uses 200 in Section 6).",
    )
    parser.add_argument(
        "--tau",
        type=float,
        default=0.1,
        help="AKLOMS cover threshold (ignored for AKLO).",
    )
    parser.add_argument(
        "--R",
        type=float,
        default=None,
        help="Norm bound for the oracle problem. Default: max observed norm.",
    )
    parser.add_argument(
        "--delta-alpha",
        type=float,
        default=None,
        help="Override the alpha decay rate (useful for Corollary 1.1).",
    )
    parser.add_argument(
        "--packing-tasks",
        type=int,
        default=15,
        help="Number of tasks on which to compute the empirical packing number.",
    )
    parser.add_argument(
        "--output",
        default=str(ROOT / "reports" / "theory"),
        help="Output directory.",
    )
    args = parser.parse_args(argv)

    data_config = load_yaml(ROOT / "configs" / "data" / f"{args.dataset}.yaml")
    model_config = load_yaml(ROOT / "configs" / "models" / f"{args.method}.yaml")

    stream = load_dataset(args.dataset, data_config, args.seed, root=ROOT)
    stream = prepare_stream(stream, args.seed)
    if args.tasks > 0:
        stream.tasks = stream.tasks[: args.tasks]

    overrides: dict[str, Any] = {}
    if args.method == "akloms":
        overrides["tau"] = float(args.tau)
    if args.delta_alpha is not None:
        overrides["delta_alpha"] = float(args.delta_alpha)

    print(
        f"Tracing {args.dataset}/{args.method} "
        f"({len(stream.tasks)} tasks, {stream.n_features} features)"
    )
    traces = trace_stream(
        stream,
        args.method,
        model_config,
        seed=args.seed,
        model_overrides=overrides,
    )
    analysis = analyze_trace(
        traces,
        stream.task_type,
        meta_loss=str(model_config.get(stream.task_type, {}).get("meta_loss", "squared")),
        current_loss=str(model_config.get(stream.task_type, {}).get("loss", "absolute")),
        R=args.R,
        tau=float(args.tau) if args.method == "akloms" else None,
        packing_task_indices=(
            _packing_indices(len(stream.tasks), args.packing_tasks)
            if args.method == "akloms"
            else None
        ),
    )

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    suffix = f"-tau{_label(args.tau)}" if args.method == "akloms" else ""
    if args.delta_alpha is not None:
        suffix += f"-da{_label(args.delta_alpha)}"
    stem = f"{args.dataset}-{args.method}{suffix}-s{args.seed}"
    json_path = output / f"{stem}.json"
    markdown_path = output / f"{stem}.md"

    payload = {
        "dataset": args.dataset,
        "method": args.method,
        "seed": args.seed,
        "tau": float(args.tau) if args.method == "akloms" else None,
        "n_tasks": len(stream.tasks),
        **analysis,
    }
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)

    title = f"Theory check: {args.dataset} / {args.method}"
    if args.method == "akloms":
        title += f" (tau={_label(args.tau)})"
    title += f", seed {args.seed}"
    markdown_path.write_text(render_markdown(analysis, title), encoding="utf-8")

    summary = analysis["summary"]
    print(f"  K={summary['K']:.4f} R={summary['R']:.4f}")
    print(
        "  Theorem 1: median ratio proof="
        f"{summary['median_ratio_proof']:.3f}, "
        f"covered={summary['fraction_ce_le_bound_proof']:.1%}"
    )
    print(
        "  Corollary 1.1: feasible="
        f"{summary['corollary_1_1_feasible']}/{summary['corollary_1_1_applicable']}"
    )
    if summary.get("corollary_1_2_median_cover_size") is not None:
        print(
            "  Corollary 1.2: median cover="
            f"{summary['corollary_1_2_median_cover_size']:.1f}, "
            f"median ratio={summary['corollary_1_2_median_ratio_cover_size']:.3f}"
        )
    print(f"  wrote {json_path}")
    print(f"  wrote {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
