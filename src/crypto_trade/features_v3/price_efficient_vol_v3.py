"""v3 efficient OHLC volatility estimators — Parkinson, Garman-Klass, Rogers-Satchell.

Track-isolated copy of v2's price_efficient_vol.py. No imports from
crypto_trade.features or crypto_trade.features_v2 permitted in this file.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _log_ratio(a: pd.Series, b: pd.Series) -> pd.Series:
    return np.log(a.clip(lower=1e-12) / b.clip(lower=1e-12))


def _parkinson(high: pd.Series, low: pd.Series, window: int) -> pd.Series:
    hl = _log_ratio(high, low) ** 2
    return np.sqrt(hl.rolling(window, min_periods=window // 2).mean() / (4.0 * np.log(2.0)))


def _garman_klass(
    open_: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, window: int
) -> pd.Series:
    hl2 = _log_ratio(high, low) ** 2
    co2 = _log_ratio(close, open_) ** 2
    gk = 0.5 * hl2 - (2.0 * np.log(2.0) - 1.0) * co2
    return np.sqrt(gk.rolling(window, min_periods=window // 2).mean().clip(lower=0))


def add_price_efficient_vol_v3_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add v3 efficient OHLC vol features to *df*.

    Requires columns: open, high, low, close.
    """
    open_ = df["open"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    close = df["close"].astype(float)

    pv20 = _parkinson(high, low, 20)
    pv50 = _parkinson(high, low, 50)
    gk20 = _garman_klass(open_, high, low, close, 20)

    df["parkinson_vol_20"] = pv20
    df["parkinson_vol_50"] = pv50
    df["garman_klass_vol_20"] = gk20
    df["parkinson_gk_ratio_20"] = pv20 / gk20.replace(0, np.nan)

    return df
