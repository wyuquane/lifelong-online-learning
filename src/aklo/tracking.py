"""Weights & Biases tracking wrapper.

The wrapper centralizes every W&B call. It supports online, offline and
disabled modes; tests use ``WANDB_MODE=disabled`` or ``enabled=False``.
"""

from __future__ import annotations

import os
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dotenv is a project dependency
    load_dotenv = None


class WandbLogger:
    """Small wrapper around ``wandb.init`` / ``wandb.log``."""

    def __init__(
        self,
        config: dict[str, Any],
        run_name: str,
        group: str,
        tags: list[str] | None = None,
        enabled: bool = True,
    ) -> None:
        if load_dotenv is not None:
            load_dotenv()
        self.config = config
        self.run_name = run_name
        self.group = group
        self.tags = tags or []
        mode = os.getenv("WANDB_MODE", config.get("wandb", {}).get("mode", "online"))
        self.enabled = enabled and mode != "disabled"
        self.mode = mode
        self.run = None

    @property
    def url(self) -> str | None:
        if self.run is None:
            return None
        return getattr(self.run, "url", None)

    def init(self) -> None:
        if not self.enabled:
            return
        import wandb

        wandb_config = self.config.get("wandb", {})
        try:
            self.run = wandb.init(
                project=wandb_config.get("project", "AKLO-lifelong-online-learning"),
                entity=wandb_config.get("entity", "AI-Athena-Lab"),
                name=self.run_name,
                group=self.group,
                job_type="repro",
                config=self.config,
                tags=self.tags,
                mode=self.mode,
            )
        except Exception as error:  # pragma: no cover - network-dependent
            print(f"[wandb] Could not initialize run ({error}); continuing without W&B.")
            self.enabled = False
            self.run = None

    def define_metric(self, pattern: str, step_metric: str) -> None:
        if self.enabled and self.run is not None:
            self.run.define_metric(pattern, step_metric=step_metric)

    def log(self, data: dict[str, Any], step: int | None = None) -> None:
        if self.enabled and self.run is not None:
            self.run.log(data, step=step)

    def log_summary(self, data: dict[str, Any]) -> None:
        if self.enabled and self.run is not None:
            for key, value in data.items():
                self.run.summary[key] = value

    def finish(self) -> None:
        if self.enabled and self.run is not None:
            self.run.finish()
