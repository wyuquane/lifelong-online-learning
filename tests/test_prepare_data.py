"""Tests for the Kaggle downloader and checksum manifest."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_FILES = {
    "landmine-detection.csv",
    "spam-detection.npz",
    "london-school/ILEA567.DAT",
    "london-school/ILEA567.ASC",
    "london-school/ILEA567.WS",
}


def _load_prepare_data():
    path = ROOT / "scripts" / "prepare_data.py"
    spec = importlib.util.spec_from_file_location("prepare_data", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_manifest_lists_expected_files() -> None:
    """The manifest records every file the real-data configs need."""
    manifest = json.loads((ROOT / "data" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["dataset"] == "wyuquane/aklo-real-world-dataset"
    assert manifest["version"] == 1
    assert manifest["license"] == "MIT"
    assert set(manifest["files"]) == EXPECTED_FILES
    for entry in manifest["files"].values():
        assert entry["size"] > 0
        assert len(entry["sha256"]) == 64
        int(entry["sha256"], 16)


def test_check_dataset_reports_missing_files(tmp_path: Path, capsys) -> None:
    """A missing data directory fails validation with a clear message."""
    prepare = _load_prepare_data()
    assert prepare.check_dataset(tmp_path) is False
    assert "[missing]" in capsys.readouterr().out


def test_file_status_detects_checksum_mismatch(tmp_path: Path) -> None:
    """Size and digest mismatches are both reported."""
    prepare = _load_prepare_data()
    path = tmp_path / "sample.bin"
    path.write_bytes(b"not the expected content")
    entry = {"size": path.stat().st_size, "sha256": "0" * 64}
    valid, message = prepare._file_status(path, entry)
    assert valid is False
    assert "checksum mismatch" in message


def test_find_source_falls_back_to_unique_basename(tmp_path: Path) -> None:
    """The nested Kaggle London directory is found by basename."""
    prepare = _load_prepare_data()
    nested = tmp_path / "london-school" / "london-school" / "ILEA567.DAT"
    nested.parent.mkdir(parents=True)
    nested.write_bytes(b"data")
    entry = {
        "source": "london-school/ILEA567.DAT",
        "path": "london-school/ILEA567.DAT",
    }
    assert prepare._find_source(tmp_path, entry) == nested


def test_find_source_rejects_ambiguous_basename(tmp_path: Path) -> None:
    """Two files with the same basename are not copied silently."""
    prepare = _load_prepare_data()
    for directory in ("a", "b"):
        path = tmp_path / directory / "ILEA567.DAT"
        path.parent.mkdir()
        path.write_bytes(b"data")
    entry = {"source": "missing/ILEA567.DAT", "path": "london-school/ILEA567.DAT"}
    assert prepare._find_source(tmp_path, entry) is None


@pytest.mark.skipif(
    not (ROOT / "data" / "landmine-detection.csv").exists(),
    reason="local datasets are not committed",
)
def test_local_files_match_manifest() -> None:
    """The checked-out local data matches the committed checksums."""
    prepare = _load_prepare_data()
    assert prepare.check_dataset(ROOT / "data") is True
