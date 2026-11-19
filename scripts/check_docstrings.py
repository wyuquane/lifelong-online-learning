"""Check that every module, class, function, and method under ``src/aklo`` has a docstring.

The project follows option A of the reproduction checklist: public classes and
functions are the minimum, and this repository documents every definition,
including private helpers.  The check is intentionally structural and fast; it
does not grade prose quality beyond a non-empty summary line.
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "src" / "aklo"
MIN_SUMMARY_LENGTH = 10


@dataclass(frozen=True)
class DocstringProblem:
    """One missing or too-short docstring."""

    path: Path
    line: int
    qualified_name: str
    reason: str


def _docstring_problem(
    path: Path,
    node: ast.AST,
    qualified_name: str,
    reason: str,
) -> DocstringProblem | None:
    """Return a problem when ``node`` has no usable docstring."""
    line = int(getattr(node, "lineno", 1))
    docstring = ast.get_docstring(node, clean=True)
    if not docstring:
        return DocstringProblem(path, line, qualified_name, "missing")
    summary = docstring.strip().splitlines()[0].strip()
    if len(summary) < MIN_SUMMARY_LENGTH:
        return DocstringProblem(
            path,
            line,
            qualified_name,
            f"summary shorter than {MIN_SUMMARY_LENGTH} characters",
        )
    return None


def _walk_definitions(
    node: ast.AST,
    path: Path,
    prefix: str = "",
) -> list[DocstringProblem]:
    """Recursively collect docstring problems from one AST subtree."""
    problems: list[DocstringProblem] = []
    for child in ast.iter_child_nodes(node):
        if not isinstance(
            child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            continue
        qualified_name = f"{prefix}.{child.name}" if prefix else child.name
        problem = _docstring_problem(path, child, qualified_name, "definition")
        if problem is not None:
            problems.append(problem)
        problems.extend(_walk_definitions(child, path, qualified_name))
    return problems


def check_file(path: Path) -> list[DocstringProblem]:
    """Return every docstring problem in one Python source file."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    problems: list[DocstringProblem] = []
    module_problem = _docstring_problem(path, tree, "<module>", "module")
    if module_problem is not None:
        problems.append(module_problem)
    problems.extend(_walk_definitions(tree, path))
    return problems


def check_paths(paths: list[Path] | None = None) -> list[DocstringProblem]:
    """Check a list of files or directories and return all problems."""
    roots = paths or [DEFAULT_SOURCE]
    problems: list[DocstringProblem] = []
    for root in roots:
        if root.is_file():
            files = [root]
        else:
            files = sorted(root.rglob("*.py"))
        for path in files:
            problems.extend(check_file(path))
    return problems


def main(argv: list[str] | None = None) -> int:
    """Run the docstring check and return a process exit code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Files or directories to check (default: src/aklo).",
    )
    args = parser.parse_args(argv)
    problems = check_paths(args.paths or None)
    if not problems:
        print("All modules, classes, functions, and methods have docstrings.")
        return 0
    for problem in problems:
        try:
            shown = problem.path.relative_to(ROOT)
        except ValueError:
            shown = problem.path
        print(
            f"{shown}:{problem.line}: {problem.qualified_name}: {problem.reason}",
            file=sys.stderr,
        )
    print(f"\n{len(problems)} docstring problem(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
