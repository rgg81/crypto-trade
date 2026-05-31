"""Per-symbol realized-vol ceiling primitive — iter-v1/038.

This module provides three pure functions for the per-symbol vol-target ceiling
axis (risk-primitive family, cycle-5 EXP-5/10):

  compute_rv_30d_ann_at_bar(closes_arr, idx, lookback_bars=90) -> float
      Rolling 30d annualized realized vol at bar ``idx``, computed strictly from
      ``closes_arr[:idx+1]`` (past-only; look-ahead safe).

  compute_per_symbol_vol_ceiling(trades_df, symbol, lookback_bars=90, percentile=75.0,
                                  oos_cutoff_ms=OOS_CUTOFF_MS) -> float
      Returns the IS-only percentile of rv_30d_ann over all bars with
      close_time < oos_cutoff_ms.  Computed ONCE per symbol at run start.
      NOT a rolling window — a static threshold from full IS history.

  apply_vol_ceiling(current_rv, threshold, scale_factor=0.5) -> float
      Returns scale_factor when current_rv > threshold (ceiling fires), else 1.0.
      STATELESS — no side effects.

Design notes
------------
- The percentile is estimated from IS-only data (close_time < OOS_CUTOFF_MS).
  Using OOS data would constitute look-ahead bias because the threshold would
  incorporate future regime information.
- rv_30d_ann uses 90 bars (= 30 calendar days at 8h candles) of past-only
  log returns as the standard rolling window.  The annualization factor is
  sqrt(3 * 252) = sqrt(756): 3 candles/day × 252 trading days.
- apply_vol_ceiling is entirely stateless: it can be called inside the backtest
  hot-loop with zero per-call allocation.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

# Sacred constant — matches config.py OOS_CUTOFF_DATE = "2025-03-24".
# Expressed in milliseconds (unix epoch) for direct comparison with close_time.
_OOS_CUTOFF_MS: int = int(pd.Timestamp("2025-03-24", tz="UTC").value // 1_000_000)

# Annualization factor: sqrt(3 candles/day * 252 trading days) = sqrt(756)
_ANN_FACTOR: float = math.sqrt(3 * 252)


def compute_rv_30d_ann_at_bar(
    closes_arr: np.ndarray,
    idx: int,
    lookback_bars: int = 90,
) -> float:
    """Rolling 30d annualized realized vol at bar ``idx`` (past-only).

    Parameters
    ----------
    closes_arr:
        1-D array of close prices, ordered oldest-first.
    idx:
        Bar index at which to evaluate the vol.  Only ``closes_arr[:idx+1]``
        is used — the function is look-ahead-safe by construction.
    lookback_bars:
        Number of past bars in the rolling window.  Default 90 = 30 calendar
        days at 8h candle frequency (3 candles/day × 30 days).

    Returns
    -------
    float
        Annualized realized vol in decimal (e.g. 0.85 = 85% annualized).
        Returns ``float("nan")`` when fewer than 2 past bars are available
        (log-return std is undefined with < 2 observations).
    """
    # Window: use at most lookback_bars past closes, stopping at idx (inclusive)
    start = max(0, idx - lookback_bars + 1)
    window = closes_arr[start : idx + 1]
    if len(window) < 2:
        return float("nan")
    log_rets = np.diff(np.log(window.astype(float)))
    if len(log_rets) < 1:
        return float("nan")
    rv = float(np.std(log_rets, ddof=0)) * _ANN_FACTOR
    return rv


def compute_per_symbol_vol_ceiling(
    klines_df: pd.DataFrame,
    symbol: str,
    lookback_bars: int = 90,
    percentile: float = 75.0,
    oos_cutoff_ms: int = _OOS_CUTOFF_MS,
) -> float:
    """IS-only percentile of rv_30d_ann for ``symbol`` — computed once at run start.

    Parameters
    ----------
    klines_df:
        DataFrame with at least columns ``symbol``, ``close_time``, ``close``.
        Must contain data for ``symbol``.  ALL data is accepted; the function
        filters to IS-only rows (close_time < oos_cutoff_ms) internally.
    symbol:
        Exchange symbol string, e.g. "BTCUSDT".
    lookback_bars:
        Rolling window length for rv_30d_ann (default 90 = 30 days at 8h).
    percentile:
        Percentile of the IS rv_30d_ann distribution to use as the ceiling
        threshold (default 75 = p75 per brief Section 3.2).
    oos_cutoff_ms:
        OOS cutoff in epoch milliseconds.  Bars at or after this cutoff are
        EXCLUDED from percentile estimation — IS-only constraint.
        Default = OOS_CUTOFF_MS = 2025-03-24 00:00 UTC.

    Returns
    -------
    float
        The computed threshold (p75 of rv_30d_ann over IS bars).
        Returns ``float("nan")`` when no IS bars exist for the symbol.

    Raises
    ------
    ValueError
        When ``percentile`` is not in [1.0, 99.0].
    """
    if not (1.0 <= percentile <= 99.0):
        raise ValueError(
            f"percentile must be in [1.0, 99.0], got {percentile}. "
            "Ceiling threshold percentile outside this range is almost certainly a bug."
        )

    sym_df = klines_df[klines_df["symbol"] == symbol].copy()
    # IS-only: exclude bars at or after OOS cutoff
    sym_df = sym_df[sym_df["close_time"] < oos_cutoff_ms].sort_values("close_time")

    if sym_df.empty:
        return float("nan")

    closes = sym_df["close"].to_numpy(dtype=float)
    n = len(closes)
    rv_series = np.empty(n, dtype=float)
    for i in range(n):
        rv_series[i] = compute_rv_30d_ann_at_bar(closes, i, lookback_bars=lookback_bars)

    # Filter NaN (first lookback_bars - 1 bars have insufficient history)
    valid = rv_series[~np.isnan(rv_series)]
    if len(valid) == 0:
        return float("nan")

    return float(np.percentile(valid, percentile))


def apply_vol_ceiling(
    current_rv: float,
    threshold: float,
    scale_factor: float = 0.5,
) -> float:
    """Return the sizing scale to apply at trade entry.

    Parameters
    ----------
    current_rv:
        Realized vol at the entry bar (rv_30d_ann, same units as threshold).
    threshold:
        Per-symbol IS-derived ceiling threshold (e.g. p75 of IS rv_30d_ann).
    scale_factor:
        Sizing multiplier when the ceiling fires (default 0.5 = half-size).
        Must be in (0.0, 1.0].

    Returns
    -------
    float
        ``scale_factor`` when ``current_rv > threshold`` (ceiling fires);
        ``1.0`` otherwise (no adjustment).
        Returns ``1.0`` if ``current_rv`` is NaN (safety: no ceiling when vol
        data is unavailable — conservative entry proceeds at full size).
    """
    if math.isnan(current_rv) or math.isnan(threshold):
        return 1.0
    if current_rv > threshold:
        return scale_factor
    return 1.0
