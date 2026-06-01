"""v1 long/short positioning features — iter-v1/049 (feature-family EXPLORATION #4/10 cycle-6).

Track-isolated: ZERO imports from crypto_trade.features_v2 or crypto_trade.features_v3.

Top-trader long/short account ratio (``sum_toptrader_long_short_ratio``) is an
account-NOTIONAL positioning sentiment primitive already cached at 8h cadence in
``data/open_interest/<SYMBOL>/8h.csv`` by the ``fetch-oi`` subcommand (iter-v3/093).
It is structurally orthogonal to all 44 existing V1_FEATURE_COLUMNS_PRUNED features,
which are functions of {OHLCV, funding_rate, open_interest, calendar}.

Column of interest in the OI cache (schema confirmed):
  ``sum_toptrader_long_short_ratio`` — sum of per-account notional long/short ratio
  as reported by Binance ``/futures/data/topLongShortAccountRatio`` (aggregated by
  the OI fetcher into the unified per-symbol 8h CSV).

Single feature exported:
  - ``long_short_zscore_30``: 30-bar (10-day) rolling z-score of
    ``sum_toptrader_long_short_ratio``.

Feature definition (canonical):

    lsr[t]                = sum_toptrader_long_short_ratio[t]          (bar close, past-only)
    lsr_mean_30[t]        = mean(lsr[t-29]...lsr[t])                  (30-bar window)
    lsr_std_30[t]         = std(lsr[t-29]...lsr[t], ddof=1)           (30-bar window)
    long_short_zscore_30[t] = (lsr[t] - lsr_mean_30[t]) / lsr_std_30[t]

**Past-only invariant**: ``lsr[t]`` is the exchange snapshot AS OF the 8h bar close
at t (fully knowable before the next 8h bar opens). The 30-bar rolling window uses
``min_periods=30`` so the denominator at t uses ONLY bars t-29...t (no future data).
The decision at candle ``t+1`` uses ``long_short_zscore_30[t]`` — one bar in the past.
No ``shift(1)`` needed here because the LightGBM feature frame is built by left-joining
the OI CSV (which already stores the CLOSED bar's ratio value), then the strategy reads
``feat_row[t]`` at candle ``t+1`` open (one bar lag is implicit in the walk-forward loop).

Warmup:
    First 29 candles per symbol are NaN (``min_periods=30`` → need 30 bars).
    At 8h cadence: 29 bars ≈ 9.67 calendar days. All v1 symbols have OI history
    starting 2020-09-01 (BTC/ETH) or 2021-12-01 (LINK/LTC/DOT) — far beyond the
    24-month IS window starting 2023-03-24. Warmup is the only NaN region.

Scale-invariance:
    Z-score normalization removes the unit; output is dimensionless.
    Clipped to [-10, +10] to prevent LightGBM instability (same convention as
    funding_v1, open_interest_v1, basis_v1).

Structural orthogonality argument (from brief Section 0.6 + Section 1):
    ``sum_toptrader_long_short_ratio`` is computed by Binance from per-account
    net position direction aggregation — completely independent of price/volume/
    range/funding/OI numerics. It is NOT derivable from OHLCV or existing
    V1_FEATURE_COLUMNS_PRUNED features. F5' IC sweep against all 44 existing
    features is the empirical arbiter (brief Section 2.5 predicts max |IC| = 0.28
    vs ``funding_rate_zscore_30`` — well below the ABORT threshold 0.60).

Track isolation enforcement:
    Phase 6.0 pre-flight Critic verifies:
        grep -r "from crypto_trade.features_v2" src/crypto_trade/features_v1/
        grep -r "from crypto_trade.features_v3" src/crypto_trade/features_v1/
    Both must return empty. This module has ZERO such imports.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# Rolling window constant (8h cadence: 3 bars/day; 30 bars = 10 days)
LSR_ZSCORE_WINDOW: int = 30

# Clip z-scored output to prevent LightGBM training instability
# (matches ZSCORE_CLIP convention in funding_v1.py / open_interest_v1.py / basis_v1.py)
LSR_ZSCORE_CLIP: float = 10.0

# Column name in the OI cache file for the long/short ratio primitive
LSR_SOURCE_COLUMN: str = "sum_toptrader_long_short_ratio"

# Default data directory for OI cache
_DEFAULT_DATA_DIR: Path = Path("data")


def compute_long_short_zscore(
    lsr_series: pd.Series,
    window: int = LSR_ZSCORE_WINDOW,
    clip: float = LSR_ZSCORE_CLIP,
) -> pd.Series:
    """Compute rolling z-score of a long/short ratio series.

    Parameters
    ----------
    lsr_series:
        Raw ``sum_toptrader_long_short_ratio`` series aligned to kline open_times.
        Index must match the kline DataFrame index (integer position).
    window:
        Rolling window in bars (default 30 = ~10 days at 8h cadence).
    clip:
        Absolute clip threshold for the z-scored output (default 10.0).

    Returns
    -------
    pd.Series
        Past-only z-scored long/short ratio series.
        First ``window - 1`` rows are NaN due to ``min_periods=window``.

    Notes
    -----
    Look-ahead discipline:
        ``lsr[t]`` is the exchange snapshot for the 8h bar closing at t —
        fully published before bar t+1 opens. The ``rolling(window=30,
        min_periods=30)`` window at bar t sees lsr[t-29]...lsr[t] (no future
        data). The LightGBM feature frame is built ONCE from the closed parquet;
        the strategy reads ``feat_row[t]`` at candle ``t+1`` open (implicit
        one-bar lag via the walk-forward loop indexing).
    """
    lsr = lsr_series.astype(float)
    rmean = lsr.rolling(window=window, min_periods=window).mean()
    rstd = lsr.rolling(window=window, min_periods=window).std(ddof=1)
    zscore = (lsr - rmean) / rstd.replace(0, np.nan)
    return zscore.clip(-clip, clip)


def add_longshort_v1_features(
    df: pd.DataFrame,
    data_dir: Path | str = _DEFAULT_DATA_DIR,
    window: int = LSR_ZSCORE_WINDOW,
    clip: float = LSR_ZSCORE_CLIP,
) -> pd.DataFrame:
    """Load cached OI data for ``df``'s symbol and add ``long_short_zscore_30`` column.

    Parameters
    ----------
    df:
        Kline DataFrame with ``symbol`` and ``open_time`` (ms int) columns.
    data_dir:
        Root data directory (default ``data/``). Reads from
        ``data_dir/open_interest/<SYMBOL>/8h.csv``.
    window:
        Rolling window in bars for z-score (default 30 = ~10 days).
    clip:
        Z-score clip threshold (default 10.0).

    Returns
    -------
    pd.DataFrame
        Input df (copy) with ``long_short_zscore_30`` column appended.
        Rows where OI data is absent (pre-archive-start) get NaN.
        First ``window - 1`` rows are NaN by construction (rolling warm-up).

    Raises
    ------
    FileNotFoundError
        If the OI cache for the symbol does not exist.
        Run ``uv run crypto-trade fetch-oi --symbols <SYMBOL>`` first.
        NEVER silently fills NaN.
    KeyError
        If ``df`` does not contain the ``symbol`` column.

    Notes
    -----
    Alignment: OI cache ``open_time`` (ms epoch int) must match kline ``open_time``.
    Both are 8h-aligned Binance timestamps; no rounding needed for 8h bars.
    A direct integer merge on ``open_time`` is used (no jitter — matches the
    open_interest_v1 pattern for OI data).

    Data source column: ``sum_toptrader_long_short_ratio`` (column index 4 in the
    OI CSV schema: open_time, sum_open_interest, sum_open_interest_value,
    count_toptrader_long_short_ratio, sum_toptrader_long_short_ratio, ...).
    """
    data_dir = Path(data_dir)

    if "symbol" not in df.columns:
        raise KeyError(
            "df must contain a 'symbol' column for longshort_v1 feature group. "
            "Set df['symbol'] = '<SYMBOL>' before calling add_longshort_v1_features."
        )

    symbol = df["symbol"].iloc[0]
    oi_path = data_dir / "open_interest" / symbol / "8h.csv"

    if not oi_path.exists():
        raise FileNotFoundError(
            f"OI cache not found: {oi_path}. "
            f"Run: uv run crypto-trade fetch-oi --symbols {symbol} --intervals 8h"
        )

    oi_df = pd.read_csv(oi_path)

    if len(oi_df) == 0:
        # Empty cache: add NaN column and return (do NOT silently fill zeros)
        df = df.copy()
        df["long_short_zscore_30"] = np.nan
        return df

    if LSR_SOURCE_COLUMN not in oi_df.columns:
        raise KeyError(
            f"OI cache {oi_path} missing column '{LSR_SOURCE_COLUMN}'. "
            f"Available columns: {list(oi_df.columns)}. "
            "Ensure fetch-oi was run with a version that fetches topLongShortAccountRatio."
        )

    # ------------------------------------------------------------------
    # Align OI to kline frame via left-merge on open_time (ms int).
    # Use a helper merge-key column to avoid the "open_time is both an
    # index level and a column label" ValueError (same pattern as
    # open_interest_v1.py).
    # ------------------------------------------------------------------
    df = df.copy()
    df["_lsr_merge_key"] = df["open_time"].astype("int64")

    oi_keyed = oi_df[["open_time", LSR_SOURCE_COLUMN]].copy()
    oi_keyed["_lsr_merge_key"] = oi_keyed["open_time"].astype("int64")

    merged = df.merge(
        oi_keyed[["_lsr_merge_key", LSR_SOURCE_COLUMN]],
        on="_lsr_merge_key",
        how="left",
    ).drop(columns=["_lsr_merge_key"])

    # Restore original index alignment
    merged.index = df.index

    # Clean up the merge key from df (df is already a copy)
    df = df.drop(columns=["_lsr_merge_key"])

    lsr_series = merged[LSR_SOURCE_COLUMN].astype(float)

    # Compute z-score (past-only by rolling window semantics)
    zscore = compute_long_short_zscore(lsr_series, window=window, clip=clip)

    df["long_short_zscore_30"] = zscore.values

    return df


__all__ = [
    "LSR_ZSCORE_WINDOW",
    "LSR_ZSCORE_CLIP",
    "LSR_SOURCE_COLUMN",
    "compute_long_short_zscore",
    "add_longshort_v1_features",
]
