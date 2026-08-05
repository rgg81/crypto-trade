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
    # No .dropna() here: silently trimming NaN observations would both change
    # the effective sample length behind the caller's back and, worse, splice
    # non-adjacent calendar days into adjacent positions before the circular
    # sampler runs -- manufacturing the exact spurious temporal adjacency
    # block bootstrapping exists to avoid. NaN is rejected by the finiteness
    # check below instead, with the same error message as any other
    # non-finite value.
    values = daily.to_numpy(dtype=float)
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
    # `not trial_count >= 1` (rather than `trial_count < 1`) so a NaN
    # trial_count is rejected too. Every IEEE-754 comparison with NaN is
    # False, including both `nan >= 1` and `nan < 1` -- but only wrapping
    # the `>=` form in `not` turns that False into a raise; the plain `< 1`
    # form leaves a NaN silently accepted, then propagating through the
    # arithmetic below to `1.0 - nan = nan`, and CPython's
    # `min(1.0, nan) == 1.0` -- the most favourable possible confidence out
    # of a module whose job is to penalise. Mirrors the positive_fraction
    # check above, whose chained comparison already rejects NaN this way.
    if not trial_count >= 1:
        raise ValueError("trial_count must be at least 1")
    return max(0.0, min(1.0, 1.0 - trial_count * (1.0 - positive_fraction)))
