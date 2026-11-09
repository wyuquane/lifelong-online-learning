"""Tests for configuration loading and experiment run specifications."""

from __future__ import annotations

from pathlib import Path

import pytest

from aklo.config import ROOT, deep_merge, load_config, load_yaml
from aklo.experiments import build_specs, experiment_names


def test_load_yaml_and_deep_merge() -> None:
    base = {"a": 1, "nested": {"x": 1, "y": 2}}
    override = {"nested": {"y": 3, "z": 4}, "b": 5}
    merged = deep_merge(base, override)
    assert merged == {"a": 1, "nested": {"x": 1, "y": 3, "z": 4}, "b": 5}
    assert base == {"a": 1, "nested": {"x": 1, "y": 2}}


def test_load_config_e1() -> None:
    config = load_config(ROOT / "configs" / "experiments" / "e1_main.yaml")
    assert config["experiment"]["experiment"] == "e1_main"
    assert set(config["datasets"]) == {
        "syn1",
        "syn2",
        "landmine",
        "spam",
        "syn3",
        "syn4",
        "london",
    }
    assert set(config["models"]) == {
        "itol",
        "tol",
        "unif_sum",
        "tranol",
        "otb",
        "aklo",
    }
    assert config["root"] == str(ROOT)


def test_e1_specs_skip_unsupported_models() -> None:
    config = load_config(ROOT / "configs" / "experiments" / "e1_main.yaml")
    specs = build_specs(config)
    # 4 classification datasets x 6 methods, plus 3 regression datasets x
    # 5 methods (OTB is classification-only).
    assert len(specs) == 4 * 6 + 3 * 5
    regression_methods = {spec.method for spec in specs if spec.dataset == "syn3"}
    assert "otb" not in regression_methods


def test_e6_specs_cover_all_tau_values() -> None:
    config = load_config(ROOT / "configs" / "experiments" / "e6_akloms_tau.yaml")
    specs = build_specs(config)
    assert len(specs) == 7 * 9
    assert {spec.model_overrides["tau"] for spec in specs} == {
        0.001,
        0.01,
        0.05,
        0.1,
        0.5,
        1.0,
        5.0,
        10.0,
        100.0,
    }


def test_e8_specs_have_both_figures() -> None:
    config = load_config(ROOT / "configs" / "experiments" / "e8_runtime.yaml")
    specs = build_specs(config)
    figures = {spec.notes.get("figure") for spec in specs}
    assert figures == {"fig8a", "fig8b"}
    assert len(specs) == 8 * 6 + 6 * 8


def test_experiment_names() -> None:
    names = experiment_names()
    assert names == [
        "e1_main",
        "e2_small_m",
        "e3_forgetting",
        "e4_sensitivity_cls",
        "e5_sensitivity_reg",
        "e6_akloms_tau",
        "e7_akloms_models",
        "e8_runtime",
    ]


def test_unknown_experiment_raises() -> None:
    config = {
        "base": {},
        "experiment": {"experiment": "nope"},
        "datasets": {},
        "models": {},
    }
    with pytest.raises(ValueError, match="Unknown experiment"):
        build_specs(config)
