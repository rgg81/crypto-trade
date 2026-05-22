"""v3 calendar/temporal features — iter-v3/063 (MASS FEATURE EXPANSION).

Track-isolated: NO imports from ``crypto_trade.features`` (v1) or
``crypto_trade.features_v2`` (v2). Enforced by Phase 6 pre-flight grep.

Module dependency order: no upstream dependencies; can be placed anywhere in
GROUP_REGISTRY.

References:
    Heston, S. L., & Sadka, R. (2008). Seasonality in the Cross-Section of
        Stock Returns. Journal of Financial Economics, 87(2), 418-445.
        (Documenting weekly cyclicality in return patterns.)

Features:
    candle_dow_sin  — sine component of cyclic day-of-week encoding
    candle_dow_cos  — cosine component of cyclic day-of-week encoding

Rationale:
    Cyclic encoding avoids the spurious ordinality of raw integer DOW (where
    Monday=0 and Sunday=6 appear maximally different despite being adjacent in
    the week cycle). sin/cos encoding preserves the circular structure:
        DOW = 0..6 (Monday=0 in pandas)
        candle_dow_sin = sin(2π * DOW / 7)
        candle_dow_cos = cos(2π * DOW / 7)

    Invariant: sin² + cos² = 1 for all bars.

Note on 8h cadence:
    At 8h candle intervals there are 3 candles per calendar day. The candles
    open at 00:00, 08:00, and 16:00 UTC. All three intra-day candles share the
    same DOW value. This means DOW cycles through 7 values over 21 bars (7 days
    × 3 candles/day), producing a coarser signal than on hourly data.

    ``candle_hour_sin`` was dropped during EDA (ADF FAIL: constant within each
    symbol at 8h cadence with only 4 candles/day; only 1/3 symbols stationary).
    DOW encoding does NOT have this issue because DOW varies across bars.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_calendar_v3_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add v3 calendar features to *df*.

    Requires column ``open_time`` (Unix milliseconds, integer).

    Computes:
        ``candle_dow_sin`` — sin(2π * DOW / 7) where DOW = 0 (Monday) .. 6 (Sunday)
        ``candle_dow_cos`` — cos(2π * DOW / 7)

    Past-only by construction:
        - ``open_time`` is the bar's open timestamp (already elapsed when the bar
          closes). Using it for DOW encoding introduces no look-ahead.
        - The DOW for bar t is determined entirely by open_time[t], which is
          strictly in the past relative to any model-inference or feature-use.
        - Appending future bars does NOT alter candle_dow_sin[t] or
          candle_dow_cos[t] (no rolling windows).

    NaN warm-up: NONE. Both features are valid for every bar (no warm-up period).

    Args:
        df: DataFrame with column ``open_time`` (integer, Unix milliseconds).

    Returns:
        Copy of ``df`` with ``candle_dow_sin`` and ``candle_dow_cos`` appended.
        If ``open_time`` is missing, both columns are set to all-NaN without error.
    """
    df = df.copy()
    if "open_time" not in df.columns:
        df["candle_dow_sin"] = np.nan
        df["candle_dow_cos"] = np.nan
        return df

    open_times = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    dow = open_times.dt.dayofweek.to_numpy(dtype=np.float64)  # 0=Monday, 6=Sunday

    angle = 2.0 * np.pi * dow / 7.0
    df["candle_dow_sin"] = np.sin(angle)
    df["candle_dow_cos"] = np.cos(angle)
    return df


__all__ = [
    "add_calendar_v3_features",
]
