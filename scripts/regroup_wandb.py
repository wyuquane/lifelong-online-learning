"""Regroup existing W&B runs by configuration.

W&B has a single ``group`` field per run and no nested groups.  This script
sets that field to the run name without its trailing ``-s<seed>`` suffix, so
all seeds of the same configuration share one group.  The experiment name is
preserved as an ``experiment-<name>`` tag.

The default mode is a dry run.  ``--apply`` performs the updates and writes a
resume/backup file; rerunning the script skips runs that are already done.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

EXPERIMENT_DIR = Path("configs") / "experiments"
SEED_SUFFIX = re.compile(r"^(?P<group>.+)-s(?P<seed>\d+)$")


def _experiment_names() -> list[str]:
    return sorted(path.stem for path in EXPERIMENT_DIR.glob("*.yaml"))


def _experiment_for(run_name: str, experiments: list[str]) -> str | None:
    matches = [name for name in experiments if run_name.startswith(f"{name}-")]
    return max(matches, key=len) if matches else None


def _configuration_group(run_name: str) -> str | None:
    match = SEED_SUFFIX.match(run_name)
    return match.group("group") if match else None


def _load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"done": [], "backup": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(state, indent=2), encoding="utf-8")
    temporary.replace(path)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write the new group/tags; without this flag only print the plan",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="update at most this many runs (0 means all)",
    )
    parser.add_argument(
        "--state",
        type=Path,
        default=Path(tempfile.gettempdir()) / "aklo_wandb_regroup_state.json",
        help="resume/backup file (default: system temp directory)",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="attempts per run before giving up",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help="parallel W&B update workers",
    )
    parser.add_argument(
        "--project",
        default=os.getenv(
            "WANDB_PROJECT", "AKLO-lifelong-online-learning"
        ),
    )
    parser.add_argument(
        "--entity",
        default=os.getenv("WANDB_ENTITY", "AI-Athena-Lab"),
    )
    parser.add_argument(
        "--base-url",
        default="https://api.forge.coreweave.com",
    )
    return parser.parse_args()


def _connect(args: argparse.Namespace):
    import wandb

    return wandb.Api(overrides={"base_url": args.base_url})


def _fetch_runs(api, entity: str, project: str):
    return list(api.runs(f"{entity}/{project}", per_page=500))


def _plan(runs, experiments: list[str]):
    planned = []
    skipped = []
    for run in runs:
        group = _configuration_group(run.name)
        experiment = _experiment_for(run.name, experiments)
        if group is None or experiment is None:
            skipped.append(run.name)
            continue
        tag = f"experiment-{experiment}"
        tags = list(dict.fromkeys([*(run.tags or []), tag]))
        planned.append(
            {
                "run": run,
                "id": run.id,
                "name": run.name,
                "old_group": run.group,
                "new_group": group,
                "old_tags": list(run.tags or []),
                "new_tags": tags,
                "experiment": experiment,
            }
        )
    return planned, skipped


def _print_summary(planned, skipped) -> None:
    groups = Counter(item["new_group"] for item in planned)
    sizes = Counter(groups.values())
    print(f"runs to update: {len(planned)}")
    print(f"configuration groups: {len(groups)}")
    print(f"group sizes: {dict(sorted(sizes.items()))}")
    if skipped:
        print(f"skipped runs without a seed/config match: {len(skipped)}")
        for name in skipped[:10]:
            print(f"  {name}")
    unexpected = {group: size for group, size in groups.items() if size != 10}
    if unexpected:
        print(f"WARNING: {len(unexpected)} groups do not contain 10 runs")
        for group, size in list(unexpected.items())[:10]:
            print(f"  {group}: {size}")


_THREAD_LOCAL = threading.local()


def _thread_api(base_url: str):
    """One W&B client per worker thread, reused across that thread's runs."""
    import wandb

    api = getattr(_THREAD_LOCAL, "api", None)
    if api is None:
        api = wandb.Api(overrides={"base_url": base_url})
        _THREAD_LOCAL.api = api
    return api


def _update_one(
    item: dict[str, Any],
    entity: str,
    project: str,
    base_url: str,
    retries: int,
) -> tuple[dict[str, Any], Exception | None]:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            api = _thread_api(base_url)
            run = api.run(f"{entity}/{project}/{item['id']}")
            run.group = item["new_group"]
            run.tags = item["new_tags"]
            run.update()
            return item, None
        except Exception as error:  # pragma: no cover - network dependent
            last_error = error
            if attempt < retries:
                time.sleep(2 ** (attempt - 1))
    return item, last_error


def _apply(
    api,
    planned,
    state_path: Path,
    limit: int,
    retries: int,
    workers: int,
    entity: str,
    project: str,
    base_url: str,
) -> int:
    state = _load_state(state_path)
    done = set(state.get("done", []))
    backup = state.setdefault("backup", {})
    pending = []
    for item in planned:
        run_id = item["id"]
        if run_id in done:
            continue
        if item["old_group"] == item["new_group"] and set(
            item["old_tags"]
        ) == set(item["new_tags"]):
            done.add(run_id)
            continue
        backup.setdefault(
            run_id,
            {
                "name": item["name"],
                "old_group": item["old_group"],
                "old_tags": item["old_tags"],
            },
        )
        pending.append(item)
        if limit and len(pending) >= limit:
            break

    print(f"pending updates: {len(pending)} (workers: {workers})")
    failures = 0
    completed = 0
    total = len(pending)
    start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = [
            pool.submit(_update_one, item, entity, project, base_url, retries)
            for item in pending
        ]
        for future in as_completed(futures):
            item, error = future.result()
            completed += 1
            if error is None:
                done.add(item["id"])
            else:
                failures += 1
                print(
                    f"[fail] {item['name']}: {type(error).__name__}: {error}",
                    file=sys.stderr,
                )
            if completed % 25 == 0 or completed == total:
                elapsed = time.perf_counter() - start
                rate = completed / elapsed if elapsed else 0.0
                remaining = max(total - completed, 0)
                eta = remaining / rate if rate else 0.0
                print(
                    f"completed {completed}/{total} "
                    f"({rate:.2f} runs/s, ETA {eta / 60:.1f} min)"
                )
                state["done"] = sorted(done)
                _save_state(state_path, state)

    state["done"] = sorted(done)
    _save_state(state_path, state)
    print(f"updated {completed - failures} runs; failures {failures}")
    return failures


def _verify(
    entity: str,
    project: str,
    base_url: str,
    expected_groups: set[str],
) -> int:
    # Use a fresh client: the client that performed the updates can return
    # cached run objects with stale group/tag values.
    import wandb

    api = wandb.Api(overrides={"base_url": base_url})
    runs = _fetch_runs(api, entity, project)
    groups = Counter(run.group for run in runs)
    sizes = Counter(groups.values())
    missing = sorted(expected_groups - set(groups))
    extra = sorted(set(groups) - expected_groups)
    tagged = sum(
        any(tag.startswith("experiment-") for tag in (run.tags or []))
        for run in runs
    )
    print(f"total runs: {len(runs)}")
    print(f"groups: {len(groups)}")
    print(f"group sizes: {dict(sorted(sizes.items()))}")
    print(f"runs with an experiment tag: {tagged}")
    if missing:
        print(f"missing groups: {len(missing)}")
        for group in missing[:10]:
            print(f"  {group}")
    if extra:
        print(f"unexpected groups: {len(extra)}")
        for group in extra[:10]:
            print(f"  {group}")
    return 0 if not missing and not extra else 1


def main() -> int:
    load_dotenv()
    args = _parse_args()
    experiments = _experiment_names()
    if not experiments:
        print("No experiment configs found; run from the repository root.", file=sys.stderr)
        return 2

    api = _connect(args)
    runs = _fetch_runs(api, args.entity, args.project)
    print(f"fetched {len(runs)} runs from {args.entity}/{args.project}")
    planned, skipped = _plan(runs, experiments)
    _print_summary(planned, skipped)

    if not args.apply:
        print("dry run: pass --apply to write the new groups")
        return 0

    failures = _apply(
        api,
        planned,
        args.state,
        args.limit,
        args.retries,
        args.workers,
        args.entity,
        args.project,
        args.base_url,
    )
    if failures:
        print(
            f"{failures} runs failed; rerun with --apply to retry (state: {args.state})",
            file=sys.stderr,
        )
        return 1
    expected = {item["new_group"] for item in planned}
    return _verify(args.entity, args.project, args.base_url, expected)


if __name__ == "__main__":
    raise SystemExit(main())
