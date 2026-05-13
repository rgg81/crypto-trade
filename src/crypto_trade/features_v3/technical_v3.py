"""v3 technical indicator features — iter-v3/063 (MASS FEATURE EXPANSION).

Track-isolated: NO imports from ``crypto_trade.features`` (v1) or
``crypto_trade.features_v2`` (v2). Enforced by Phase 6 pre-flight grep.

Module dependency order: ``technical_v3`` MUST run AFTER ``regime`` (which
produces ``atr14`` indirectly via the true-range computation). In practice,
ADX requires a true-range computation that shares logic with ATR. The group is
registered AFTER ``regime_v3`` in GROUP_REGISTRY.

References:
    Wilder, J. W. (1978). New Concepts in Technical Trading Systems.
    Trend Research. ADX = Directional Movement Index; combines +DI and -DI
    into a single measure of trend strength (0-100 scale).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _wilder_smooth(series: np.ndarray, period: int) -> np.ndarray:
    """Wilder smoothing (EWMA with alpha = 1/period) over a 1D array.

    Wilder (1978) uses a recursive formula:
        smoothed[i] = smoothed[i-1] * (period - 1) / period + series[i] / period
    which is equivalent to EWMA with alpha = 1/period, adjust=False.

    NaN values in the input are propagated forward (treated as 0 for the
    smoothing sum, then NaN-masked in the output). The first non-NaN window
    of size `period` is summed as the seed value (Wilder's first-bar average).

    Args:
        series: 1-D array of float values. NaN-safe.
        period: smoothing period (integer >= 1).

    Returns:
        1-D array of the same length with Wilder-smoothed values. First
        (period-1) elements are NaN (insufficient warm-up).
    """
    n = len(series)
    out = np.full(n, np.nan, dtype=np.float64)
    alpha = 1.0 / period

    # Find first seed window with enough non-NaN bars
    seed_idx = -1
    seed_sum = 0.0
    count = 0
    for i in range(n):
        if not np.isnan(series[i]):
            seed_sum += series[i]
            count += 1
            if count == period:
                seed_idx = i
                break
    if seed_idx < 0:
        return out  # insufficient data

    out[seed_idx] = seed_sum / period
    for i in range(seed_idx + 1, n):
        if np.isnan(series[i]):
            # Propagate NaN (no valid data at bar i)
            out[i] = out[i - 1]  # carry forward last known value
        else:
            out[i] = out[i - 1] * (1.0 - alpha) + series[i] * alpha

    return out


def add_technical_v3_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add v3 technical indicator features to *df*.

    Currently computes:
        ``adx_14`` — Wilder (1978) Average Directional Index with period 14.
            Measures trend strength on a [0, 100] scale (scale-invariant).
            Values above 25 indicate a strong trend; below 20 indicate chop.

    Computation (Wilder 1978):
        1. True Range (TR): max(high-low, |high-prev_close|, |low-prev_close|)
        2. +DM = max(high - prev_high, 0) if > max(prev_low - low, 0) else 0
        3. -DM = max(prev_low - low, 0)  if > max(high - prev_high, 0) else 0
        4. Smooth TR, +DM, -DM over 14 bars (Wilder smoothing = EWMA alpha=1/14)
        5. +DI14 = 100 * smooth(+DM) / smooth(TR)
        6. -DI14 = 100 * smooth(-DM) / smooth(TR)
        7. DX = 100 * |+DI14 - -DI14| / (+DI14 + -DI14)
        8. ADX = Wilder smooth of DX over 14 bars

    Past-only by construction:
        - TR, +DM, -DM all use prev_close and prev_high/prev_low via shift(1).
        - Wilder smoothing is causal (each bar uses only past bars).
        - adx_14[t] depends only on bars [t-14-14, t-1] at most (28 bars warm-up).
        - Appending future bars does NOT alter adx_14[t].

    NaN warm-up: approximately first 27 bars (14 bars for DX seed + 14 bars for
        ADX seed). At 8h cadence: 27 bars ≈ 9 calendar days, well within the 24-month
        IS window.

    Args:
        df: DataFrame with columns ``high``, ``low``, ``close`` (float-castable).

    Returns:
        Copy of ``df`` with ``adx_14`` column appended. Values in [0, 100].
        If required columns are missing, ``adx_14`` is set to all-NaN without error.
    """
    df = df.copy()
    required = ("high", "low", "close")
    if not all(c in df.columns for c in required):
        df["adx_14"] = np.nan
        return df

    period = 14
    high = df["high"].astype(float).to_numpy()
    low = df["low"].astype(float).to_numpy()
    close = df["close"].astype(float).to_numpy()

    prev_high = np.concatenate([[np.nan], high[:-1]])
    prev_low = np.concatenate([[np.nan], low[:-1]])
    prev_close = np.concatenate([[np.nan], close[:-1]])

    # True Range
    tr = np.maximum(
        high - low,
        np.maximum(np.abs(high - prev_close), np.abs(low - prev_close)),
    )
    tr[0] = np.nan

    # Directional movement
    up_move = high - prev_high
    down_move = prev_low - low
    up_move[0] = np.nan
    down_move[0] = np.nan

    plus_dm = np.where(
        (up_move > down_move) & (up_move > 0),
        up_move,
        0.0,
    )
    minus_dm = np.where(
        (down_move > up_move) & (down_move > 0),
        down_move,
        0.0,
    )
    plus_dm[0] = np.nan
    minus_dm[0] = np.nan

    # Wilder smoothing
    smooth_tr = _wilder_smooth(tr, period)
    smooth_plus_dm = _wilder_smooth(plus_dm, period)
    smooth_minus_dm = _wilder_smooth(minus_dm, period)

    # DI lines
    with np.errstate(divide="ignore", invalid="ignore"):
        plus_di = np.where(smooth_tr > 0, 100.0 * smooth_plus_dm / smooth_tr, np.nan)
        minus_di = np.where(smooth_tr > 0, 100.0 * smooth_minus_dm / smooth_tr, np.nan)

    # DX
    di_sum = plus_di + minus_di
    di_diff = np.abs(plus_di - minus_di)
    with np.errstate(divide="ignore", invalid="ignore"):
        dx = np.where(di_sum > 0, 100.0 * di_diff / di_sum, np.nan)

    # ADX = Wilder smooth of DX
    adx = _wilder_smooth(dx, period)

    df["adx_14"] = adx
    return df


__all__ = [
    "add_technical_v3_features",
]
