"""Build the Markdown report and figures from saved JSON results."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aklo.report import build_report  # noqa: E402


def _configure_stdout() -> None:
    """Avoid UnicodeEncodeError on consoles using a legacy code page."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass


def _resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def main() -> int:
    _configure_stdout()
    parser = argparse.ArgumentParser(description="Build the reproduction report.")
    parser.add_argument("--results", default="results", help="Directory with JSON results.")
    parser.add_argument("--output", default="reports", help="Directory for the report.")
    parser.add_argument(
        "--no-figures",
        action="store_true",
        help="Only write the Markdown tables, without PNG figures.",
    )
    args = parser.parse_args()

    report_path = build_report(
        results_dir=_resolve(args.results),
        output_dir=_resolve(args.output),
        make_figures=not args.no_figures,
    )
    try:
        shown = report_path.relative_to(ROOT)
    except ValueError:
        shown = report_path
    print(f"Report written to {shown}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
