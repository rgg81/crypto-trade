"""v3 funding-rate features — funding_rate_zscore_30 (iter-v3/019 NEW external-data-source axis).

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
