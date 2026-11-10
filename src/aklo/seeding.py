"""Deterministic seeding utilities."""

from __future__ import annotations

import os
import random

import numpy as np


def seed_everything(seed: int) -> None:
    """Seed Python and NumPy RNGs.

    The global NumPy RNG is seeded for libraries that still use it; the
    reproduction code itself uses explicit ``default_rng`` streams.
    """
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)


def rng_for(seed: int, stream: int) -> np.random.Generator:
    """Return an independent RNG for a named stream.

    ``stream`` is a small integer used to decouple task order, example order,
    subsampling and train/test splitting.
    """
    return np.random.default_rng(seed + 10_000 * stream)
