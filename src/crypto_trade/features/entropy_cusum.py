"""Entropy and CUSUM structural break features (AFML Ch. 17-18).

Entropy features quantify market predictability — low entropy means patterned
price action (edge exploitable), high entropy means random (avoid trading).

CUSUM features detect structural breaks in the return series — regime changes
where the cumulative deviation from the mean exceeds a threshold.

Both are scale-invariant and novel relative to the existing feature set.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _shannon_entropy(x: np.ndarray, n_bins: int = 10) -> float:
    """Shannon entropy of a 1D array, discretized into ``n_bins`` bins.

    Returns entropy in nats (natural log). Higher = more random.
    Handles NaN by returning NaN if >50% of values are NaN.
    """
    x = x[~np.isnan(x)]
    if len(x) < 3:
        return np.nan
    counts, _ = np.histogram(x, bins=n_bins)
    probs = counts / counts.sum()
    probs = probs[probs > 0]
    return float(-np.sum(probs * np.log(probs)))


def _cusum_filter(returns: pd.Series, threshold: float) -> pd.Series:
    """Symmetric CUSUM filter per AFML Ch. 17.

    Tracks cumulative positive and negative deviations from zero.
    Returns the number of candles since the last CUSUM break
    (i.e., since either cusum_pos or cusum_neg exceeded ``threshold``).

    The output is a "freshness" indicator: low values mean a structural
    break just happened (regime change), high values mean the current
    regime has persisted for many candles.
    """
    n = len(returns)
    candles_since = np.full(n, np.nan)
    s_pos = 0.0
    s_neg = 0.0
    last_break = 0

    for i in range(n):
        r = returns.iloc[i]
        if np.isnan(r):
            continue
        s_pos = max(0.0, s_pos + r)
        s_neg = min(0.0, s_neg + r)
        if s_pos > threshold:
            s_pos = 0.0
            last_break = i
        if s_neg < -threshold:
            s_neg = 0.0
            last_break = i
        candles_since[i] = i - last_break

    return pd.Series(candles_since, index=returns.index)


def add_entropy_cusum_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add entropy and CUSUM feature columns to *df*.

    Entropy features (prefix ``ent_``):
    - Rolling Shannon entropy of discretized returns at windows 10, 20, 50.
    - Rolling Shannon entropy of discretized volume changes at window 20.

    CUSUM features (prefix ``cusum_``):
    - Candles since last CUSUM break at thresholds 1σ, 2σ, 3σ.
    - Normalized candles-since (divided by window) for each threshold.
    - Boolean: break within last 5 candles (at 2σ threshold).
    """
    close = df["close"]
    returns = close.pct_change()
    cols: dict[str, pd.Series] = {}

    # --- Entropy features ---
    for window in (10, 20, 50):
        cols[f"ent_shannon_{window}"] = returns.rolling(window, min_periods=window).apply(
            _shannon_entropy, raw=True, kwargs={"n_bins": 10}
        )

    # Volume-change entropy (captures microstructure regime)
    if "volume" in df.columns:
        vol_change = df["volume"].pct_change()
        cols["ent_volume_20"] = vol_change.rolling(20, min_periods=20).apply(
            _shannon_entropy, raw=True, kwargs={"n_bins": 10}
        )

    # --- CUSUM features ---
    # Compute rolling std for adaptive thresholds
    rolling_std_50 = returns.rolling(50, min_periods=20).std()

    for n_sigma in (1.0, 2.0, 3.0):
        # Adaptive threshold: n_sigma × rolling_std
        threshold = n_sigma * rolling_std_50.median()
        if np.isnan(threshold) or threshold <= 0:
            threshold = n_sigma * 0.02  # fallback: 2% per sigma

        candles_since = _cusum_filter(returns, threshold)
        cols[f"cusum_since_{n_sigma:.0f}s"] = candles_since

        # Normalize by a reference window (50 candles) for scale invariance
        cols[f"cusum_norm_{n_sigma:.0f}s"] = candles_since / 50.0

    # Binary: CUSUM break within last 5 candles (at 2σ)
    threshold_2s = 2.0 * rolling_std_50.median()
    if np.isnan(threshold_2s) or threshold_2s <= 0:
        threshold_2s = 0.04
    cusum_2s = _cusum_filter(returns, threshold_2s)
    cols["cusum_break_5"] = (cusum_2s <= 5).astype(float)

    return pd.concat([df, pd.DataFrame(cols, index=df.index)], axis=1)
