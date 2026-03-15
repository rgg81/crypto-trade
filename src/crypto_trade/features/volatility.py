"""Volatility features: ATR, NATR, BB, range spike, Garman-Klass, Parkinson, hist vol."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pandas_ta as ta


def add_volatility_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add ~30 volatility feature columns to *df*."""
    close = df["close"]
    high = df["high"]
    low = df["low"]
    open_ = df["open"]
    cols: dict[str, pd.Series] = {}

    # ATR
    for p in (5, 7, 10, 14, 21):
        cols[f"vol_atr_{p}"] = ta.atr(high, low, close, length=p)

    # NATR (normalized ATR)
    for p in (7, 14, 21):
        cols[f"vol_natr_{p}"] = ta.natr(high, low, close, length=p)

    # Bollinger Bands — bandwidth and %B
    for p in (10, 15, 20, 30):
        bb = ta.bbands(close, length=p, std=2.0)
        if bb is not None:
            for col in bb.columns:
                if col.startswith("BBB_"):
                    cols[f"vol_bb_bandwidth_{p}"] = bb[col]
                elif col.startswith("BBP_"):
                    cols[f"vol_bb_pctb_{p}"] = bb[col]

    # Range spike (from range_spike_filter.py formula)
    range_ratio = (high - low) / open_.replace(0.0, np.nan)
    for w in (12, 24, 36, 48, 72, 96):
        rolling_mean = range_ratio.rolling(w, min_periods=w).mean()
        cols[f"vol_range_spike_{w}"] = range_ratio / rolling_mean.replace(0.0, np.nan)

    # Garman-Klass volatility
    log_hl = np.log(high / low) ** 2
    log_co = np.log(close / open_) ** 2
    gk = 0.5 * log_hl - (2 * np.log(2) - 1) * log_co
    for p in (10, 20, 30, 50):
        cols[f"vol_garman_klass_{p}"] = gk.rolling(p, min_periods=p).mean()

    # Parkinson volatility
    log_hl_sq = np.log(high / low) ** 2
    for p in (10, 20, 30, 50):
        cols[f"vol_parkinson_{p}"] = np.sqrt(
            log_hl_sq.rolling(p, min_periods=p).mean() / (4 * np.log(2))
        )

    # Historical volatility (std of returns)
    returns = close.pct_change()
    for p in (5, 10, 20, 30, 50):
        cols[f"vol_hist_{p}"] = returns.rolling(p, min_periods=p).std()

    return pd.concat([df, pd.DataFrame(cols, index=df.index)], axis=1)
