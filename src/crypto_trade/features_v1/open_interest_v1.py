"""v1 open-interest delta features — iter-v1/025 (feature-family EXPLORATION #10/10 cycle-3).

Track-isolated: ZERO imports from crypto_trade.features_v2 or crypto_trade.features_v3.
The OI compute math is COPIED (not imported) from the v3 derivatives panel logic to
maintain v1↔v3 isolation per the v1 track discipline.

Open interest (OI) is the total number of outstanding perpetual futures contracts.
OI delta measures the rate-of-change: persistent positive OI delta = leveraged-long
buildup (squeeze pressure); persistent negative OI delta = confirmed deleveraging
(momentum continuation). OI delta is z-scored over a 90-bar window to normalize
for secular OI growth (BTC OI in 2026 ~100k contracts vs 2020 ~40k).

Single feature exported:
  - ``oi_delta_30_z90``: 30-bar OI % change, z-scored over a 90-bar past-only window.
    This is the primary v1-025 feature. Raw oi_delta_30 is NOT added to avoid
    SAME-FAMILY same-window stacking (brief Section 3.3 /
    feedback_v3_engineered_features_dont_stack.md).

Data source:
    ``data/open_interest/<SYMBOL>/8h.csv`` — cached CSV from /fapi/v1/openInterest.
    Schema: ``open_time`` (ms epoch int), ``sum_open_interest`` (float), ...
    The fetcher (``uv run crypto-trade fetch-oi --symbols ...``) writes this file.

Look-ahead discipline:
    OI delta at bar t uses ONLY past OI levels:
        oi_delta_30[t] = (oi[t] - oi[t-30]) / oi[t-30]

    The 90-bar z-score uses ONLY past delta values via shift(1):
        z90[t] = (oi_delta_30[t] - mean(delta[t-90]...delta[t-1]))
                 / std(delta[t-90]...delta[t-1])

    Past-only is enforced by:
    (a) oi_delta_30: the 30-bar lookback uses .shift(lookback) — no bar-t value
        enters the denominator.
    (b) z90 rolling stats: the rolling mean/std uses s_shifted = oi_delta.shift(1),
        so bar t's own delta does NOT enter bar t's rolling stats.

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
    oi_delta_30_z90: clipped to [-10, +10] to prevent LightGBM training instability.

Burn-in:
    - oi_delta_30: first 30 rows NaN (lookback warm-up)
    - oi_delta_30_z90: first 30 + 90 = 120 rows NaN (delta warm-up + z-score warm-up)

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
OI_DELTA_LOOKBACK: int = 30  # 10-day delta window
OI_ZSCORE_WINDOW: int = 90  # 30-day z-score window

# Clip thresholds
OI_DELTA_CLIP_LOW: float = -1.0  # -100% floor (full deleveraging)
OI_DELTA_CLIP_HIGH: float = 5.0  # +500% ceiling (extreme OI surge)
OI_ZSCORE_CLIP: float = 10.0  # z-score clip (same as funding_v1 convention)

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
    # ------------------------------------------------------------------
    merged = df.merge(
        oi_df[["open_time", "sum_open_interest"]],
        on="open_time",
        how="left",
    )
    # Restore original index alignment
    merged.index = df.index

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


__all__ = [
    "OI_DELTA_LOOKBACK",
    "OI_ZSCORE_WINDOW",
    "OI_DELTA_CLIP_LOW",
    "OI_DELTA_CLIP_HIGH",
    "OI_ZSCORE_CLIP",
    "compute_oi_delta_zscore",
    "add_oi_delta_v1_features",
]
