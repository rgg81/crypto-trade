"""v3 multi-frequency (coarser daily-bar) features — iter-v3/113; 24h-multioffset — iter-v3/126.

Track-isolated module (NO imports from crypto_trade.features (v1) or
crypto_trade.features_v2 (v2)). The Phase 6 grep check must stay empty:

    grep -r "from crypto_trade.features " src/crypto_trade/features_v3/
    grep -r "from crypto_trade.features_v2" src/crypto_trade/features_v3/

Axis iter-v3/113: cycle-6 menu item 3 — multi-frequency feature engineering.
One symbol's 8h OHLCV frame → copy with 8 coarser-frequency daily features.

Axis iter-v3/126: cycle-7 EXPLORATION #5 — 24h multi-frequency feature stack.
Loads data/features_v3_24h/<SYM>_24h_features.parquet (offset_id=0 slice),
extracts d24_ret_autocorr_lag1_50, and merges causally onto the 8h decision
grid via pd.merge_asof(direction='backward', left_on='open_time',
right_on='bar_close_time', allow_exact_matches=True).

Look-ahead-free design (T2 audit EDA SHA dd9fc2d: 0 violations / 14130 rows):
    The merge direction='backward' + allow_exact_matches=True guarantees
    bar_close_time <= open_time for every joined row. The 24h bar at
    bar_close_time t_close can only be joined to an 8h bar whose open_time >= t_close.
    TRX max_lag observed 88h (3.7 days) in data gaps — still strictly past-only.

The d24_ prefix distinguishes 24h-cadence features from the d_ prefix used by
the /113 family (8h-aggregated-to-daily). 'd24_' features load from the
/117 multi-offset infrastructure parquet; 'd_' features aggregate inline.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

MS_PER_DAY: int = 86_400_000

DAILY_FEATURES: list[str] = [
    "d_ret_5d",
    "d_ret_10d",
    "d_trend_slope_10",
    "d_realvol_10",
    "d_realvol_ratio",
    "d_atr_pctrank_60",
    "d_efficiency_10",
    "d_close_pos_20",
]


def _aggregate_to_daily(df8h: pd.DataFrame) -> pd.DataFrame:
    """Aggregate one symbol's 8h OHLCV frame into 1d (daily) bars.

    The 8h candles open at 00/08/16 UTC; a daily bar groups the (up to) three
    8h candles whose open_time falls in [day_start, day_start + 1d).  For each
    daily bar:
        open       = first 8h open in the day
        high       = max 8h high
        low        = min 8h low
        close      = last 8h close
        volume     = sum 8h volume
        day_open   = day_start epoch-ms
        day_close  = last 8h close_time in the day  (the causal timestamp:
                     the daily feature for any 8h decision row is only valid
                     once day_close <= that 8h row's open_time)
        n_8h       = number of 8h candles in the day (should be 3; < 3 on data gaps)

    Days with fewer than 3 8h candles (data gaps) are still aggregated — partial
    days are kept as a faithful reflection of the data the runner sees.
    """
    df = df8h.sort_values("open_time").reset_index(drop=True).copy()
    df["day_open"] = (df["open_time"] // MS_PER_DAY) * MS_PER_DAY
    grp = df.groupby("day_open", sort=True)
    daily = pd.DataFrame(
        {
            "day_open": grp["day_open"].first().to_numpy(),
            "open": grp["open"].first().to_numpy(),
            "high": grp["high"].max().to_numpy(),
            "low": grp["low"].min().to_numpy(),
            "close": grp["close"].last().to_numpy(),
            "volume": grp["volume"].sum().to_numpy(),
            "day_close": grp["close_time"].last().to_numpy(),
            "n_8h": grp.size().to_numpy(),
        }
    ).reset_index(drop=True)
    return daily


def _add_daily_features(daily: pd.DataFrame) -> pd.DataFrame:
    """Compute the 8 coarser-frequency feature family on the daily bars.

    All features are scale-invariant and strictly past-only (every rolling
    window uses only bars at index <= t; no centered windows; no shift into the
    future).  Verbatim from analysis/iteration_v3-113/_shared.py:_add_daily_features
    (EDA SHA ebd84e2) — production feature is bit-identical to EDA-validated feature.
    """
    d = daily.sort_values("day_open").reset_index(drop=True).copy()
    close = d["close"].to_numpy(dtype=np.float64)
    high = d["high"].to_numpy(dtype=np.float64)
    low = d["low"].to_numpy(dtype=np.float64)
    n = len(d)
    log_close = np.log(np.where(close > 0, close, np.nan))

    def _lag_ret(h: int) -> np.ndarray:
        out = np.full(n, np.nan)
        if n > h:
            out[h:] = log_close[h:] - log_close[:-h]
        return out

    d["d_ret_5d"] = _lag_ret(5)
    d["d_ret_10d"] = _lag_ret(10)

    # OLS slope of log_close vs index over a 10-bar trailing window,
    # normalized by mean log-price (smoothed daily trend-strength estimate).
    slope = np.full(n, np.nan)
    win = 10
    x = np.arange(win, dtype=np.float64)
    x_c = x - x.mean()
    denom = np.sum(x_c**2)
    for t in range(win - 1, n):
        y = log_close[t - win + 1 : t + 1]
        if np.any(np.isnan(y)):
            continue
        y_c = y - y.mean()
        slope[t] = np.sum(x_c * y_c) / denom / (np.abs(y.mean()) + 1e-12)
    d["d_trend_slope_10"] = slope

    log_ret_1d = np.concatenate([[np.nan], np.diff(log_close)])

    def _rv(w: int) -> np.ndarray:
        return pd.Series(log_ret_1d).rolling(w, min_periods=w).std().to_numpy()

    d["d_realvol_10"] = _rv(10)
    rv5, rv20 = _rv(5), _rv(20)
    with np.errstate(divide="ignore", invalid="ignore"):
        d["d_realvol_ratio"] = np.where(rv20 > 0, rv5 / rv20, np.nan)

    # Daily true-range / close, percentile-ranked over 60 bars.
    prev_close = np.concatenate([[np.nan], close[:-1]])
    tr = np.maximum(
        high - low,
        np.maximum(np.abs(high - prev_close), np.abs(low - prev_close)),
    )
    with np.errstate(divide="ignore", invalid="ignore"):
        tr_norm = np.where(close > 0, tr / close, np.nan)
    d["d_atr_pctrank_60"] = (
        pd.Series(tr_norm).rolling(60, min_periods=60).apply(lambda s: s.rank(pct=True).iloc[-1])
    ).to_numpy()

    # Kaufman efficiency ratio over 10 daily bars.
    eff = np.full(n, np.nan)
    abs_1d = np.abs(log_ret_1d)
    for t in range(10, n):
        net = np.abs(log_close[t] - log_close[t - 10])
        path = np.nansum(abs_1d[t - 9 : t + 1])
        if path > 0:
            eff[t] = net / path
    d["d_efficiency_10"] = eff

    # Daily close position in the last-20-bar [min low, max high] channel.
    roll_lo = pd.Series(low).rolling(20, min_periods=20).min().to_numpy()
    roll_hi = pd.Series(high).rolling(20, min_periods=20).max().to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        d["d_close_pos_20"] = np.where(
            (roll_hi - roll_lo) > 0,
            (close - roll_lo) / (roll_hi - roll_lo),
            np.nan,
        )

    return d


def add_multifreq_v3_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add the 8 coarser-frequency daily features to one symbol's 8h frame.

    Takes one symbol's 8h DataFrame (must contain open_time, close_time, open,
    high, low, close, volume). Returns a copy with the 8 daily feature columns
    appended. The 'day_close' join-key column is dropped before returning —
    only the 8 DAILY_FEATURES columns are added.

    The three steps:
    (a) Aggregate the 8h frame to daily bars via _aggregate_to_daily.
    (b) Compute the 8 daily features via _add_daily_features.
    (c) Causal merge_asof — left_on=open_time, right_on=day_close,
        direction="backward", allow_exact_matches=True.
        The day_close <= open_time direction guarantees the daily bar is fully
        closed before the 8h decision candle opens.

    Mirrors the open_time-index guard used by cross_btc_v3.py: if the input
    DataFrame is indexed by open_time, it is temporarily reset and restored
    after the merge.

    Track isolation: imports ONLY stdlib + numpy / pandas.  No imports from
    crypto_trade.features (v1) or crypto_trade.features_v2 (v2).
    """
    df = df.copy()
    had_open_time_index = df.index.name == "open_time"
    if had_open_time_index:
        df = df.reset_index(drop=True)

    # (a) Aggregate 8h → daily bars.
    daily = _aggregate_to_daily(df)

    # (b) Compute the 8 daily features on the daily bars.
    daily = _add_daily_features(daily)

    # (c) Causal as-of join: most-recently-CLOSED daily bar at the 8h row's open.
    daily_join = (
        daily[["day_close"] + DAILY_FEATURES].sort_values("day_close").reset_index(drop=True)
    )
    df = df.sort_values("open_time").reset_index(drop=True)
    merged = pd.merge_asof(
        df,
        daily_join,
        left_on="open_time",
        right_on="day_close",
        direction="backward",
        allow_exact_matches=True,
    )
    # Drop the join-key column — only the 8 feature columns are part of the payload.
    merged = merged.drop(columns=["day_close"])

    if had_open_time_index:
        merged = merged.set_index("open_time", drop=False)
        merged.index.name = "open_time"

    return merged


# ---------------------------------------------------------------------------
# iter-v3/126: 24h multi-frequency feature — d24_ret_autocorr_lag1_50
# ---------------------------------------------------------------------------

#: The single 24h feature column added by iter-v3/126.
D24_FEATURE_COLUMN: str = "d24_ret_autocorr_lag1_50"

#: The source parquet column name (before d24_ prefix rename).
_D24_SOURCE_COLUMN: str = "ret_autocorr_lag1_50"

#: Default features_v3_24h directory (relative to the repo root).
_DEFAULT_24H_DIR: Path = Path("data/features_v3_24h")


def add_multifreq_v3_24h_features(
    df8h: pd.DataFrame,
    symbol: str | None = None,
    features_24h_dir: str | Path | None = None,
) -> pd.DataFrame:
    """Add the 24h multi-frequency feature d24_ret_autocorr_lag1_50 to one symbol's 8h frame.

    iter-v3/126 cycle-7 EXPLORATION #5 — FEATURE-CADENCE-STACK axis.

    Parameters
    ----------
    df8h:
        One symbol's 8h decision-grid DataFrame. Must contain ``open_time`` and
        ``symbol`` columns (or pass ``symbol`` explicitly). The ``symbol`` column
        is used to locate the 24h parquet at
        ``features_24h_dir/<SYM>_24h_features.parquet``.
    symbol:
        Symbol string (e.g. 'BCHUSDT'). If None, reads from ``df8h['symbol'].iloc[0]``.
    features_24h_dir:
        Path to the directory containing the 24h feature parquets. Defaults to
        ``data/features_v3_24h/`` (relative to cwd, i.e. the repo root).

    Returns
    -------
    pd.DataFrame
        Copy of ``df8h`` with one new column appended: ``d24_ret_autocorr_lag1_50``.
        The ``bar_close_time`` join-key is dropped before returning — only the
        feature column is added to the payload.

    Look-ahead-free design
    ----------------------
    The merge_asof uses ``direction='backward'`` + ``allow_exact_matches=True`` with
    ``left_on='open_time'`` and ``right_on='bar_close_time'``. This guarantees that
    for every joined 8h row, the matched 24h bar satisfies
    ``bar_close_time <= open_time``. The 24h bar is fully closed before the 8h
    decision candle opens (or at the exact same instant for the 00:00 UTC alignment).

    T2 audit (EDA SHA dd9fc2d): 0 look-ahead violations across 14130 joined rows
    (BCH/LDO/TRX IS+OOS combined). Median lag = 8.0 hours. TRX max_lag = 88h
    (data gap) — still strictly past-only.

    Track isolation
    ---------------
    Imports ONLY stdlib + numpy / pandas + pathlib. No imports from
    ``crypto_trade.features`` (v1) or ``crypto_trade.features_v2`` (v2).
    """
    df = df8h.copy()
    had_open_time_index = df.index.name == "open_time"
    if had_open_time_index:
        df = df.reset_index(drop=True)

    # Resolve symbol.
    if symbol is None:
        if "symbol" not in df.columns:
            raise ValueError(
                "add_multifreq_v3_24h_features: 'symbol' column not found in df8h "
                "and no symbol parameter supplied."
            )
        symbol = str(df["symbol"].iloc[0])

    # Resolve 24h parquet path.
    parquet_dir = Path(features_24h_dir) if features_24h_dir is not None else _DEFAULT_24H_DIR
    parquet_path = parquet_dir / f"{symbol}_24h_features.parquet"
    if not parquet_path.exists():
        raise FileNotFoundError(
            f"add_multifreq_v3_24h_features: 24h feature parquet not found: {parquet_path}. "
            f"Run the 24h feature pipeline for {symbol} first (iter-v3/117 infrastructure)."
        )

    # Load offset_id=0 slice — calendar-day-aligned 24h aggregation.
    panel = pd.read_parquet(parquet_path)
    if "offset_id" not in panel.columns:
        raise KeyError(
            f"add_multifreq_v3_24h_features: 'offset_id' column missing from {parquet_path}. "
            "Parquet was generated with an older version of the /117 pipeline."
        )
    panel_offset0 = panel[panel["offset_id"] == 0].copy()

    # Extract the single feature column.
    if _D24_SOURCE_COLUMN not in panel_offset0.columns:
        raise KeyError(
            f"add_multifreq_v3_24h_features: source column '{_D24_SOURCE_COLUMN}' "
            f"not found in {parquet_path} (offset_id=0). "
            "Verify the /117 pipeline wrote this column."
        )
    join_frame = (
        panel_offset0[["bar_close_time", _D24_SOURCE_COLUMN]]
        .rename(columns={_D24_SOURCE_COLUMN: D24_FEATURE_COLUMN})
        .sort_values("bar_close_time")
        .reset_index(drop=True)
    )

    # Causal as-of join: most-recently-CLOSED 24h bar at each 8h row's open.
    df_sorted = df.sort_values("open_time").reset_index(drop=True)
    merged = pd.merge_asof(
        df_sorted,
        join_frame,
        left_on="open_time",
        right_on="bar_close_time",
        direction="backward",
        allow_exact_matches=True,
    )
    # Drop the join-key column — only the feature column is part of the payload.
    merged = merged.drop(columns=["bar_close_time"])

    if had_open_time_index:
        merged = merged.set_index("open_time", drop=False)
        merged.index.name = "open_time"

    return merged
