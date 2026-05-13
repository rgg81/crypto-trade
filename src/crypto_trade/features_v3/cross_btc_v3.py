"""v3 BTC cross-asset features.

Track-isolated copy of v2's cross_btc.py. No imports from crypto_trade.features
or crypto_trade.features_v2 permitted in this file.

Features added:
    btc_ret_3d        — BTC log return over 3 days (9 x 8h bars)
    btc_ret_7d        — BTC log return over 7 days (21 x 8h bars)
    btc_ret_14d       — BTC log return over 14 days (42 x 8h bars)
    btc_vol_14d       — BTC 14-day realized vol (std of 1-bar log returns x sqrt(42))
    sym_vs_btc_ret_7d — symbol's 7-day log return minus BTC's 7-day log return
    sym_vs_btc_ret_3d — symbol's 3-day log return minus BTC's 3-day log return (iter-v3/063)
    sym_vs_btc_vol_14d — symbol 14d realized vol minus BTC 14d realized vol (iter-v3/063)
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


def _sym_vol_14d(log_close: np.ndarray) -> np.ndarray:
    """Compute 14-day realized vol from log returns (42 x 8h bars = 14 days)."""
    log_ret = np.concatenate([[np.nan], np.diff(log_close)])
    return pd.Series(log_ret).rolling(42, min_periods=42).std().to_numpy() * np.sqrt(42)


def add_cross_btc_v3_features(df: pd.DataFrame) -> pd.DataFrame:
    """Merge BTC-derived features into the symbol's feature frame.

    iter-v3/063: Added sym_vs_btc_ret_3d and sym_vs_btc_vol_14d.
        sym_vs_btc_ret_3d: shorter-horizon relative return (3-day vs 7-day).
            Mechanism: cross-sectional relative-strength signal at finer resolution.
            9-bar diff instead of 21-bar. Ref: Asness (1995) cross-sectional momentum.
        sym_vs_btc_vol_14d: relative vol (symbol 14d vol minus BTC 14d vol).
            Mechanism: vol divergence signal — when a symbol's vol spikes above BTC's,
            it may indicate idiosyncratic risk vs systematic risk.
            Both features are past-only (shift-based rolling windows; no future bars used).
    """
    btc = _load_btc_v3_features()

    df = df.copy()
    had_open_time_index = df.index.name == "open_time"
    if had_open_time_index:
        df = df.reset_index(drop=True)

    log_close = np.log(df["close"].to_numpy(dtype=np.float64))
    n = len(log_close)

    # 7-day relative return (21 bars)
    if n >= 21:
        sym_ret_7d = np.concatenate([np.full(21, np.nan), log_close[21:] - log_close[:-21]])
    else:
        sym_ret_7d = np.full(n, np.nan)
    df["_sym_ret_7d"] = sym_ret_7d

    # iter-v3/063: 3-day relative return (9 bars)
    if n >= 9:
        sym_ret_3d = np.concatenate([np.full(9, np.nan), log_close[9:] - log_close[:-9]])
    else:
        sym_ret_3d = np.full(n, np.nan)
    df["_sym_ret_3d"] = sym_ret_3d

    # iter-v3/063: 14-day realized vol (42 bars)
    sym_vol_14d = _sym_vol_14d(log_close)
    df["_sym_vol_14d"] = sym_vol_14d

    merged = df.merge(btc, on="open_time", how="left")
    merged["sym_vs_btc_ret_7d"] = merged["_sym_ret_7d"] - merged["btc_ret_7d"]
    # iter-v3/063: new cross-asset features
    merged["sym_vs_btc_ret_3d"] = merged["_sym_ret_3d"] - merged["btc_ret_3d"]
    merged["sym_vs_btc_vol_14d"] = merged["_sym_vol_14d"] - merged["btc_vol_14d"]
    merged = merged.drop(columns=["_sym_ret_7d", "_sym_ret_3d", "_sym_vol_14d"])

    if had_open_time_index:
        merged = merged.set_index("open_time", drop=False)
        merged.index.name = "open_time"

    return merged
