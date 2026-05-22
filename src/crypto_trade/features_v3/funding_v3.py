"""v3 funding-rate features — per-symbol (iter-v3/019) + cross-asset BTC (iter-v3/024).

Track-isolated: zero imports from crypto_trade.features (v1) or crypto_trade.features_v2 (v2).

Funding rate is the canonical economic primitive of Binance Futures perpetual markets.
Every 8h at 00/08/16 UTC, longs pay shorts (positive funding) or shorts pay longs
(negative funding).  Persistent positive funding signals leveraged-long crowding with
mean-reversion / liquidation-cascade pressure (BIS WP 1087, 2025: 10% carry shock →
22% liquidation jump).  The z-score over a 30-bar (10-day) window normalises per-symbol
baselines and is scale-invariant across the BCH/LDO/TRX pooled model.

Data source:
    ``data/funding_rates/<SYMBOL>.csv`` — cached CSV from /fapi/v1/fundingRate.
    Schema: ``funding_time`` (ms epoch int), ``funding_rate`` (float).
    The fetcher (``uv run crypto-trade fetch-funding``) writes this file.

Look-ahead discipline:
    The funding rate AT bar t is the rate that SETTLED at candle open_time T
    (knowable from the previous 8h period close).  Past-only is implemented by
    shifting the rolling-window stats by 1 bar:

        bar t z-score  =  (rate[t] - mean(rate[t-30]...rate[t-1]))
                          / std(rate[t-30]...rate[t-1])

    ``rate[t]`` is the rate that settled AT t (broadcast 5 min before settlement,
    so fully knowable at bar t open).  The rolling denominator uses ONLY t-30…t-1
    via ``.shift(1)`` — no bar t data enters the denominator.

    Unit-test ``tests/features_v3/test_funding_v3.py`` enforces this invariant.

Outlier clipping:
    When funding is clamped at Binance's floor for >30 consecutive bars,
    the rolling std → 0 and z-score → ±∞.  We clip to [-10, 10] to prevent
    LightGBM training instability (per iter-v3/019 brief §2.3 outlier note).

Verifier (Phase 6 sub-fix #1):
    python -c "
    from crypto_trade.features_v3.funding_v3 import add_funding_v3_features
    import pandas as pd
    df = pd.read_csv('data/BCHUSDT/8h.csv')
    df['symbol'] = 'BCHUSDT'
    df2 = add_funding_v3_features(df)
    assert 'funding_rate_zscore_30' in df2.columns
    assert df2['funding_rate_zscore_30'].notna().mean() > 0.95
    print('OK')
    "
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# Default rolling window: 30 funding cycles = 10 days at 8h cadence
FUNDING_ZSCORE_WINDOW: int = 30

# Clip z-scored output to prevent LightGBM instability from funding-floor outliers
# (see brief §2.3 outlier note: small number of bars have |z| > 100 when
# rolling std → 0 during Binance's +0.0001 clamping regime)
ZSCORE_CLIP: float = 10.0

# Default data directory for funding-rate cache
_DEFAULT_DATA_DIR: Path = Path("data")


def compute_funding_rate_zscore(
    df: pd.DataFrame,
    funding_df: pd.DataFrame,
    window: int = FUNDING_ZSCORE_WINDOW,
    clip: float = ZSCORE_CLIP,
) -> pd.DataFrame:
    """Merge funding rates into kline frame and compute rolling z-score.

    Parameters
    ----------
    df:
        Kline DataFrame with at least ``open_time`` (ms int) column.
        Must NOT already contain a ``funding_rate`` column — this function
        adds it via merge and then drops it.
    funding_df:
        DataFrame with columns ``funding_time`` (ms int) and
        ``funding_rate`` (float), as written by the ``fetch-funding`` CLI.
    window:
        Rolling window in bars (default 30 = ~10 days at 8h cadence).
    clip:
        Absolute clip threshold for the z-scored output (default 10.0).

    Returns
    -------
    pd.DataFrame
        Input df with ``funding_rate_zscore_30`` column appended.
        Rows that cannot match a funding record (start of listing) get NaN.

    Notes
    -----
    Look-ahead discipline: the z-score at bar t uses ONLY rates t-window…t-1
    for the rolling denominator (via ``.shift(1)``).  The numerator uses
    ``rate[t]`` which settled at candle open_time T (past-only by construction
    — the settlement is broadcast 5 min before the 8h boundary).

    Alignment: funding settles at exactly 00/08/16 UTC, identical to v3's 8h
    kline open_times.  We round both timestamps to the nearest minute
    (//60000*60000) to absorb Binance's ~10-15ms settlement jitter.
    """
    df = df.copy()

    # ------------------------------------------------------------------
    # Step 1: align timestamps (round to nearest minute to handle jitter)
    # ------------------------------------------------------------------
    funding = funding_df.copy()
    funding["open_time_aligned"] = (funding["funding_time"] // 60_000) * 60_000
    df["open_time_aligned"] = (df["open_time"] // 60_000) * 60_000

    # ------------------------------------------------------------------
    # Step 2: left-merge kline → funding on rounded open_time
    # ------------------------------------------------------------------
    merged = df.merge(
        funding[["open_time_aligned", "funding_rate"]],
        on="open_time_aligned",
        how="left",
    ).drop(columns=["open_time_aligned"])

    # Restore original index alignment
    merged.index = df.index

    # ------------------------------------------------------------------
    # Step 3: compute past-only rolling z-score
    # ------------------------------------------------------------------
    s = merged["funding_rate"].astype(float)

    # Rolling stats lagged by 1 bar: at bar t, mean/std use t-window…t-1 only
    s_shifted = s.shift(1)
    rmean = s_shifted.rolling(window=window, min_periods=window).mean()
    rstd = s_shifted.rolling(window=window, min_periods=window).std(ddof=1)

    # Numerator: rate[t] (settled at bar t open — past-only by funding broadcast convention)
    zscore = (s - rmean) / rstd.replace(0, np.nan)

    # Clip to prevent LightGBM instability from funding-floor outliers
    zscore = zscore.clip(lower=-clip, upper=clip)

    df["funding_rate_zscore_30"] = zscore.values

    return df


def compute_btc_funding_rate_zscore(
    df: pd.DataFrame,
    funding_df: pd.DataFrame,
    window: int = FUNDING_ZSCORE_WINDOW,
    clip: float = ZSCORE_CLIP,
) -> pd.DataFrame:
    """Merge BTC funding rates into kline frame and broadcast cross-asset z-score.

    Identical z-score computation to ``compute_funding_rate_zscore`` but the
    result is labelled ``btc_funding_rate_zscore_30`` and carries BTC's funding
    stress signal regardless of which symbol *df* belongs to.  At any given
    ``open_time`` the column value is IDENTICAL across BCH/LDO/TRX kline frames
    — the broadcast invariant is the key architectural difference vs the per-symbol
    variant from iter-v3/019/023.

    Parameters
    ----------
    df:
        Kline DataFrame with at least ``open_time`` (ms int) column.
        May belong to any symbol; the BTC funding signal is broadcast.
    funding_df:
        DataFrame with columns ``funding_time`` (ms int) and
        ``funding_rate`` (float) from ``data/funding_rates/BTCUSDT.csv``.
    window:
        Rolling window in bars (default 30 = ~10 days at 8h cadence).
    clip:
        Absolute clip threshold for the z-scored output (default 10.0).

    Returns
    -------
    pd.DataFrame
        Input df with ``btc_funding_rate_zscore_30`` column appended.
        Rows that cannot match a BTC funding record get NaN.

    Notes
    -----
    Look-ahead discipline: identical to ``compute_funding_rate_zscore``.
    The z-score at bar t uses ONLY BTC rates t-window…t-1 for the rolling
    denominator (via ``.shift(1)``).  The numerator uses rate[t] which
    settled at candle open_time T (past-only by funding broadcast convention).

    Broadcast invariant: since this function reads BTC funding data
    (not per-symbol data), calling it on BCH, LDO, or TRX kline frames
    with the same BTC funding_df produces identical column values at
    matching open_times — verified in the adversarial test suite.
    """
    df = df.copy()

    # ------------------------------------------------------------------
    # Step 1: align timestamps (round to nearest minute to handle jitter)
    # ------------------------------------------------------------------
    funding = funding_df.copy()
    funding["open_time_aligned"] = (funding["funding_time"] // 60_000) * 60_000
    df["open_time_aligned"] = (df["open_time"] // 60_000) * 60_000

    # ------------------------------------------------------------------
    # Step 2: left-merge kline → BTC funding on rounded open_time
    # ------------------------------------------------------------------
    merged = df.merge(
        funding[["open_time_aligned", "funding_rate"]],
        on="open_time_aligned",
        how="left",
    ).drop(columns=["open_time_aligned"])

    # Restore original index alignment
    merged.index = df.index

    # ------------------------------------------------------------------
    # Step 3: compute past-only rolling z-score (identical math to
    #         compute_funding_rate_zscore, different output column name)
    # ------------------------------------------------------------------
    s = merged["funding_rate"].astype(float)

    # Rolling stats lagged by 1 bar: at bar t, mean/std use t-window…t-1 only
    s_shifted = s.shift(1)
    rmean = s_shifted.rolling(window=window, min_periods=window).mean()
    rstd = s_shifted.rolling(window=window, min_periods=window).std(ddof=1)

    # Numerator: rate[t] (settled at bar t open — past-only by funding broadcast convention)
    zscore = (s - rmean) / rstd.replace(0, np.nan)

    # Clip to prevent LightGBM instability from funding-floor outliers
    zscore = zscore.clip(lower=-clip, upper=clip)

    df["btc_funding_rate_zscore_30"] = zscore.values

    return df


def add_btc_funding_v3_features(
    df: pd.DataFrame,
    data_dir: Path | str = _DEFAULT_DATA_DIR,
    window: int = FUNDING_ZSCORE_WINDOW,
    clip: float = ZSCORE_CLIP,
) -> pd.DataFrame:
    """Load BTC funding cache and broadcast cross-asset z-score to any symbol's kline frame.

    This is the GROUP_REGISTRY entry point for the ``btc_funding_v3`` group
    (iter-v3/024).  Unlike ``add_funding_v3_features`` (which reads the per-symbol
    cache), this function ALWAYS reads ``data/funding_rates/BTCUSDT.csv``
    regardless of which symbol *df* represents.  The resulting
    ``btc_funding_rate_zscore_30`` column carries BTC's funding stress signal
    broadcast identically to BCH/LDO/TRX training datasets.

    Parameters
    ----------
    df:
        Kline DataFrame with ``open_time`` column.  Symbol column optional
        (not read by this function — BTC funding is always used).
    data_dir:
        Root data directory (default ``data/``).
    window:
        Rolling window in bars (default 30).
    clip:
        Z-score clip threshold (default 10.0).

    Returns
    -------
    pd.DataFrame
        Input df with ``btc_funding_rate_zscore_30`` column appended.

    Raises
    ------
    FileNotFoundError
        If the BTC funding-rate cache does not exist.
        Run ``uv run crypto-trade fetch-funding --symbols BTCUSDT`` first.
    """
    data_dir = Path(data_dir)

    btc_cache_path = data_dir / "funding_rates" / "BTCUSDT.csv"
    if not btc_cache_path.exists():
        raise FileNotFoundError(
            f"BTC funding-rate cache not found: {btc_cache_path}. "
            "Run: uv run crypto-trade fetch-funding --symbols BTCUSDT"
        )

    funding_df = pd.read_csv(btc_cache_path)
    if len(funding_df) == 0:
        # Empty cache — add NaN column and return
        df = df.copy()
        df["btc_funding_rate_zscore_30"] = np.nan
        return df

    return compute_btc_funding_rate_zscore(df, funding_df, window=window, clip=clip)


def add_funding_v3_features(
    df: pd.DataFrame,
    data_dir: Path | str = _DEFAULT_DATA_DIR,
    window: int = FUNDING_ZSCORE_WINDOW,
    clip: float = ZSCORE_CLIP,
) -> pd.DataFrame:
    """Load cached funding rates for *df*'s symbol and add ``funding_rate_zscore_30``.

    This function is the GROUP_REGISTRY entry point.  It reads the
    ``data/funding_rates/<SYMBOL>.csv`` cache file (populated by
    ``uv run crypto-trade fetch-funding``).

    Parameters
    ----------
    df:
        Kline DataFrame with ``symbol`` and ``open_time`` columns.
    data_dir:
        Root data directory (default ``data/``).
    window:
        Rolling window in bars (default 30).
    clip:
        Z-score clip threshold (default 10.0).

    Returns
    -------
    pd.DataFrame
        Input df with ``funding_rate_zscore_30`` column appended.

    Raises
    ------
    FileNotFoundError
        If the funding-rate cache for the symbol does not exist.
        Run ``uv run crypto-trade fetch-funding --symbols <SYMBOL>`` first.
    KeyError
        If ``df`` does not contain the ``symbol`` column.
    """
    data_dir = Path(data_dir)

    symbol = df["symbol"].iloc[0] if "symbol" in df.columns else None
    if symbol is None:
        raise KeyError(
            "df must contain a 'symbol' column for funding_v3 feature group. "
            "Set df['symbol'] = '<SYMBOL>' before calling add_funding_v3_features."
        )

    cache_path = data_dir / "funding_rates" / f"{symbol}.csv"
    if not cache_path.exists():
        raise FileNotFoundError(
            f"Funding-rate cache not found: {cache_path}. "
            f"Run: uv run crypto-trade fetch-funding --symbols {symbol}"
        )

    funding_df = pd.read_csv(cache_path)
    if len(funding_df) == 0:
        # Empty cache — add NaN column and return
        df = df.copy()
        df["funding_rate_zscore_30"] = np.nan
        return df

    return compute_funding_rate_zscore(df, funding_df, window=window, clip=clip)


# =====================================================================
# iter-v3/082 — funding-rate FEATURE FAMILY (cycle-3 EXPLORATION #1).
#
# This is a DIFFERENT axis from the PERMANENTLY-CLOSED single-feature
# funding_rate_zscore_30 (iter-v3/019/023/024 — rank 14/14 at every Optuna
# budget).  A mean-zero rolling z-score discards the SIGN, the LEVEL, and the
# price leg — the three properties the 2023-2025 funding literature identifies
# as carrying funding's predictive content:
#   - BIS WP 1087 (2025): carry SHOCKS, not carry levels, predict liquidation
#     jumps  -> funding_accel_3 (the second-difference / carry-shock proxy).
#   - MDPI Mathematics 14(2):346 (2025): persistent funding regimes encode
#     positioning crowding  -> funding_sign_persist_9 (sign persistence).
#   - CFB Benchmarks / funding-as-sentiment crowding-reversal literature: price
#     stalls while funding stays extended = the "crowded at the high" unwind
#     setup  -> funding_price_divergence_6 (funding-crowding-minus-price-progress).
#
# The funding_rate_zscore_30 / btc_funding_rate_zscore_30 columns and their
# runner pre-flight bans are UNCHANGED — the closed single-z-score axis stays
# closed.  The family uses four entirely distinct names.
#
# Brief: briefs-v3/iteration_v3-082/research_brief.md Section 3.
# EDA:   analysis/iteration_v3-082/funding_family_eda.py (SHA 37d4da8).
# =====================================================================

# Family window constants (8h cadence: 3 bars/day).
FUNDING_MOMENTUM_WINDOW: int = 3      # 1-day funding momentum
FUNDING_PERSIST_WINDOW: int = 9       # 3-day sign-persistence window
FUNDING_DIVERGENCE_WINDOW: int = 6    # 2-day funding-price divergence window
FUNDING_DIVERGENCE_NORM: int = 60     # z-score normalisation history for divergence

FUNDING_FAMILY_COLUMNS: tuple[str, ...] = (
    "funding_sign_persist_9",
    "funding_momentum_3",
    "funding_accel_3",
    "funding_price_divergence_6",
)


def compute_funding_family(
    df: pd.DataFrame,
    funding_df: pd.DataFrame,
    clip: float = ZSCORE_CLIP,
) -> pd.DataFrame:
    """Merge funding rates into kline frame and build the 4-member funding family.

    Parameters
    ----------
    df:
        Kline DataFrame with at least ``open_time`` (ms int) and ``close``.
    funding_df:
        DataFrame with ``funding_time`` (ms int) and ``funding_rate`` (float).
    clip:
        Absolute clip threshold for the divergence z-difference (default 10.0).

    Returns
    -------
    pd.DataFrame
        Input df with the 4 ``FUNDING_FAMILY_COLUMNS`` appended.

    Notes
    -----
    Look-ahead discipline (identical convention to ``compute_funding_rate_zscore``).
    The funding rate AT bar t SETTLED at candle open_time T and is broadcast
    ~5 min before the 8h boundary — ``rate[t]`` is knowable at bar t open. Every
    rolling stat is ``.shift(1)``-lagged so bar t's own settlement never enters
    its own rolling window/denominator.

      - funding_sign_persist_9   = mean(sign(rate).shift(1)) over 9 bars
      - funding_momentum_3       = rate[t] - rate[t-3]
      - funding_accel_3          = momentum_3[t] - momentum_3[t-3]
      - funding_price_divergence_6 = z(cum-funding-6, 60) - z(price-return-6, 60)

    All four are past-only; ``tests/features_v3/test_funding_family_v3.py``
    enforces the invariant by spike-perturbation.
    """
    df = df.copy()

    # Align timestamps (round to minute to absorb Binance settlement jitter)
    funding = funding_df.copy()
    funding["open_time_aligned"] = (funding["funding_time"] // 60_000) * 60_000
    df["open_time_aligned"] = (df["open_time"] // 60_000) * 60_000
    merged = df.merge(
        funding[["open_time_aligned", "funding_rate"]],
        on="open_time_aligned",
        how="left",
    ).drop(columns=["open_time_aligned"])
    merged.index = df.index
    r = merged["funding_rate"].astype(float)

    # --- funding_sign_persist_9 -------------------------------------------
    # Net sign agreement over the trailing 9 settlements (3 days). Encodes
    # crowding DIRECTION + PERSISTENCE. Past-only: .shift(1) -> window [t-9, t-1].
    sign = np.sign(r)
    df["funding_sign_persist_9"] = (
        sign.shift(1)
        .rolling(FUNDING_PERSIST_WINDOW, min_periods=FUNDING_PERSIST_WINDOW)
        .mean()
        .values
    )

    # --- funding_momentum_3 -----------------------------------------------
    # 1-day funding momentum. rate[t] past-only by broadcast; rate[t-3] trivial.
    mom = r - r.shift(FUNDING_MOMENTUM_WINDOW)
    df["funding_momentum_3"] = mom.values

    # --- funding_accel_3 --------------------------------------------------
    # Funding acceleration (second difference / carry-shock proxy; BIS WP 1087).
    df["funding_accel_3"] = (mom - mom.shift(FUNDING_MOMENTUM_WINDOW)).values

    # --- funding_price_divergence_6 ---------------------------------------
    # The "crowded at the high" reversal setup. z(trailing-6-bar cumulative
    # funding) minus z(trailing-6-bar price return); both legs .shift(1)-lagged.
    cum_fund = (
        r.shift(1)
        .rolling(FUNDING_DIVERGENCE_WINDOW, min_periods=FUNDING_DIVERGENCE_WINDOW)
        .sum()
    )
    cf_mean = cum_fund.rolling(FUNDING_DIVERGENCE_NORM, min_periods=FUNDING_DIVERGENCE_NORM).mean()
    cf_std = cum_fund.rolling(
        FUNDING_DIVERGENCE_NORM, min_periods=FUNDING_DIVERGENCE_NORM
    ).std(ddof=1)
    cf_z = (cum_fund - cf_mean) / cf_std.replace(0, np.nan)

    logc = np.log(df["close"].astype(float))
    price_ret = (logc - logc.shift(FUNDING_DIVERGENCE_WINDOW)).shift(1)
    pr_mean = price_ret.rolling(
        FUNDING_DIVERGENCE_NORM, min_periods=FUNDING_DIVERGENCE_NORM
    ).mean()
    pr_std = price_ret.rolling(
        FUNDING_DIVERGENCE_NORM, min_periods=FUNDING_DIVERGENCE_NORM
    ).std(ddof=1)
    pr_z = (price_ret - pr_mean) / pr_std.replace(0, np.nan)

    df["funding_price_divergence_6"] = (cf_z - pr_z).clip(lower=-clip, upper=clip).values

    return df


def add_funding_family_v3_features(
    df: pd.DataFrame,
    data_dir: Path | str = _DEFAULT_DATA_DIR,
    clip: float = ZSCORE_CLIP,
) -> pd.DataFrame:
    """GROUP_REGISTRY entry point for the ``funding_family_v3`` group (iter-v3/082).

    Reads the per-symbol ``data/funding_rates/<SYMBOL>.csv`` cache (populated by
    ``uv run crypto-trade fetch-funding``) and appends the 4
    ``FUNDING_FAMILY_COLUMNS``.

    Parameters
    ----------
    df:
        Kline DataFrame with ``symbol``, ``open_time`` and ``close`` columns.
    data_dir:
        Root data directory (default ``data/``).
    clip:
        Z-score clip threshold for the divergence feature (default 10.0).

    Returns
    -------
    pd.DataFrame
        Input df with the 4 funding-family columns appended.

    Raises
    ------
    FileNotFoundError
        If the funding-rate cache for the symbol does not exist.
    KeyError
        If ``df`` does not contain the ``symbol`` column.
    """
    data_dir = Path(data_dir)

    symbol = df["symbol"].iloc[0] if "symbol" in df.columns else None
    if symbol is None:
        raise KeyError(
            "df must contain a 'symbol' column for funding_family_v3 feature group. "
            "Set df['symbol'] = '<SYMBOL>' before calling add_funding_family_v3_features."
        )

    cache_path = data_dir / "funding_rates" / f"{symbol}.csv"
    if not cache_path.exists():
        raise FileNotFoundError(
            f"Funding-rate cache not found: {cache_path}. "
            f"Run: uv run crypto-trade fetch-funding --symbols {symbol}"
        )

    funding_df = pd.read_csv(cache_path)
    if len(funding_df) == 0:
        df = df.copy()
        for col in FUNDING_FAMILY_COLUMNS:
            df[col] = np.nan
        return df

    return compute_funding_family(df, funding_df, clip=clip)
