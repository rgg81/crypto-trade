"""v3 BTC cross-asset features.

Track-isolated copy of v2's cross_btc.py. No imports from crypto_trade.features
or crypto_trade.features_v2 permitted in this file.

Features added:
    btc_ret_3d      — BTC log return over 3 days (9 x 8h bars)
    btc_ret_7d      — BTC log return over 7 days (21 x 8h bars)
    btc_ret_14d     — BTC log return over 14 days (42 x 8h bars)
    btc_vol_14d     — BTC 14-day realized vol (std of 1-bar log returns x sqrt(42))
    sym_vs_btc_ret_7d — symbol's 7-day log return minus BTC's 7-day log return
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

BTC_CSV_PATH = Path("data/BTCUSDT/8h.csv")

_BTC_CACHE_V3: pd.DataFrame | None = None


def _load_btc_v3_features() -> pd.DataFrame:
    """Load BTC 8h klines and precompute BTC-derived columns (cached)."""
    global _BTC_CACHE_V3
    if _BTC_CACHE_V3 is not None:
        return _BTC_CACHE_V3

    df = pd.read_csv(BTC_CSV_PATH).sort_values("open_time").reset_index(drop=True)
    close = df["close"].to_numpy(dtype=np.float64)

    log_close = np.log(close)
    log_ret_1bar = np.concatenate([[np.nan], np.diff(log_close)])

    df["btc_ret_3d"] = np.concatenate([np.full(9, np.nan), log_close[9:] - log_close[:-9]])
    df["btc_ret_7d"] = np.concatenate([np.full(21, np.nan), log_close[21:] - log_close[:-21]])
    df["btc_ret_14d"] = np.concatenate([np.full(42, np.nan), log_close[42:] - log_close[:-42]])

    btc_vol = pd.Series(log_ret_1bar).rolling(42, min_periods=42).std().to_numpy() * np.sqrt(42)
    df["btc_vol_14d"] = btc_vol

    _BTC_CACHE_V3 = df[
        ["open_time", "btc_ret_3d", "btc_ret_7d", "btc_ret_14d", "btc_vol_14d"]
    ].copy()
    return _BTC_CACHE_V3


def add_cross_btc_v3_features(df: pd.DataFrame) -> pd.DataFrame:
    """Merge BTC-derived features into the symbol's feature frame."""
    btc = _load_btc_v3_features()

    df = df.copy()
    had_open_time_index = df.index.name == "open_time"
    if had_open_time_index:
        df = df.reset_index(drop=True)

    log_close = np.log(df["close"].to_numpy(dtype=np.float64))
    n = len(log_close)
    if n >= 21:
        sym_ret_7d = np.concatenate([np.full(21, np.nan), log_close[21:] - log_close[:-21]])
    else:
        sym_ret_7d = np.full(n, np.nan)
    df["_sym_ret_7d"] = sym_ret_7d

    merged = df.merge(btc, on="open_time", how="left")
    merged["sym_vs_btc_ret_7d"] = merged["_sym_ret_7d"] - merged["btc_ret_7d"]
    merged = merged.drop(columns=["_sym_ret_7d"])

    if had_open_time_index:
        merged = merged.set_index("open_time", drop=False)
        merged.index.name = "open_time"

    return merged
