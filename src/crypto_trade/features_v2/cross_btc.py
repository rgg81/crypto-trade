"""iter-v2/026: BTC cross-asset features for the v2 feature catalog.

Adds BTC-derived context to each v2 symbol's feature row. The v2 track
has been lacking cross-asset features — the existing 35 features are all
intra-symbol (regime, tail risk, vol, momentum, volume, fracdiff). This
module adds BTC-relative context so the model can learn BTC regime
awareness at the feature level, complementing iter-v2/019's BTC trend
filter at the risk-gate level.

Features added:
- ``btc_ret_3d`` — BTC log return over 3 days (9 × 8h bars)
- ``btc_ret_7d`` — BTC log return over 7 days (21 × 8h bars)
- ``btc_ret_14d`` — BTC log return over 14 days (42 × 8h bars)
- ``btc_vol_14d`` — BTC 14-day realized volatility (std of 1-bar log returns × sqrt(42))
- ``sym_vs_btc_ret_7d`` — symbol's 7-day log return minus BTC's 7-day log return

All features are computed at each bar's ``open_time`` and aligned via a
left merge. Pre-history bars (where the lookback would read before the
series starts) get NaN and are handled by the model's own NaN-dropping
logic downstream.

**Important**: this module does NOT import from ``crypto_trade.features``
(the v1 package). It reads BTC's raw CSV data directly from
``data/BTCUSDT/8h.csv``. Per iter-v2/001's rules, cross-asset signals
as features are allowed as long as they don't reuse v1's feature
implementations.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

BTC_CSV_PATH = Path("data/BTCUSDT/8h.csv")

_BTC_CACHE: pd.DataFrame | None = None


def clear_btc_cache() -> None:
    """Invalidate the cached BTC features. See cross_v2sym.clear_peer_cache."""
    global _BTC_CACHE
    from crypto_trade import decision_log

    if _BTC_CACHE is not None and decision_log.is_configured():
        decision_log.log({"kind": "cache_clear", "cache": "btc"})
    _BTC_CACHE = None


def _load_btc_features() -> pd.DataFrame:
    """Load BTC 8h klines and precompute BTC-derived columns (cached)."""
    global _BTC_CACHE
    if _BTC_CACHE is not None:
        return _BTC_CACHE

    df = pd.read_csv(BTC_CSV_PATH).sort_values("open_time").reset_index(drop=True)
    close = df["close"].to_numpy(dtype=np.float64)

    log_close = np.log(close)
    log_ret_1bar = np.concatenate([[np.nan], np.diff(log_close)])

    df["btc_ret_3d"] = np.concatenate([np.full(9, np.nan), log_close[9:] - log_close[:-9]])
    df["btc_ret_7d"] = np.concatenate([np.full(21, np.nan), log_close[21:] - log_close[:-21]])
    df["btc_ret_14d"] = np.concatenate([np.full(42, np.nan), log_close[42:] - log_close[:-42]])

    # 14-day realized vol from 1-bar log returns (42 bars, sqrt-42 scale)
    btc_vol = pd.Series(log_ret_1bar).rolling(42, min_periods=42).std().to_numpy() * np.sqrt(42)
    df["btc_vol_14d"] = btc_vol

    _BTC_CACHE = df[["open_time", "btc_ret_3d", "btc_ret_7d", "btc_ret_14d", "btc_vol_14d"]].copy()

    from crypto_trade import decision_log

    if decision_log.is_configured():
        decision_log.log(
            {
                "kind": "cache_load",
                "cache": "btc",
                "max_open_time": int(_BTC_CACHE["open_time"].max()) if len(_BTC_CACHE) else None,
            }
        )
    return _BTC_CACHE


def add_cross_btc_features(df: pd.DataFrame) -> pd.DataFrame:
    """Merge BTC-derived features into the symbol's feature frame.

    Also computes ``sym_vs_btc_ret_7d`` as the symbol's own 7-day log
    return minus BTC's 7-day log return, a direct "relative strength"
    feature the model can use to decide whether the symbol is
    out/under-performing the market.
    """
    btc = _load_btc_features()

    df = df.copy()
    # Earlier feature groups may have set open_time as an index while
    # keeping it as a column too. Drop the index to avoid merge ambiguity;
    # restore at the end if needed.
    had_open_time_index = df.index.name == "open_time"
    if had_open_time_index:
        df = df.reset_index(drop=True)
    # Symbol's own 7-day log return (same 21-bar lookback as BTC)
    log_close = np.log(df["close"].to_numpy(dtype=np.float64))
    n = len(log_close)
    if n >= 21:
        sym_ret_7d = np.concatenate([np.full(21, np.nan), log_close[21:] - log_close[:-21]])
    else:
        sym_ret_7d = np.full(n, np.nan)
    df["_sym_ret_7d"] = sym_ret_7d

    # Left-merge BTC features by open_time
    merged = df.merge(btc, on="open_time", how="left")

    # Symbol-vs-BTC relative 7-day return
    merged["sym_vs_btc_ret_7d"] = merged["_sym_ret_7d"] - merged["btc_ret_7d"]
    merged = merged.drop(columns=["_sym_ret_7d"])

    # Restore original index if needed
    if had_open_time_index:
        merged = merged.set_index("open_time", drop=False)
        merged.index.name = "open_time"

    return merged
