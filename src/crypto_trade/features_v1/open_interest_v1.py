"""v1 open-interest delta features — iter-v1/025 (feature-family EXPLORATION #10/10 cycle-3).
iter-v1/058: added ``btc_oi_delta_5_z30`` (5-bar delta, 30-bar z-score; short-window companion).
iter-v1/084: added ``oi_price_divergence_30`` (OI-price divergence z-score; CRV specialist).

Track-isolated: ZERO imports from crypto_trade.features_v2 or crypto_trade.features_v3.
The OI compute math is COPIED (not imported) from the v3 derivatives panel logic to
maintain v1↔v3 isolation per the v1 track discipline.

Open interest (OI) is the total number of outstanding perpetual futures contracts.
OI delta measures the rate-of-change: persistent positive OI delta = leveraged-long
buildup (squeeze pressure); persistent negative OI delta = confirmed deleveraging
(momentum continuation). OI delta is z-scored over a 90-bar window to normalize
for secular OI growth (BTC OI in 2026 ~100k contracts vs 2020 ~40k).

Features exported:
  - ``oi_delta_30_z90``: 30-bar OI % change, z-scored over a 90-bar past-only window.
    This is the primary v1-025 feature. Raw oi_delta_30 is NOT added to avoid
    SAME-FAMILY same-window stacking (brief Section 3.3 /
    feedback_v3_engineered_features_dont_stack.md).
  - ``btc_oi_delta_5_z30``: 5-bar OI % change (40h horizon), z-scored over a 30-bar
    (10-day) past-only window. iter-v1/058 NEW feature. Targets rapid institutional
    positioning shifts not captured by the slower 30-bar accumulation window.
    Computed for ALL symbols (universal, not BTC-only), but only BTCUSDT is traded
    in /058 cohort. LightGBM handles NaN natively for non-BTC symbols.
    Burn-in: first 5 + 30 = 35 rows NaN (shorter than oi_delta_30_z90's 120 rows).
  - ``oi_price_divergence_30``: OI-price divergence z-score. iter-v1/084 NEW feature.
    Captures when OI and price DISAGREE on direction — signals crowding/squeeze risk.
    Hypothesis: when OI is rising but price is falling (OI-longs getting squeezed) or
    OI is falling but price rising (deleveraging rally), ML has edge vs trend-follower.
    Computation (all components past-only via .shift(1)):
      oi_delta_30 = sum_open_interest.pct_change(30)
      ret_30 = log(close).diff(30)
      div_raw = sign(oi_delta_30) - sign(ret_30)   ∈ {-2, 0, +2}
      oi_price_divergence_30 = z90(div_raw).shift(1)  where z90 = (x - rmean_90) / rstd_90
    Intermediate columns (oi_delta_30, ret_30, div_raw) NOT added to feature set;
    registered as NON_FEATURE intermediates.
    NaN warmup: ~120 bars (30 for delta + 90 for z-score).
    LightGBM handles NaN natively. Clip: [-10, +10] (same as other OI features).

Data source:
    ``data/open_interest/<SYMBOL>/8h.csv`` — cached CSV from /fapi/v1/openInterest.
    Schema: ``open_time`` (ms epoch int), ``sum_open_interest`` (float), ...
    The fetcher (``uv run crypto-trade fetch-oi --symbols ...``) writes this file.

Look-ahead discipline:
    OI delta at bar t uses ONLY past OI levels:
        oi_delta_30[t] = (oi[t] - oi[t-30]) / oi[t-30]
        oi_delta_5[t]  = (oi[t] - oi[t-5])  / oi[t-5]   (iter-v1/058)

    The z-score window uses ONLY past delta values via shift(1):
        z90[t] = (oi_delta_30[t] - mean(delta[t-90]...delta[t-1]))
                 / std(delta[t-90]...delta[t-1])
        z30[t] = (oi_delta_5[t]  - mean(delta5[t-30]...delta5[t-1]))
                 / std(delta5[t-30]...delta5[t-1])          (iter-v1/058)

    Past-only is enforced by:
    (a) oi_delta: the lookback uses .shift(lookback) — no bar-t value in denominator.
    (b) z-score rolling stats: uses s_shifted = oi_delta.shift(1), so bar t's own
        delta does NOT enter bar t's rolling stats.

    Unit-test ``tests/features_v1/test_open_interest_v1.py`` enforces this invariant.

Skip-month NaN policy (LM Master §5(a) ADOPTED):
    For calendar months where >50% of a symbol's OI delta values are NaN
    (typically the 2020-01 → 2020-09 window where Binance's OI archive
    had not started), the RUNNER excludes that symbol from that month's
    training fold. This avoids LightGBM synthesizing a curve-fit
    (symbol_dummy × NaN_indicator) interaction.

    The skip-month logic lives in the RUNNER (run_baseline_v1.py), not here.
    This module only produces the raw NaN where data is absent.

Outlier clipping:
    oi_delta_30: clipped to [-1.0, +5.0] (BTC OI floor approx; -100% = full unwind).
    oi_delta_5:  clipped to [-1.0, +5.0] (same clip convention as oi_delta_30).
    oi_delta_30_z90:           clipped to [-10, +10] to prevent LightGBM training instability.
    btc_oi_delta_5_z30:        clipped to [-10, +10] (same convention).
    oi_price_divergence_30:    clipped to [-10, +10] (same convention).

Burn-in:
    - oi_delta_30: first 30 rows NaN (lookback warm-up)
    - oi_delta_30_z90: first 30 + 90 = 120 rows NaN (delta warm-up + z-score warm-up)
    - oi_delta_5:  first 5 rows NaN (lookback warm-up)  (iter-v1/058)
    - btc_oi_delta_5_z30: first 5 + 30 = 35 rows NaN    (iter-v1/058)
    - oi_price_divergence_30: first 30 + 90 = 120 rows NaN (same as oi_delta_30_z90)  (iter-v1/084)

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

# Rolling window constants (8h cadence: 3 bars/day)
OI_DELTA_LOOKBACK: int = 30  # 10-day delta window (oi_delta_30_z90)
OI_ZSCORE_WINDOW: int = 90  # 30-day z-score window (oi_delta_30_z90)

# iter-v1/058: short-window companion constants
OI_DELTA_LOOKBACK_5: int = 5  # 40h delta window (btc_oi_delta_5_z30)
OI_ZSCORE_WINDOW_30: int = 30  # 10-day z-score window (btc_oi_delta_5_z30)

# Clip thresholds (shared between both features)
OI_DELTA_CLIP_LOW: float = -1.0  # -100% floor (full deleveraging)
OI_DELTA_CLIP_HIGH: float = 5.0  # +500% ceiling (extreme OI surge)
OI_ZSCORE_CLIP: float = 10.0  # z-score clip (same as funding_v1 convention)

# Column name for the iter-v1/058 short-window feature
OI_DELTA_5_Z30_COLUMN: str = "btc_oi_delta_5_z30"

# iter-v1/084: OI-price divergence z-score constants
OI_PRICE_DIV_ZSCORE_WINDOW: int = 90  # 30-day z-score window (matches OI_ZSCORE_WINDOW)
OI_PRICE_DIV_COLUMN: str = "oi_price_divergence_30"

# Default data directory for OI cache
_DEFAULT_DATA_DIR: Path = Path("data")


def compute_oi_delta_zscore(
    oi_series: pd.Series,
    delta_window: int = OI_DELTA_LOOKBACK,
    zscore_window: int = OI_ZSCORE_WINDOW,
    delta_clip_low: float = OI_DELTA_CLIP_LOW,
    delta_clip_high: float = OI_DELTA_CLIP_HIGH,
    zscore_clip: float = OI_ZSCORE_CLIP,
) -> pd.Series:
    """Compute past-only OI delta z-score from a raw OI level series.

    Parameters
    ----------
    oi_series:
        Raw OI level series (``sum_open_interest``), aligned to kline open_times.
        Index must be the integer position (0-based) or the kline DataFrame index.
    delta_window:
        Lookback window in bars for OI % change (default 30 = ~10 days at 8h).
    zscore_window:
        Rolling window in bars for z-score normalization (default 90 = ~30 days).
    delta_clip_low:
        Floor clip for raw delta (default -1.0 = -100%).
    delta_clip_high:
        Ceiling clip for raw delta (default +5.0 = +500%).
    zscore_clip:
        Absolute clip for the z-scored output (default 10.0).

    Returns
    -------
    pd.Series
        Past-only z-scored OI delta series. First (delta_window + zscore_window - 1)
        rows will be NaN due to rolling warm-up.

    Notes
    -----
    Look-ahead discipline:
    - oi_delta_30[t] = (oi[t] - oi[t-30]) / oi[t-30] uses .shift(delta_window).
      Bar t's delta uses only price levels at t and earlier — fully past-only.
    - z90 denominator uses s_shifted = oi_delta.shift(1): at bar t, the rolling
      mean/std see only bars t-zscore_window…t-1 (NOT bar t itself).
    """
    oi = oi_series.astype(float)

    # Step 1: 30-bar OI % change (past-only: shift(30) = oi[t-30])
    denom = oi.shift(delta_window).replace(0, np.nan)
    oi_delta = ((oi - oi.shift(delta_window)) / denom).clip(delta_clip_low, delta_clip_high)

    # Step 2: past-only 90-bar z-score
    # shift(1): at bar t, rolling stats see only bars t-zscore_window…t-1
    s_shifted = oi_delta.shift(1)
    rmean = s_shifted.rolling(window=zscore_window, min_periods=zscore_window).mean()
    rstd = s_shifted.rolling(window=zscore_window, min_periods=zscore_window).std(ddof=1)

    zscore = (oi_delta - rmean) / rstd.replace(0, np.nan)
    return zscore.clip(-zscore_clip, zscore_clip)


def add_oi_delta_v1_features(
    df: pd.DataFrame,
    data_dir: Path | str = _DEFAULT_DATA_DIR,
    delta_window: int = OI_DELTA_LOOKBACK,
    zscore_window: int = OI_ZSCORE_WINDOW,
    zscore_clip: float = OI_ZSCORE_CLIP,
) -> pd.DataFrame:
    """Load cached OI data for ``df``'s symbol and add oi_delta_30_z90 column.

    Appends ``oi_delta_30_z90`` to the DataFrame.
    Uses PAST-ONLY rolling delta + z-score computation.

    Parameters
    ----------
    df:
        Kline DataFrame with ``symbol`` and ``open_time`` (ms int) columns.
    data_dir:
        Root data directory (default ``data/``). Reads from
        ``data_dir/open_interest/<SYMBOL>/8h.csv``.
    delta_window:
        Lookback for OI % change (default 30 bars = ~10 days at 8h cadence).
    zscore_window:
        Rolling window for z-score normalization (default 90 bars = ~30 days).
    zscore_clip:
        Absolute clip for the z-score output (default 10.0).

    Returns
    -------
    pd.DataFrame
        Input df (copy) with ``oi_delta_30_z90`` column appended.
        Rows where OI data is absent (pre-archive-start) get NaN.
        First (delta_window + zscore_window - 1) rows are NaN by construction.

    Raises
    ------
    FileNotFoundError
        If the OI cache for the symbol does not exist.
        Run ``uv run crypto-trade fetch-oi --symbols <SYMBOL>`` first.
        NEVER silently fills NaN — echoes the /024 dispatch-defect lesson.
    KeyError
        If ``df`` does not contain the ``symbol`` column.

    Notes
    -----
    Alignment: OI cache open_time (ms epoch) must match kline open_time.
    Both are 8h-aligned Binance timestamps; no rounding needed for 8h bars.
    A direct integer merge on ``open_time`` is used (no jitter for OI data
    unlike funding rates which have ~10-15ms settlement jitter).

    Skip-month policy: The RUNNER (run_baseline_v1.py) excludes calendar months
    where >50% of a symbol's ``oi_delta_30_z90`` values are NaN from that
    symbol's training fold. This function produces NaN where data is absent;
    the skip-month decision is the runner's responsibility.
    """
    data_dir = Path(data_dir)

    if "symbol" not in df.columns:
        raise KeyError(
            "df must contain a 'symbol' column for open_interest_v1 feature group. "
            "Set df['symbol'] = '<SYMBOL>' before calling add_oi_delta_v1_features."
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
        df["oi_delta_30_z90"] = np.nan
        return df

    # ------------------------------------------------------------------
    # Align OI to kline frame via left-merge on open_time (ms int)
    # 8h bars are exactly aligned; no rounding needed unlike funding jitter.
    #
    # NOTE: ka.df (the source of df) has open_time as BOTH the datetime index
    # AND a millisecond-int column.  pandas raises:
    #   ValueError: 'open_time' is both an index level and a column label.
    # when merging on="open_time" in that situation.
    # Workaround: add a merge key column with a different name (_oi_merge_key),
    # merge on that, then drop it.  Mirrors the funding_v1 open_time_aligned
    # pattern (avoids resetting the index which would lose the datetime index).
    # ------------------------------------------------------------------
    df = df.copy()
    df["_oi_merge_key"] = df["open_time"].astype("int64")

    oi_df_keyed = oi_df[["open_time", "sum_open_interest"]].copy()
    oi_df_keyed["_oi_merge_key"] = oi_df_keyed["open_time"].astype("int64")

    merged = df.merge(
        oi_df_keyed[["_oi_merge_key", "sum_open_interest"]],
        on="_oi_merge_key",
        how="left",
    ).drop(columns=["_oi_merge_key"])

    # Restore original index alignment
    merged.index = df.index

    # Clean up the merge key from df (df is already a copy)
    df = df.drop(columns=["_oi_merge_key"])

    oi_series = merged["sum_open_interest"].astype(float)

    # Compute past-only OI delta z-score
    oi_delta_z90 = compute_oi_delta_zscore(
        oi_series,
        delta_window=delta_window,
        zscore_window=zscore_window,
        zscore_clip=zscore_clip,
    )

    df = df.copy()
    df["oi_delta_30_z90"] = oi_delta_z90.values

    return df


def add_oi_delta_5_z30_feature(
    df: pd.DataFrame,
    data_dir: Path | str = _DEFAULT_DATA_DIR,
    delta_window: int = OI_DELTA_LOOKBACK_5,
    zscore_window: int = OI_ZSCORE_WINDOW_30,
    zscore_clip: float = OI_ZSCORE_CLIP,
) -> pd.DataFrame:
    """Load cached OI data for ``df``'s symbol and add btc_oi_delta_5_z30 column.

    iter-v1/058: short-window companion to ``oi_delta_30_z90``.
    Computes 5-bar (40h) OI % change, z-scored over a 30-bar (10-day) past-only window.

    The feature is computed for ALL symbols (universal, not BTC-only). In the /058 runner,
    only BTCUSDT is traded. LightGBM handles NaN natively for non-BTC symbols in future
    multi-symbol contexts.

    Parameters
    ----------
    df:
        Kline DataFrame with ``symbol`` and ``open_time`` (ms int) columns.
    data_dir:
        Root data directory (default ``data/``). Reads from
        ``data_dir/open_interest/<SYMBOL>/8h.csv``.
    delta_window:
        Lookback for OI % change (default 5 bars = 40h at 8h cadence).
    zscore_window:
        Rolling window for z-score normalization (default 30 bars = 10 days).
    zscore_clip:
        Absolute clip for the z-score output (default 10.0).

    Returns
    -------
    pd.DataFrame
        Input df (copy) with ``btc_oi_delta_5_z30`` column appended.
        Rows where OI data is absent get NaN.
        First (delta_window + zscore_window - 1) rows are NaN by construction.

    Raises
    ------
    FileNotFoundError
        If the OI cache for the symbol does not exist.
    KeyError
        If ``df`` does not contain the ``symbol`` column.

    Notes
    -----
    Look-ahead discipline:
    - delta_5[t] = (oi[t] - oi[t-5]) / oi[t-5] uses .shift(delta_window) — past-only.
    - z30 uses s_shifted = oi_delta.shift(1): bar t's rolling stats see only
      bars t-zscore_window…t-1 (NOT bar t itself).
    This mirrors the exact past-only pattern in ``add_oi_delta_v1_features``.

    Burn-in: first 5 + 30 = 35 rows NaN (shorter than oi_delta_30_z90's 120 rows).
    """
    data_dir = Path(data_dir)

    if "symbol" not in df.columns:
        raise KeyError(
            "df must contain a 'symbol' column for open_interest_v1 btc_oi_delta_5_z30 feature. "
            "Set df['symbol'] = '<SYMBOL>' before calling add_oi_delta_5_z30_feature."
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
        df = df.copy()
        df[OI_DELTA_5_Z30_COLUMN] = np.nan
        return df

    # ------------------------------------------------------------------
    # Align OI to kline frame via left-merge on open_time (ms int).
    # Same pattern as add_oi_delta_v1_features to avoid index collisions.
    # ------------------------------------------------------------------
    df = df.copy()
    df["_oi5_merge_key"] = df["open_time"].astype("int64")

    oi_df_keyed = oi_df[["open_time", "sum_open_interest"]].copy()
    oi_df_keyed["_oi5_merge_key"] = oi_df_keyed["open_time"].astype("int64")

    merged = df.merge(
        oi_df_keyed[["_oi5_merge_key", "sum_open_interest"]],
        on="_oi5_merge_key",
        how="left",
    ).drop(columns=["_oi5_merge_key"])

    merged.index = df.index
    df = df.drop(columns=["_oi5_merge_key"])

    oi_series = merged["sum_open_interest"].astype(float)

    # Compute past-only OI delta z-score (5-bar delta, 30-bar z-score)
    oi_delta_5_z30 = compute_oi_delta_zscore(
        oi_series,
        delta_window=delta_window,
        zscore_window=zscore_window,
        zscore_clip=zscore_clip,
    )

    df = df.copy()
    df[OI_DELTA_5_Z30_COLUMN] = oi_delta_5_z30.values

    return df


def add_oi_price_divergence_30_feature(
    df: pd.DataFrame,
    data_dir: Path | str = _DEFAULT_DATA_DIR,
    delta_window: int = OI_DELTA_LOOKBACK,
    zscore_window: int = OI_PRICE_DIV_ZSCORE_WINDOW,
    zscore_clip: float = OI_ZSCORE_CLIP,
) -> pd.DataFrame:
    """Load cached OI data for ``df``'s symbol and add oi_price_divergence_30 column.

    iter-v1/084: OI-price direction divergence z-score.
    Captures the disagreement between OI delta direction and price return direction
    over a 30-bar (10-day) horizon, normalized via a 90-bar (30-day) z-score window.

    Parameters
    ----------
    df:
        Kline DataFrame with ``symbol``, ``open_time`` (ms int), and ``close`` columns.
    data_dir:
        Root data directory (default ``data/``). Reads from
        ``data_dir/open_interest/<SYMBOL>/8h.csv``.
    delta_window:
        Lookback for OI % change and log-return (default 30 bars = ~10 days at 8h).
    zscore_window:
        Rolling window for z-score normalization (default 90 bars = ~30 days).
    zscore_clip:
        Absolute clip for the z-score output (default 10.0).

    Returns
    -------
    pd.DataFrame
        Input df (copy) with ``oi_price_divergence_30`` column appended.
        Intermediate columns (oi_delta_30, ret_30, div_raw) are NOT retained.
        Rows where OI data is absent get NaN.
        First (delta_window + zscore_window - 1) rows are NaN by construction.

    Raises
    ------
    FileNotFoundError
        If the OI cache for the symbol does not exist.
    KeyError
        If ``df`` does not contain ``symbol`` or ``close`` columns.

    Notes
    -----
    Look-ahead discipline (all components past-only):
    - oi_delta_30[t] uses .pct_change(delta_window) — bar t vs bar t-30, past-only.
    - ret_30[t] = log(close[t]) - log(close[t-30]) via .diff(delta_window), past-only.
    - div_raw[t] = sign(oi_delta_30[t]) - sign(ret_30[t])  ∈ {-2, 0, +2}
    - z-score uses s_shifted = div_raw.shift(1): at bar t, rolling stats see only
      bars t-zscore_window…t-1 (NOT bar t itself) — additional past-only guard.
    - Final output = z-scored div_raw with extra .shift(1) so that bar t's feature
      uses at most bars up to t-1 in both the divergence and the z-score stats.

    NON_FEATURE intermediates (oi_delta_30, ret_30, div_raw): these intermediate
    values are computed internally and discarded. They must NOT appear as model
    feature columns per brief Section 3 (registered in NON_FEATURE_COLUMNS contract).
    """
    data_dir = Path(data_dir)

    if "symbol" not in df.columns:
        raise KeyError(
            "df must contain a 'symbol' column for oi_price_divergence_30 feature. "
            "Set df['symbol'] = '<SYMBOL>' before calling add_oi_price_divergence_30_feature."
        )
    if "close" not in df.columns:
        raise KeyError("df must contain a 'close' column for oi_price_divergence_30 feature.")

    symbol = df["symbol"].iloc[0]
    oi_path = data_dir / "open_interest" / symbol / "8h.csv"

    if not oi_path.exists():
        raise FileNotFoundError(
            f"OI cache not found: {oi_path}. "
            f"Run: uv run crypto-trade fetch-oi --symbols {symbol} --intervals 8h"
        )

    oi_df = pd.read_csv(oi_path)

    if len(oi_df) == 0:
        df = df.copy()
        df[OI_PRICE_DIV_COLUMN] = np.nan
        return df

    # ------------------------------------------------------------------
    # Align OI to kline frame via left-merge on open_time (ms int).
    # Same pattern as add_oi_delta_v1_features to avoid index collisions.
    # ------------------------------------------------------------------
    df = df.copy()
    df["_oidiv_merge_key"] = df["open_time"].astype("int64")

    oi_df_keyed = oi_df[["open_time", "sum_open_interest"]].copy()
    oi_df_keyed["_oidiv_merge_key"] = oi_df_keyed["open_time"].astype("int64")

    merged = df.merge(
        oi_df_keyed[["_oidiv_merge_key", "sum_open_interest"]],
        on="_oidiv_merge_key",
        how="left",
    ).drop(columns=["_oidiv_merge_key"])

    merged.index = df.index
    df = df.drop(columns=["_oidiv_merge_key"])

    oi_series = merged["sum_open_interest"].astype(float)
    close_series = df["close"].astype(float)

    # Step 1: 30-bar OI % change (past-only: close[t] vs close[t-30])
    denom = oi_series.shift(delta_window).replace(0, np.nan)
    oi_delta_30 = ((oi_series - oi_series.shift(delta_window)) / denom).clip(
        OI_DELTA_CLIP_LOW, OI_DELTA_CLIP_HIGH
    )

    # Step 2: 30-bar log return (past-only: log(close[t]) - log(close[t-30]))
    log_close = np.log(close_series.replace(0, np.nan))
    ret_30 = log_close.diff(delta_window)

    # Step 3: direction divergence raw
    # div_raw ∈ {-2, 0, +2} — nonzero only when OI and price disagree on direction
    oi_sign = np.sign(oi_delta_30)
    price_sign = np.sign(ret_30)
    div_raw = oi_sign - price_sign

    # Step 4: past-only 90-bar z-score of divergence
    # shift(1): at bar t, rolling stats see only bars t-zscore_window…t-1 (NOT bar t itself)
    s_shifted = div_raw.shift(1)
    rmean = s_shifted.rolling(window=zscore_window, min_periods=zscore_window).mean()
    rstd = s_shifted.rolling(window=zscore_window, min_periods=zscore_window).std(ddof=1)

    zscore_raw = (div_raw - rmean) / rstd.replace(0, np.nan)
    # Additional shift(1) ensures bar t's feature value uses only bars ≤ t-1
    zscore_final = zscore_raw.shift(1).clip(-zscore_clip, zscore_clip)

    df = df.copy()
    df[OI_PRICE_DIV_COLUMN] = zscore_final.values

    return df


__all__ = [
    "OI_DELTA_LOOKBACK",
    "OI_ZSCORE_WINDOW",
    "OI_DELTA_LOOKBACK_5",
    "OI_ZSCORE_WINDOW_30",
    "OI_DELTA_CLIP_LOW",
    "OI_DELTA_CLIP_HIGH",
    "OI_ZSCORE_CLIP",
    "OI_DELTA_5_Z30_COLUMN",
    "OI_PRICE_DIV_ZSCORE_WINDOW",
    "OI_PRICE_DIV_COLUMN",
    "compute_oi_delta_zscore",
    "add_oi_delta_v1_features",
    "add_oi_delta_5_z30_feature",
    "add_oi_price_divergence_30_feature",
]
