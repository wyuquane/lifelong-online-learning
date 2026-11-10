"""Shared pytest fixtures for the AKLO reproduction."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aklo.config import load_yaml  # noqa: E402
from aklo.data.stream import prepare_stream  # noqa: E402
from aklo.data.synthetic import make_synthetic  # noqa: E402


@pytest.fixture(scope="session")
def root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def syn1_config() -> dict:
    return load_yaml(ROOT / "configs" / "data" / "syn1.yaml")


@pytest.fixture(scope="session")
def syn3_config() -> dict:
    return load_yaml(ROOT / "configs" / "data" / "syn3.yaml")


@pytest.fixture()
def small_syn1():
    """A tiny shuffled classification stream for fast unit tests."""
    stream = make_synthetic("syn1", n_tasks=4, n_samples=20, seed=0)
    return prepare_stream(stream, seed=0)


@pytest.fixture()
def small_syn3():
    """A tiny shuffled regression stream for fast unit tests."""
    stream = make_synthetic("syn3", n_tasks=4, n_samples=20, seed=0)
    return prepare_stream(stream, seed=0)
