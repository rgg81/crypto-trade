"""Mean reversion features: BB %B, z-score, VWAP distance, RSI extremes, % from high/low."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pandas_ta as ta


def add_mean_reversion_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add ~25 mean reversion feature columns to *df*."""
    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]
    cols: dict[str, pd.Series] = {}

    # BB %B
    for p in (10, 15, 20, 30):
        bb = ta.bbands(close, length=p, std=2.0)
        if bb is not None:
            for col in bb.columns:
                if col.startswith("BBP_"):
                    cols[f"mr_bb_pctb_{p}"] = bb[col]

    # Z-score of price
    for p in (10, 20, 30, 50, 100):
        rolling_mean = close.rolling(p, min_periods=p).mean()
        rolling_std = close.rolling(p, min_periods=p).std()
        cols[f"mr_zscore_{p}"] = (close - rolling_mean) / rolling_std.replace(0.0, np.nan)

    # Distance from VWAP
    typical_price = (high + low + close) / 3
    vwap = (typical_price * volume).cumsum() / volume.cumsum().replace(0.0, np.nan)
    cols["mr_dist_vwap"] = (close - vwap) / vwap.replace(0.0, np.nan)

    # RSI extreme categorical (1 = oversold <30, -1 = overbought >70, 0 = neutral)
    for p in (7, 14, 21):
        rsi = ta.rsi(close, length=p)
        if rsi is not None:
            extreme = pd.Series(0, index=df.index, dtype=np.int8)
            extreme = extreme.where(rsi >= 30, 1)  # oversold
            extreme = extreme.where(rsi <= 70, -1)  # overbought
            cols[f"mr_rsi_extreme_{p}"] = extreme

    # % from rolling high
    for p in (5, 10, 20, 50, 100):
        rolling_high = high.rolling(p, min_periods=p).max()
        cols[f"mr_pct_from_high_{p}"] = (close - rolling_high) / rolling_high.replace(0.0, np.nan)

    # % from rolling low
    for p in (5, 10, 20, 50, 100):
        rolling_low = low.rolling(p, min_periods=p).min()
        cols[f"mr_pct_from_low_{p}"] = (close - rolling_low) / rolling_low.replace(0.0, np.nan)

    # Normalized distance from SMA
    for p in (10, 20, 50):
        sma = ta.sma(close, length=p)
        if sma is not None:
            cols[f"mr_dist_sma_{p}"] = (close - sma) / sma.replace(0.0, np.nan)

    return pd.concat([df, pd.DataFrame(cols, index=df.index)], axis=1)
