# Run the theory checks used by reports/theory/README.md.
#
# These are diagnostics, not benchmark runs: they do not log to W&B.  Each
# command traces 50 tasks of the shuffled stream and writes a JSON and a
# Markdown report under reports/theory/.
$ErrorActionPreference = "Continue"

python -X utf8 scripts/check_theory.py --dataset syn1 --method aklo --tasks 50
python -X utf8 scripts/check_theory.py --dataset syn3 --method aklo --tasks 50

# Cover-set checks for Corollary 1.2 at six tau values.
python -X utf8 scripts/check_theory.py --dataset syn1 --method akloms --tau 0 --tasks 50 --packing-tasks 15
python -X utf8 scripts/check_theory.py --dataset syn1 --method akloms --tau 0.01 --tasks 50 --packing-tasks 15
python -X utf8 scripts/check_theory.py --dataset syn1 --method akloms --tau 0.1 --tasks 50 --packing-tasks 15
python -X utf8 scripts/check_theory.py --dataset syn1 --method akloms --tau 1.0 --tasks 50 --packing-tasks 15
python -X utf8 scripts/check_theory.py --dataset syn1 --method akloms --tau 5 --tasks 50 --packing-tasks 15
python -X utf8 scripts/check_theory.py --dataset syn1 --method akloms --tau 10 --tasks 50 --packing-tasks 15

# Corollary 1.1: the alpha decay controls whether the small-interaction
# hypothesis is reachable at all.
python -X utf8 scripts/check_theory.py --dataset syn1 --method aklo --tasks 50 --delta-alpha 0.0001
python -X utf8 scripts/check_theory.py --dataset syn1 --method aklo --tasks 50 --delta-alpha 0.01
