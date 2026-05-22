"""v3 perp-spot BASIS features — iter-v3/086 cycle-3 EXPLORATION #5.

Track-isolated: zero imports from crypto_trade.features (v1) or
crypto_trade.features_v2 (v2).

The BASIS is the canonical sentiment primitive of a perpetual market:

    basis(t)  =  (perp_close[t] - spot_close[t]) / spot_close[t]

A persistently positive basis signals leveraged-long crowding; a negative
basis signals leveraged-short positioning.  Unlike the funding rate — which
settles every 8h on a lag and is clamped at Binance's +/- floor — the basis
reprices continuously and is unclamped, so it carries a faster, less-saturated
crowding signal.  The 2024-2025 perpetual-futures literature (Ackerer-Hugonnier-
Jermann "Perpetual Futures Pricing", Mathematical Finance; the AEA 2026
"Perpetual Futures and Basis Risk" empirical paper) treats the basis as the
directly-observable deviation the premium mechanism mean-reverts.

This is a NEW crypto-native data feed for v3 — every prior v3 feature is derived
from OHLCV or the funding rate.  The basis requires SPOT 8h klines, a feed v3
has never fetched.  It is genuinely distinct from the CLOSED v3 funding axis
(/019/023/024/082/085): IS corr(basis_z, funding_z) is only 0.22-0.28 (funding
is the lagged clamped settlement, the basis is the continuous unclamped premium).

Data source:
    ``data/spot/<SYMBOL>/8h.csv`` — spot 8h klines, 11-column kline schema,
    written by ``uv run crypto-trade fetch-spot`` (the Phase-6 productionised
    fetcher; the iter-v3/086 QR prototype is
    ``analysis/iteration_v3-086/fetch_spot_klines.py``).

Look-ahead discipline (STRICTER than funding):
    perp_close[t] AND spot_close[t] both settle at candle ``close_time(t)``.
    The basis(t) is therefore knowable only at bar t CLOSE, NOT at bar t open.
    Every basis feature is computed on ``basis.shift(1)`` — bar t's decision
    uses basis[t-1] (the previous fully-closed candle) and earlier ONLY.
    This is a STRICTER one-candle lag than the funding convention (funding
    broadcasts ~5 min before settlement, so funding_rate[t] is knowable at bar
    t open).  ``tests/features_v3/test_basis_v3.py`` enforces this invariant
    with an adversarial spike-perturbation test.

Outlier clipping:
    ``basis_zscore_30`` is clipped to [-10, 10] (the funding_v3.py ZSCORE_CLIP
    convention) to prevent LightGBM training instability when a degenerate
    flat-basis window drives the rolling std -> 0.

Three features (iter-v3/086 brief Section 3.1):
    basis_zscore_30     — crowding LEVEL  (30-bar past-only z-score of basis)
    basis_momentum_3    — crowding MOMENTUM  (3-bar change of the lagged basis)
    basis_extreme_flag  — crowding DIRECTION + PERSISTENCE
                          (sign(basis).shift(1).rolling(9).mean())
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# Default rolling window: 30 8h-candles = 10 days (= funding_v3.FUNDING_ZSCORE_WINDOW;
# the funding-settlement-cycle convention — re-used a-priori, NOT swept).
BASIS_ZSCORE_WINDOW: int = 30

# 3-bar (1-day) basis momentum; 9-bar (3-day) sign-persistence window.
# Re-used a-priori from the /082 funding-family construction (funding_momentum_3 /
# funding_sign_persist_9) — NOT swept on any metric.
BASIS_MOMENTUM_WINDOW: int = 3
BASIS_PERSIST_WINDOW: int = 9

# Clip the basis z-score (funding_v3.ZSCORE_CLIP convention) to bound a
# degenerate flat-basis window's z-score blow-up.
ZSCORE_CLIP: float = 10.0

_DEFAULT_DATA_DIR: Path = Path("data")

BASIS_FAMILY_COLUMNS: tuple[str, ...] = (
    "basis_zscore_30",
    "basis_momentum_3",
    "basis_extreme_flag",
)


def compute_basis_features(
    df: pd.DataFrame,
    spot_df: pd.DataFrame,
    zscore_window: int = BASIS_ZSCORE_WINDOW,
    momentum_window: int = BASIS_MOMENTUM_WINDOW,
    persist_window: int = BASIS_PERSIST_WINDOW,
    clip: float = ZSCORE_CLIP,
) -> pd.DataFrame:
    """Merge spot closes into the perp kline frame and add the 3 basis features.

    Parameters
    ----------
    df:
        Perp kline DataFrame with at least ``open_time`` and ``close`` columns.
        ``df['close']`` is the perp close.
    spot_df:
        Spot kline DataFrame with ``open_time`` and ``close`` columns, as
        written by the ``fetch-spot`` CLI.  ``spot_df['close']`` is the spot
        close.
    zscore_window:
        Rolling window in bars for ``basis_zscore_30`` (default 30 = ~10 days).
    momentum_window:
        Lag in bars for ``basis_momentum_3`` (default 3 = ~1 day).
    persist_window:
        Rolling window in bars for ``basis_extreme_flag`` (default 9 = ~3 days).
    clip:
        Absolute clip threshold for ``basis_zscore_30`` (default 10.0).

    Returns
    -------
    pd.DataFrame
        Input df with the 3 ``BASIS_FAMILY_COLUMNS`` appended.  Rows with no
        matching spot candle (start of listing) get NaN.

    Notes
    -----
    Look-ahead discipline: basis(t) = (perp_close[t] - spot_close[t]) /
    spot_close[t] is knowable only at bar t CLOSE (both closes settle at
    close_time(t)).  Every feature below is computed on ``basis.shift(1)`` — bar
    t's feature uses basis[t-1] and earlier ONLY.
    """
    df = df.copy()
    had_open_time_index = df.index.name == "open_time"
    if had_open_time_index:
        df = df.reset_index(drop=True)

    # ------------------------------------------------------------------
    # Step 1: left-merge perp -> spot on open_time, bring in spot close.
    # ------------------------------------------------------------------
    spot = spot_df[["open_time", "close"]].rename(columns={"close": "_spot_close"})
    merged = df.merge(spot, on="open_time", how="left")
    merged.index = df.index

    # ------------------------------------------------------------------
    # Step 2: raw basis — knowable at candle CLOSE (both closes settle there).
    # ------------------------------------------------------------------
    perp_close = merged["close"].astype(float)
    spot_close = merged["_spot_close"].astype(float)
    basis = (perp_close - spot_close) / spot_close.replace(0, np.nan)

    # ------------------------------------------------------------------
    # Step 3: PAST-ONLY — shift basis one full candle before ALL stats.
    # ------------------------------------------------------------------
    b = basis.shift(1)

    # F1 — basis_zscore_30: 30-bar past-only z-score of the basis.
    rmean = b.rolling(window=zscore_window, min_periods=zscore_window).mean()
    rstd = b.rolling(window=zscore_window, min_periods=zscore_window).std(ddof=1)
    z = (b - rmean) / rstd.replace(0, np.nan)
    merged["basis_zscore_30"] = z.clip(-clip, clip)

    # F2 — basis_momentum_3: 3-bar change of the (already-lagged) basis.
    merged["basis_momentum_3"] = b - b.shift(momentum_window)

    # F3 — basis_extreme_flag: sign-persistence over 9 bars of the lagged basis.
    merged["basis_extreme_flag"] = (
        np.sign(b).rolling(window=persist_window, min_periods=persist_window).mean()
    )

    merged = merged.drop(columns=["_spot_close"])

    if had_open_time_index:
        merged = merged.set_index("open_time", drop=False)
        merged.index.name = "open_time"

    return merged


def add_basis_v3_features(
    df: pd.DataFrame,
    data_dir: Path | str = _DEFAULT_DATA_DIR,
) -> pd.DataFrame:
    """Load cached SPOT klines for *df*'s symbol and add the 3 basis features.

    This is the GROUP_REGISTRY entry point.  It reads the
    ``data/spot/<SYMBOL>/8h.csv`` cache file (populated by
    ``uv run crypto-trade fetch-spot``).

    Parameters
    ----------
    df:
        Perp kline DataFrame with ``symbol``, ``open_time`` and ``close``.
    data_dir:
        Root data directory (default ``data/``).

    Returns
    -------
    pd.DataFrame
        Input df with the 3 ``BASIS_FAMILY_COLUMNS`` appended.

    Raises
    ------
    KeyError
        If ``df`` does not contain the ``symbol`` column.
    FileNotFoundError
        If the spot-kline cache for the symbol does not exist.
        Run ``uv run crypto-trade fetch-spot --symbols <SYMBOL>`` first.
    """
    data_dir = Path(data_dir)

    symbol = df["symbol"].iloc[0] if "symbol" in df.columns else None
    if symbol is None:
        raise KeyError(
            "df must contain a 'symbol' column for the basis_v3 feature group. "
            "Set df['symbol'] = '<SYMBOL>' before calling add_basis_v3_features."
        )

    cache_path = data_dir / "spot" / symbol / "8h.csv"
    if not cache_path.exists():
        raise FileNotFoundError(
            f"Spot-kline cache not found: {cache_path}. "
            f"Run: uv run crypto-trade fetch-spot --symbols {symbol}"
        )

    spot_df = pd.read_csv(cache_path)
    if len(spot_df) == 0:
        # Empty cache — add NaN columns and return.
        df = df.copy()
        for col in BASIS_FAMILY_COLUMNS:
            df[col] = np.nan
        return df

    return compute_basis_features(df, spot_df)
