"""Deterministic seeding utilities."""

from __future__ import annotations

import os
import random

import numpy as np


def seed_everything(seed: int) -> None:
    """Seed Python, NumPy, and the process hash seed.

    The global NumPy RNG is seeded for libraries that still use it; the
    reproduction code itself uses explicit ``default_rng`` streams.

    Parameters
    ----------
    seed : int
        Seed applied to ``PYTHONHASHSEED``, :mod:`random`, and NumPy.

    Returns
    -------
    None
        Global process RNG state is updated in place.
    """
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)


def rng_for(seed: int, stream: int) -> np.random.Generator:
    """Return an independent NumPy generator for a named stream.

    Parameters
    ----------
    seed : int
        Base run seed.
    stream : int
        Small integer selecting an independent stream, such as task order,
        example order, subsampling, or train/test splitting.

    Returns
    -------
    np.random.Generator
        Deterministic generator seeded with ``seed + 10_000 * stream``.
    """
    return np.random.default_rng(seed + 10_000 * stream)
