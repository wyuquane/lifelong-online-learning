"""Tests for the repository-wide docstring check."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_checker():
    path = ROOT / "scripts" / "check_docstrings.py"
    spec = importlib.util.spec_from_file_location("check_docstrings", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_all_src_definitions_have_docstrings() -> None:
    """Every module, class, function, and method under src/aklo is documented."""
    checker = _load_checker()
    problems = checker.check_paths()
    assert problems == [], "\n".join(
        f"{problem.path}:{problem.line}: {problem.qualified_name} "
        f"({problem.reason})"
        for problem in problems
    )


def test_checker_reports_missing_docstring(tmp_path: Path) -> None:
    """The checker flags a deliberately undocumented definition."""
    checker = _load_checker()
    source = tmp_path / "example.py"
    source.write_text("def undocumented(x):\n    return x\n", encoding="utf-8")
    problems = checker.check_paths([source])
    assert {problem.qualified_name for problem in problems} == {
        "<module>",
        "undocumented",
    }
    assert all(problem.reason == "missing" for problem in problems)
