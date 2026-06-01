"""v1 cross-BTC idiosyncratic ratio features — iter-v1/050 (DOT) + /055 (ETH) + /057 (LTC).

Feature-family EXPLORATION:
- iter-v1/050 EXPLORATION #5/10 cycle-6 (DOT cross-asset ratio)
- iter-v1/055 EXPLORATION #10/10 cycle-6 FINAL (ETH cross-asset ratio)
- iter-v1/057 EXPLORATION #1/N cycle-7 (LTC cross-asset ratio; algebraic mirror of /055)

Track-isolated: ZERO imports from crypto_trade.features_v2 or crypto_trade.features_v3.

This module provides cross-asset features measuring DOT's, ETH's, and LTC's idiosyncratic
return relative to BTC market beta, z-scored for stationarity.

Feature: ``dot_vs_btc_ret_ratio_30``
-------------------------------------
Captures phases where DOTUSDT's 30-bar price return DECOUPLES from BTC's 30-bar return —
signalling an idiosyncratic altcoin-expansion regime vs BTC-dominance contagion.

Computation:
    dot_ret_30[t]  = dot_close.pct_change(30)[t]     (past-only 30-bar return)
    btc_ret_30[t]  = btc_close.pct_change(30)[t]     (past-only 30-bar return)
    ratio[t]       = dot_ret_30[t] / btc_ret_30[t]   (replace inf/nan with NaN; clip ±10)
    zscore[t]      = rolling_zscore_90bar(ratio[t])   (clip ±10)

For non-DOTUSDT symbols: the feature is NaN (DOT-only signal; other symbols are unaffected
at training time since run_iteration_050 uses DOT-only cohort).

Feature: ``eth_vs_btc_ret_ratio_30``
-------------------------------------
iter-v1/055 FINAL EXPLORATION #10/10 cycle-6. Direct algebraic mirror of
``dot_vs_btc_ret_ratio_30`` for ETH-only specialist head. Captures phases where ETHUSDT's
30-bar price return DECOUPLES from BTC's 30-bar return — ETH idiosyncratic momentum vs BTC
market beta contagion.

Computation:
    eth_ret_30[t]  = eth_close.pct_change(30)[t]     (past-only 30-bar return)
    btc_ret_30[t]  = btc_close.pct_change(30)[t]     (past-only 30-bar return)
    ratio[t]       = eth_ret_30[t] / btc_ret_30[t]   (replace inf/nan with NaN; clip ±10)
    zscore[t]      = rolling_zscore_90bar(ratio[t])   (clip ±10)

For non-ETHUSDT symbols: the feature is NaN (ETH-only signal; other symbols are unaffected
at training time since run_iteration_055 uses ETH-only cohort).

Feature: ``ltc_vs_btc_ret_ratio_30``
-------------------------------------
iter-v1/057 EXPLORATION #1/N cycle-7. Direct algebraic mirror of
``eth_vs_btc_ret_ratio_30`` for LTC-only specialist head. Captures phases where LTCUSDT's
30-bar price return DECOUPLES from BTC's 30-bar return — LTC idiosyncratic momentum vs BTC
market beta contagion. LTC has lower correlation with BTC (~0.65 vs ETH ~0.85), producing
higher ratio variance and potentially more information content for the LightGBM model.

Computation:
    ltc_ret_30[t]  = ltc_close.pct_change(30)[t]     (past-only 30-bar return)
    btc_ret_30[t]  = btc_close.pct_change(30)[t]     (past-only 30-bar return)
    ratio[t]       = ltc_ret_30[t] / btc_ret_30[t]   (replace inf/nan with NaN; clip ±10)
    zscore[t]      = rolling_zscore_90bar(ratio[t])   (clip ±10)

For non-LTCUSDT symbols: the feature is NaN (LTC-only signal; other symbols are unaffected
at training time since run_iteration_057 uses LTC-only cohort).

Data source:
    BTC close prices from ``data_dir/BTCUSDT/8h.csv`` (standard kline CSV).
    DOT close prices from the input kline DataFrame (passed in as ``df``).

Look-ahead discipline (PAST-ONLY):
    pct_change(30) at bar t uses close[t-30]...close[t] — fully in the past.
    rolling(90, min_periods=90) at bar t uses ratio[t-89]...ratio[t] — no future data.
    Unit-test ``tests/test_iteration_v1_050.py::test_cross_btc_v1_no_lookahead`` verifies
    this: perturbing ratio[-1] does NOT affect zscore[<-1].

Warmup:
    - dot_ret_30, btc_ret_30: first 30 rows NaN (pct_change(30) needs 30 bars)
    - rolling zscore: first 90 rows NaN (min_periods=90 rolling window on ratio)
    Total warmup: first 90 rows NaN (zscore dominates).
    At 8h cadence: 90 bars = 30 calendar days. IS window starts 2023-03-24 (full 24 months).
    Warmup is the only NaN region.

Regime-gate integration (runner-side, NOT in this module):
    The companion vol-spike regime gate lives in ``run_iteration_050.py``:
        btc_realized_vol_30 = rolling_30bar_std(log(btc_close)).shift(1)  (IS-only q75)
        if vol > q75_IS AND pred_proba < 0.55: skip_signal()
    This module only computes the FEATURE, not the post-prediction gate.

Scale-invariance:
    Z-score output is dimensionless and clipped to [-10, +10].
    Matches the convention in funding_v1.py, open_interest_v1.py, longshort_v1.py.

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

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Return lookback window (number of bars). At 8h cadence: 30 bars = 10 days.
RATIO_LOOKBACK: int = 30

#: Z-score rolling window (number of bars). At 8h cadence: 90 bars = 30 days.
ZSCORE_WINDOW: int = 90

#: Clip ratio before z-scoring (prevents extreme outliers from BTC ≈ 0 return periods).
RATIO_CLIP: float = 10.0

#: Clip z-scored output (matches convention in funding_v1.py / longshort_v1.py).
ZSCORE_CLIP: float = 10.0

#: Column name of the DOT output feature.
FEATURE_COLUMN: str = "dot_vs_btc_ret_ratio_30"

#: Column name of the ETH output feature (iter-v1/055).
ETH_FEATURE_COLUMN: str = "eth_vs_btc_ret_ratio_30"

#: Column name of the LTC output feature (iter-v1/057).
LTC_FEATURE_COLUMN: str = "ltc_vs_btc_ret_ratio_30"

#: Symbol for which the DOT feature is meaningful. NaN for all other symbols.
TARGET_SYMBOL: str = "DOTUSDT"

#: Symbol for which the ETH feature is meaningful (iter-v1/055). NaN for all other symbols.
ETH_TARGET_SYMBOL: str = "ETHUSDT"

#: Symbol for which the LTC feature is meaningful (iter-v1/057). NaN for all other symbols.
LTC_TARGET_SYMBOL: str = "LTCUSDT"

#: BTC symbol name used for cross-asset data loading.
BTC_SYMBOL: str = "BTCUSDT"

#: Default data directory.
_DEFAULT_DATA_DIR: Path = Path("data")


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------


def compute_dot_vs_btc_ret_ratio_30(
    df_dot: pd.DataFrame,
    df_btc: pd.DataFrame,
    lookback: int = RATIO_LOOKBACK,
    zscore_window: int = ZSCORE_WINDOW,
    ratio_clip: float = RATIO_CLIP,
    zscore_clip: float = ZSCORE_CLIP,
) -> pd.Series:
    """Compute the DOT-vs-BTC 30-bar return ratio, z-scored over 90 bars.

    Parameters
    ----------
    df_dot:
        DOTUSDT kline DataFrame with a ``close`` column and ``open_time`` (ms int) index
        or column. Must be aligned and sorted by time (ascending).
    df_btc:
        BTCUSDT kline DataFrame with a ``close`` column aligned to ``df_dot`` by
        ``open_time``.
    lookback:
        Number of bars for pct_change return computation (default 30 = 10 days at 8h).
    zscore_window:
        Rolling window for z-score computation (default 90 = 30 days at 8h).
    ratio_clip:
        Absolute clip threshold for raw ratio before z-scoring (default 10.0).
    zscore_clip:
        Absolute clip threshold for final z-scored output (default 10.0).

    Returns
    -------
    pd.Series
        Past-only z-scored ratio aligned to ``df_dot``'s index.
        First ``zscore_window - 1`` rows are NaN (rolling warm-up dominates).
        Rows where BTC return is zero (or NaN) produce NaN (no division by zero).

    Notes
    -----
    **Past-only invariant**: ``pct_change(lookback)`` at bar t uses close[t-lookback]...
    close[t] — all past data. The z-score window uses ratio[t-zscore_window+1]...
    ratio[t] — all past data. No ``shift(1)`` is needed because ``df_dot`` is the kline
    frame whose features are indexed at the bar CLOSE — the strategy consumes
    ``feat_row[t]`` at bar ``t+1`` open (implicit one-bar lag in the walk-forward loop).
    """
    # Extract close series (reset index for alignment safety)
    dot_close = df_dot["close"].reset_index(drop=True).astype(float)
    btc_close = df_btc["close"].reset_index(drop=True).astype(float)

    # 30-bar percentage returns (past-only by pct_change definition)
    dot_ret = dot_close.pct_change(lookback)
    btc_ret = btc_close.pct_change(lookback)

    # Ratio: DOT / BTC; replace zero-denominator and inf with NaN
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio_raw = dot_ret / btc_ret

    # Replace inf/-inf introduced by btc_ret == 0 with NaN
    ratio_raw = ratio_raw.replace([np.inf, -np.inf], np.nan)

    # Clip extreme ratios before z-scoring
    ratio_clipped = ratio_raw.clip(-ratio_clip, ratio_clip)

    # Rolling 90-bar z-score (past-only)
    rmean = ratio_clipped.rolling(window=zscore_window, min_periods=zscore_window).mean()
    rstd = ratio_clipped.rolling(window=zscore_window, min_periods=zscore_window).std(ddof=1)

    # Divide, handling rolling_std == 0 (constant ratio window)
    zscore = (ratio_clipped - rmean) / rstd.replace(0, np.nan)

    # Final clip
    return zscore.clip(-zscore_clip, zscore_clip)


# ---------------------------------------------------------------------------
# ETH cross-asset ratio (iter-v1/055)
# ---------------------------------------------------------------------------


def compute_eth_vs_btc_ret_ratio_30(
    df_eth: pd.DataFrame,
    df_btc: pd.DataFrame,
    lookback: int = RATIO_LOOKBACK,
    zscore_window: int = ZSCORE_WINDOW,
    ratio_clip: float = RATIO_CLIP,
    zscore_clip: float = ZSCORE_CLIP,
) -> pd.Series:
    """Compute the ETH-vs-BTC 30-bar return ratio, z-scored over 90 bars.

    Direct algebraic mirror of ``compute_dot_vs_btc_ret_ratio_30`` for ETHUSDT.
    Captures ETH idiosyncratic momentum vs BTC market beta.

    Parameters
    ----------
    df_eth:
        ETHUSDT kline DataFrame with a ``close`` column and ``open_time`` (ms int) index
        or column. Must be aligned and sorted by time (ascending).
    df_btc:
        BTCUSDT kline DataFrame with a ``close`` column aligned to ``df_eth`` by
        ``open_time``.
    lookback:
        Number of bars for pct_change return computation (default 30 = 10 days at 8h).
    zscore_window:
        Rolling window for z-score computation (default 90 = 30 days at 8h).
    ratio_clip:
        Absolute clip threshold for raw ratio before z-scoring (default 10.0).
    zscore_clip:
        Absolute clip threshold for final z-scored output (default 10.0).

    Returns
    -------
    pd.Series
        Past-only z-scored ratio aligned to ``df_eth``'s index.
        First ``zscore_window - 1`` rows are NaN (rolling warm-up dominates).
        Rows where BTC return is zero (or NaN) produce NaN (no division by zero).

    Notes
    -----
    **Past-only invariant**: identical to ``compute_dot_vs_btc_ret_ratio_30``.
    ``pct_change(lookback)`` at bar t uses close[t-lookback]...close[t] — all past data.
    The z-score window uses ratio[t-zscore_window+1]...ratio[t] — all past data.
    """
    # Extract close series (reset index for alignment safety)
    eth_close = df_eth["close"].reset_index(drop=True).astype(float)
    btc_close = df_btc["close"].reset_index(drop=True).astype(float)

    # 30-bar percentage returns (past-only by pct_change definition)
    eth_ret = eth_close.pct_change(lookback)
    btc_ret = btc_close.pct_change(lookback)

    # Ratio: ETH / BTC; replace zero-denominator and inf with NaN
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio_raw = eth_ret / btc_ret

    # Replace inf/-inf introduced by btc_ret == 0 with NaN
    ratio_raw = ratio_raw.replace([np.inf, -np.inf], np.nan)

    # Clip extreme ratios before z-scoring
    ratio_clipped = ratio_raw.clip(-ratio_clip, ratio_clip)

    # Rolling 90-bar z-score (past-only)
    rmean = ratio_clipped.rolling(window=zscore_window, min_periods=zscore_window).mean()
    rstd = ratio_clipped.rolling(window=zscore_window, min_periods=zscore_window).std(ddof=1)

    # Divide, handling rolling_std == 0 (constant ratio window)
    zscore = (ratio_clipped - rmean) / rstd.replace(0, np.nan)

    # Final clip
    return zscore.clip(-zscore_clip, zscore_clip)


# ---------------------------------------------------------------------------
# LTC cross-asset ratio (iter-v1/057)
# ---------------------------------------------------------------------------


def compute_ltc_vs_btc_ret_ratio_30(
    df_ltc: pd.DataFrame,
    df_btc: pd.DataFrame,
    lookback: int = RATIO_LOOKBACK,
    zscore_window: int = ZSCORE_WINDOW,
    ratio_clip: float = RATIO_CLIP,
    zscore_clip: float = ZSCORE_CLIP,
) -> pd.Series:
    """Compute the LTC-vs-BTC 30-bar return ratio, z-scored over 90 bars.

    Direct algebraic mirror of ``compute_eth_vs_btc_ret_ratio_30`` for LTCUSDT.
    Captures LTC idiosyncratic momentum vs BTC market beta. LTC has lower correlation
    with BTC (~0.65) than ETH (~0.85), producing higher ratio variance and potentially
    more information content for the LightGBM model.

    Parameters
    ----------
    df_ltc:
        LTCUSDT kline DataFrame with a ``close`` column and ``open_time`` (ms int) index
        or column. Must be aligned and sorted by time (ascending).
    df_btc:
        BTCUSDT kline DataFrame with a ``close`` column aligned to ``df_ltc`` by
        ``open_time``.
    lookback:
        Number of bars for pct_change return computation (default 30 = 10 days at 8h).
    zscore_window:
        Rolling window for z-score computation (default 90 = 30 days at 8h).
    ratio_clip:
        Absolute clip threshold for raw ratio before z-scoring (default 10.0).
    zscore_clip:
        Absolute clip threshold for final z-scored output (default 10.0).

    Returns
    -------
    pd.Series
        Past-only z-scored ratio aligned to ``df_ltc``'s index.
        First ``zscore_window - 1`` rows are NaN (rolling warm-up dominates).
        Rows where BTC return is zero (or NaN) produce NaN (no division by zero).

    Notes
    -----
    **Past-only invariant**: identical to ``compute_dot_vs_btc_ret_ratio_30``.
    ``pct_change(lookback)`` at bar t uses close[t-lookback]...close[t] — all past data.
    The z-score window uses ratio[t-zscore_window+1]...ratio[t] — all past data.
    """
    # Extract close series (reset index for alignment safety)
    ltc_close = df_ltc["close"].reset_index(drop=True).astype(float)
    btc_close = df_btc["close"].reset_index(drop=True).astype(float)

    # 30-bar percentage returns (past-only by pct_change definition)
    ltc_ret = ltc_close.pct_change(lookback)
    btc_ret = btc_close.pct_change(lookback)

    # Ratio: LTC / BTC; replace zero-denominator and inf with NaN
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio_raw = ltc_ret / btc_ret

    # Replace inf/-inf introduced by btc_ret == 0 with NaN
    ratio_raw = ratio_raw.replace([np.inf, -np.inf], np.nan)

    # Clip extreme ratios before z-scoring
    ratio_clipped = ratio_raw.clip(-ratio_clip, ratio_clip)

    # Rolling 90-bar z-score (past-only)
    rmean = ratio_clipped.rolling(window=zscore_window, min_periods=zscore_window).mean()
    rstd = ratio_clipped.rolling(window=zscore_window, min_periods=zscore_window).std(ddof=1)

    # Divide, handling rolling_std == 0 (constant ratio window)
    zscore = (ratio_clipped - rmean) / rstd.replace(0, np.nan)

    # Final clip
    return zscore.clip(-zscore_clip, zscore_clip)


# ---------------------------------------------------------------------------
# Feature injection
# ---------------------------------------------------------------------------


def _load_btc_aligned(
    df: pd.DataFrame,
    data_dir: Path,
    interval: str,
) -> pd.DataFrame:
    """Load BTC klines and align to ``df`` by ``open_time``.

    Internal helper shared by DOT and ETH feature computation.

    Parameters
    ----------
    df:
        Kline DataFrame (already a copy with ``_merge_key`` NOT yet added).
    data_dir:
        Root data directory. BTC klines read from ``data_dir/BTCUSDT/<interval>.csv``.
    interval:
        Kline interval string (e.g. ``8h``).

    Returns
    -------
    pd.DataFrame
        DataFrame with ``close`` and ``open_time`` columns aligned to ``df``'s index.
        Rows with no matching BTC bar produce NaN in ``close``.

    Raises
    ------
    FileNotFoundError:
        If BTC kline CSV is not found.
    KeyError:
        If BTC CSV is missing ``open_time`` or ``close`` columns.
    """
    btc_csv_path = data_dir / BTC_SYMBOL / f"{interval}.csv"
    if not btc_csv_path.exists():
        raise FileNotFoundError(
            f"BTC kline CSV not found: {btc_csv_path}. "
            f"Run: uv run crypto-trade fetch --symbols {BTC_SYMBOL} --intervals {interval}"
        )

    btc_raw = pd.read_csv(btc_csv_path)
    btc_raw.columns = [c.lower().replace(" ", "_") for c in btc_raw.columns]

    if "open_time" not in btc_raw.columns or "close" not in btc_raw.columns:
        raise KeyError(
            f"BTC CSV {btc_csv_path} missing 'open_time' or 'close' column. "
            f"Columns: {list(btc_raw.columns)}"
        )

    btc_raw["open_time"] = btc_raw["open_time"].astype("int64")
    btc_raw["close"] = pd.to_numeric(btc_raw["close"], errors="coerce")
    btc_raw = btc_raw[["open_time", "close"]].dropna().reset_index(drop=True)

    # Left-merge BTC close onto the symbol frame by open_time
    merge_key_col = "_merge_key_btc"
    df_tmp = df.copy()
    df_tmp[merge_key_col] = df_tmp["open_time"].astype("int64")
    btc_keyed = btc_raw.rename(columns={"close": "_btc_close"}).copy()
    btc_keyed[merge_key_col] = btc_keyed["open_time"].astype("int64")

    merged = df_tmp.merge(
        btc_keyed[[merge_key_col, "_btc_close"]],
        on=merge_key_col,
        how="left",
    )
    merged.index = df.index

    return pd.DataFrame(
        {"close": merged["_btc_close"].values, "open_time": df["open_time"].values},
        index=df.index,
    )


def add_cross_btc_v1_features(
    df: pd.DataFrame,
    data_dir: Path | str = _DEFAULT_DATA_DIR,
    interval: str = "8h",
    lookback: int = RATIO_LOOKBACK,
    zscore_window: int = ZSCORE_WINDOW,
    ratio_clip: float = RATIO_CLIP,
    zscore_clip: float = ZSCORE_CLIP,
) -> pd.DataFrame:
    """Add cross-BTC ratio features to the kline DataFrame.

    Dispatches on ``symbol``:

    - **DOTUSDT**: computes ``dot_vs_btc_ret_ratio_30`` (iter-v1/050). Loads BTC klines from
      ``data_dir/BTCUSDT/<interval>.csv``, aligns by ``open_time``, computes ratio.
      Adds NaN ``eth_vs_btc_ret_ratio_30`` and ``ltc_vs_btc_ret_ratio_30`` columns for
      V1_FEATURE_COLUMNS_PRUNED compliance.
    - **ETHUSDT**: computes ``eth_vs_btc_ret_ratio_30`` (iter-v1/055). Same loading/alignment.
      Adds NaN ``dot_vs_btc_ret_ratio_30`` and ``ltc_vs_btc_ret_ratio_30`` columns for
      V1_FEATURE_COLUMNS_PRUNED compliance.
    - **LTCUSDT**: computes ``ltc_vs_btc_ret_ratio_30`` (iter-v1/057). Same loading/alignment.
      Adds NaN ``dot_vs_btc_ret_ratio_30`` and ``eth_vs_btc_ret_ratio_30`` columns for
      V1_FEATURE_COLUMNS_PRUNED compliance.
    - **All other symbols**: all three columns added as NaN (no feature applies; columns must
      still exist for V1_FEATURE_COLUMNS_PRUNED compliance at model training time).

    Parameters
    ----------
    df:
        Kline DataFrame with ``symbol``, ``open_time``, and ``close`` columns.
    data_dir:
        Root data directory (default ``data/``). BTC klines read from
        ``data_dir/BTCUSDT/<interval>.csv``.
    interval:
        Kline interval string (default ``8h``).
    lookback:
        Bars for pct_change computation (default 30).
    zscore_window:
        Bars for rolling z-score (default 90).
    ratio_clip:
        Raw ratio clip before z-scoring (default 10.0).
    zscore_clip:
        Final z-score clip (default 10.0).

    Returns
    -------
    pd.DataFrame
        Copy of ``df`` with ``dot_vs_btc_ret_ratio_30``, ``eth_vs_btc_ret_ratio_30``,
        and ``ltc_vs_btc_ret_ratio_30`` columns appended.

    Raises
    ------
    KeyError:
        If ``df`` is missing a required column (``symbol``, ``open_time``, ``close``).
    FileNotFoundError:
        If BTC kline CSV is not found at the expected path for DOT, ETH, or LTC symbol.
        (Not raised for other symbols — NaN columns added silently.)

    Notes
    -----
    Alignment: merges BTC closes onto the symbol frame by ``open_time`` (ms int left-join).
    Rows in df that have no matching BTC bar (e.g. missing BTC data) produce NaN.
    """
    data_dir = Path(data_dir)

    for col in ("symbol", "open_time", "close"):
        if col not in df.columns:
            raise KeyError(
                f"df must contain '{col}' column for cross_btc_v1 feature group. "
                f"Available columns: {list(df.columns)}"
            )

    symbol = df["symbol"].iloc[0]
    df = df.copy()

    if symbol == TARGET_SYMBOL:
        # DOTUSDT: compute dot_vs_btc_ret_ratio_30; ETH and LTC columns are NaN
        df_btc_aligned = _load_btc_aligned(df, data_dir, interval)
        zscore_series = compute_dot_vs_btc_ret_ratio_30(
            df_dot=df,
            df_btc=df_btc_aligned,
            lookback=lookback,
            zscore_window=zscore_window,
            ratio_clip=ratio_clip,
            zscore_clip=zscore_clip,
        )
        df[FEATURE_COLUMN] = zscore_series.values
        df[ETH_FEATURE_COLUMN] = np.nan
        df[LTC_FEATURE_COLUMN] = np.nan

    elif symbol == ETH_TARGET_SYMBOL:
        # ETHUSDT: compute eth_vs_btc_ret_ratio_30 (iter-v1/055); DOT and LTC columns are NaN
        df_btc_aligned = _load_btc_aligned(df, data_dir, interval)
        zscore_series = compute_eth_vs_btc_ret_ratio_30(
            df_eth=df,
            df_btc=df_btc_aligned,
            lookback=lookback,
            zscore_window=zscore_window,
            ratio_clip=ratio_clip,
            zscore_clip=zscore_clip,
        )
        df[ETH_FEATURE_COLUMN] = zscore_series.values
        df[FEATURE_COLUMN] = np.nan
        df[LTC_FEATURE_COLUMN] = np.nan

    elif symbol == LTC_TARGET_SYMBOL:
        # LTCUSDT: compute ltc_vs_btc_ret_ratio_30 (iter-v1/057); DOT and ETH columns are NaN
        df_btc_aligned = _load_btc_aligned(df, data_dir, interval)
        zscore_series = compute_ltc_vs_btc_ret_ratio_30(
            df_ltc=df,
            df_btc=df_btc_aligned,
            lookback=lookback,
            zscore_window=zscore_window,
            ratio_clip=ratio_clip,
            zscore_clip=zscore_clip,
        )
        df[LTC_FEATURE_COLUMN] = zscore_series.values
        df[FEATURE_COLUMN] = np.nan
        df[ETH_FEATURE_COLUMN] = np.nan

    else:
        # Non-DOT, non-ETH, non-LTC symbols: all three columns are NaN
        df[FEATURE_COLUMN] = np.nan
        df[ETH_FEATURE_COLUMN] = np.nan
        df[LTC_FEATURE_COLUMN] = np.nan

    return df


# ---------------------------------------------------------------------------
# BTC realized vol helper (for vol-spike regime gate in runner)
# ---------------------------------------------------------------------------


def compute_btc_realized_vol_30(
    btc_close: pd.Series,
    window: int = 30,
) -> pd.Series:
    """Compute BTC 30-bar rolling realized volatility from log returns.

    Used by the vol-spike regime gate in ``run_iteration_050.py`` to compute
    the IS q75 training-data threshold.

    Parameters
    ----------
    btc_close:
        BTC close price series (aligned to kline open_times).
    window:
        Rolling window in bars (default 30 = 10 days at 8h).

    Returns
    -------
    pd.Series
        Rolling std of log returns, past-only (min_periods=window).
        First window-1 rows are NaN.

    Notes
    -----
    Past-only: log-return at bar t = log(close[t]/close[t-1]) — uses only past prices.
    Rolling std at bar t = std(log_ret[t-window+1]...log_ret[t]) — past only.
    No shift needed — the runner uses this for post-prediction gate (reads feature
    row at bar t to gate prediction for bar t+1).
    """
    log_ret = np.log(btc_close / btc_close.shift(1))
    return log_ret.rolling(window=window, min_periods=window).std()


__all__ = [
    "RATIO_LOOKBACK",
    "ZSCORE_WINDOW",
    "RATIO_CLIP",
    "ZSCORE_CLIP",
    "FEATURE_COLUMN",
    "ETH_FEATURE_COLUMN",
    "LTC_FEATURE_COLUMN",
    "TARGET_SYMBOL",
    "ETH_TARGET_SYMBOL",
    "LTC_TARGET_SYMBOL",
    "BTC_SYMBOL",
    "compute_dot_vs_btc_ret_ratio_30",
    "compute_eth_vs_btc_ret_ratio_30",
    "compute_ltc_vs_btc_ret_ratio_30",
    "add_cross_btc_v1_features",
    "compute_btc_realized_vol_30",
]
