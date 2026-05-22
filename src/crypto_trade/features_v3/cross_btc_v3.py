"""v3 BTC and ETH cross-asset features.

Track-isolated copy of v2's cross_btc.py. No imports from crypto_trade.features
or crypto_trade.features_v2 permitted in this file.

Features added:
    btc_ret_3d           — BTC log return over 3 days (9 x 8h bars)
    btc_ret_7d           — BTC log return over 7 days (21 x 8h bars)
    btc_ret_14d          — BTC log return over 14 days (42 x 8h bars)
    btc_vol_14d          — BTC 14-day realized vol (std of 1-bar log returns x sqrt(42))
    sym_vs_btc_ret_7d    — symbol's 7-day log return minus BTC's 7-day log return
    sym_vs_btc_ret_3d    — symbol's 3-day log return minus BTC's 3-day log return (iter-v3/063)
    sym_vs_btc_vol_14d   — symbol 14d realized vol minus BTC 14d realized vol (iter-v3/063)
    eth_vs_sym_rv_50     — ETH realized-vol-50 / symbol realized-vol-50 ratio (iter-v3/123)
                           eth_ret_3d (iter-v3/122) REMOVED per /122 NEGATIVE-INERT verdict.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

BTC_CSV_PATH = Path("data/BTCUSDT/8h.csv")
ETH_CSV_PATH = Path("data/ETHUSDT/8h.csv")

_BTC_CACHE_V3: pd.DataFrame | None = None
_ETH_CACHE_V3: pd.DataFrame | None = None


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


def _load_eth_v3_features() -> pd.DataFrame:
    """Load ETH 8h klines and precompute ETH realized-vol-50 (cached).

    iter-v3/123: Replaces eth_ret_3d (closed at /122 NEGATIVE-INERT) with
    eth_rv_50 = rolling(50, min_periods=50).std() of ETH 1-bar log returns.
    Past-only by construction: rolling.std with min_periods=W uses ONLY the
    prior W bars at each timestamp — no future bars are accessed.

    ETH klines source: data/ETHUSDT/8h.csv (same fetcher convention as BTC).
    Merge key: open_time (same convention as BTC merge).

    eth_rv_50 is an intermediate column — it is NOT added to the symbol frame
    directly. The ratio eth_vs_sym_rv_50 = eth_rv_50 / (sym_rv_50 + EPS) is
    computed inside add_cross_btc_v3_features() after the left-join.
    """
    global _ETH_CACHE_V3
    if _ETH_CACHE_V3 is not None:
        return _ETH_CACHE_V3

    df = pd.read_csv(ETH_CSV_PATH).sort_values("open_time").reset_index(drop=True)
    close = df["close"].to_numpy(dtype=np.float64)

    log_close = np.log(close)
    # 1-bar log returns: first bar is NaN (no prior bar)
    log_ret_1bar = np.concatenate([[np.nan], np.diff(log_close)])

    # eth_rv_50 = rolling(50, min_periods=50).std() of 1-bar log returns
    # First 49 bars are NaN (insufficient history for 50-bar window).
    df["eth_rv_50"] = pd.Series(log_ret_1bar).rolling(50, min_periods=50).std().to_numpy()

    _ETH_CACHE_V3 = df[["open_time", "eth_rv_50"]].copy()
    return _ETH_CACHE_V3


def clear_btc_cache_v3() -> None:
    """Invalidate the v3 BTC features cache.

    Mirrors ``features_v2.cross_btc.clear_btc_cache`` (commit 62d56dc).
    Called at the start of every ``run_features_v3()`` invocation so live
    ticks re-read the latest BTCUSDT/8h.csv data (which the engine refreshes
    each tick). Without this, cross_btc_v3 features go stale on tick #2+ and
    live↔backtest determinism breaks.
    """
    global _BTC_CACHE_V3
    if _BTC_CACHE_V3 is not None:
        try:
            from crypto_trade import decision_log

            if decision_log.is_configured():
                decision_log.log({"kind": "cache_clear", "cache": "btc_v3"})
        except Exception:
            pass  # decision_log is best-effort instrumentation
    _BTC_CACHE_V3 = None


def clear_eth_cache_v3() -> None:
    """Invalidate the v3 ETH features cache.

    Same hygiene contract as ``clear_btc_cache_v3``. eth_vs_sym_rv_50 was
    REMOVED from V3_FEATURE_COLUMNS_TOP_N at iter-v3/124, but
    ``_load_eth_v3_features`` is still called unconditionally inside
    ``add_cross_btc_v3_features`` (the merge happens even though the
    feature isn't trained on). The cache must still be cleared to avoid
    serving stale ETH data to the merge.
    """
    global _ETH_CACHE_V3
    if _ETH_CACHE_V3 is not None:
        try:
            from crypto_trade import decision_log

            if decision_log.is_configured():
                decision_log.log({"kind": "cache_clear", "cache": "eth_v3"})
        except Exception:
            pass
    _ETH_CACHE_V3 = None


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
    iter-v3/123: Added eth_vs_sym_rv_50 — ETH-vs-symbol 50-bar realized-vol ratio.
        eth_vs_sym_rv_50 = eth_rv_50 / (range_realized_vol_50 + EPS).
        ETH realized vol: rolling(50, min_periods=50).std() of ETH 1-bar log returns.
        Symbol realized vol: range_realized_vol_50 (pre-computed in the parquet panel
            by multioffset_24h.py — same rolling(50, min_periods=50).std() convention).
        Ratio semantics: > 1 means ETH regime is more volatile than the symbol;
            < 1 means symbol is more volatile than ETH. Cross-asset regime classifier.
        Past-only: rolling.std uses only prior bars; ETH klines merged on open_time.
        Source: data/ETHUSDT/8h.csv; left-join on open_time (same convention as BTC).
        eth_ret_3d (iter-v3/122) REMOVED — /122 NEGATIVE-INERT verdict (Critic `9e0eeb6`).
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

    # iter-v3/123: ETH-vs-symbol realized-vol ratio — left-join on open_time
    # eth_rv_50 is the intermediate ETH realized vol; it is dropped after ratio computation.
    eth = _load_eth_v3_features()
    merged = merged.merge(eth, on="open_time", how="left")

    # Compute ratio: eth_rv_50 / (range_realized_vol_50 + EPS).
    # range_realized_vol_50 is the symbol's own 50-bar realized vol, already present
    # in the parquet panel (computed by multioffset_24h.py with the same rolling-std
    # convention). EPS = 1e-12 guards against division-by-zero on degenerate vol values.
    _eps = 1e-12
    merged["eth_vs_sym_rv_50"] = merged["eth_rv_50"] / (merged["range_realized_vol_50"] + _eps)

    # Drop the intermediate ETH realized-vol column (not a model feature).
    merged = merged.drop(columns=["eth_rv_50"])

    if had_open_time_index:
        merged = merged.set_index("open_time", drop=False)
        merged.index.name = "open_time"

    return merged
