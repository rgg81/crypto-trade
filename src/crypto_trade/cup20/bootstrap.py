"""Circular block bootstrap and multiplicity-adjusted confidence."""

from __future__ import annotations

import numpy as np
import pandas as pd


def circular_block_bootstrap_positive_fraction(
    daily: pd.Series,
    *,
    samples: int = 2000,
    block_days: int = 10,
    seed: int = 20260804,
) -> float:
    """Fraction of circular block bootstrap resample means that are strictly positive."""
    if samples < 1 or block_days < 1:
        raise ValueError("samples and block_days must be positive")
    values = daily.dropna().to_numpy(dtype=float)
    if values.size < block_days * 2:
        raise ValueError("daily series is too short for the requested block length")
    if not np.isfinite(values).all():
        raise ValueError("daily series contains non-finite values")

    length = values.size
    blocks = int(np.ceil(length / block_days))
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, length, size=(samples, blocks))
    offsets = np.arange(block_days)
    indices = (starts[:, :, None] + offsets[None, None, :]) % length
    resampled = values[indices.reshape(samples, blocks * block_days)[:, :length]]
    return float(np.mean(resampled.mean(axis=1) > 0.0))


def trial_adjusted_confidence(positive_fraction: float, trial_count: int) -> float:
    """Penalise the bootstrap confidence by the team's complete accepted-trial count."""
    if not 0.0 <= positive_fraction <= 1.0:
        raise ValueError("positive_fraction must lie in [0, 1]")
    if trial_count < 1:
        raise ValueError("trial_count must be at least 1")
    return max(0.0, min(1.0, 1.0 - trial_count * (1.0 - positive_fraction)))
