"""Run one experiment configuration.

Examples
--------
python scripts/run.py --experiment e1_main --dataset syn1 --method aklo
python scripts/run.py --experiment e1_main --smoke --no-wandb --limit 2
python scripts/run.py --experiment e7_akloms_models --list
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aklo.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
