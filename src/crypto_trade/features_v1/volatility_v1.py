"""v1 volatility state features — iter-v1/085 (UNI specialist; feature-engineering set #1).

Track-isolated: ZERO imports from crypto_trade.features_v2 or crypto_trade.features_v3.

Feature exported:
  - ``vol_state_z_natr_30``: z-normalized NATR-30 volatility state signal.

Feature definition (canonical):

    natr_30[t]          = 30-bar Normalized ATR (pandas_ta.natr length=30)
                          (exact window the UNI prescreen flagged; |IC|≈0.0386 with label)
    vmu_90[t]           = rolling-90-bar mean of natr_30 (90-bar = 30 calendar days)
    vsd_90[t]           = rolling-90-bar std of natr_30 (ddof=1; 90-bar window)
    vol_state_z_natr_30[t] = (natr_30[t] - vmu_90[t]) / vsd_90[t], clipped [-5, +5]

Rationale:
    Rather than re-add the raw natr_30 level (non-stationary, drifts with regime),
    z-normalizing lets the tree see a stationary 'how unusual is current vol vs recent
    history' signal.  ADF passes comfortably for z-score of a bounded NATR level.

EDA finding (iter-v1/085 brief Section 2):
    natr_30 IC with label ≈ 0.0386 (near the 0.04 secondary gate threshold).
    vol_bb_bandwidth_20 IC ≈ 0.0393 — two features near the gate; z-normalized form
    is preferred to preserve stationarity.

Past-only discipline:
    - natr_30[t] uses only past OHLC data (pandas_ta.natr is past-only by construction;
      ATR = exponentially smoothed TR over trailing window, no future bars used).
    - vmu_90[t] and vsd_90[t] = rolling(90) of natr_30 — window [t-89, t], past-only.
    - Additional .shift(1) on the final series so bar t's value uses only data ≤ t-1.

Warmup:
    natr_30: first 30 rows NaN (NATR ATR warm-up).
    vmu_90, vsd_90: first 90 rows of natr_30 → first 119 rows of natr_30 are NaN
    (30 + 90 - 1 = 119). Plus 1 extra shift → first 120 rows of vol_state_z_natr_30 NaN.

Track isolation enforcement:
    Phase 6.0 pre-flight Critic verifies:
        grep -r "from crypto_trade.features_v2" src/crypto_trade/features_v1/
        grep -r "from crypto_trade.features_v3" src/crypto_trade/features_v1/
    Both must return empty. This module has ZERO such imports.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pandas_ta as ta

# ---------------------------------------------------------------------------
# Rolling window constants (8h cadence: 3 bars/day)
# ---------------------------------------------------------------------------
VOL_NATR_WINDOW: int = 30  # NATR ATR window (matches UNI prescreen window)
VOL_ZNORM_WINDOW: int = 90  # z-normalization window = 30 calendar days
VOL_ZSCORE_CLIP: float = 5.0  # clip to [-5, +5]


def compute_vol_state_z_natr_30(
    df: pd.DataFrame,
    natr_window: int = VOL_NATR_WINDOW,
    znorm_window: int = VOL_ZNORM_WINDOW,
    clip: float = VOL_ZSCORE_CLIP,
) -> pd.DataFrame:
    """Compute ``vol_state_z_natr_30`` = z-normalized 30-bar NATR volatility state.

    Parameters
    ----------
    df:
        Kline DataFrame with ``high``, ``low``, ``close`` (float-castable) columns.
    natr_window:
        ATR window for NATR computation (default 30 bars = 10 days at 8h cadence).
    znorm_window:
        Rolling window for z-normalization of natr series (default 90 = 30 days).
    clip:
        Absolute clip for the z-score output (default 5.0).

    Returns
    -------
    pd.DataFrame
        Copy of ``df`` with ``vol_state_z_natr_30`` column appended.
        First (natr_window + znorm_window - 1 + 1) rows will be NaN (burn-in + shift).

    Notes
    -----
    Past-only by construction:
    - pandas_ta.natr uses only past OHLC — no future bars.
    - vmu_90 and vsd_90: rolling(znorm_window) of natr_30 — window [t-89, t].
    - Additional .shift(1) ensures bar t's value uses only data from bars <= t-1.
    """
    df = df.copy()
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    close = df["close"].astype(float)

    # 30-bar Normalized ATR (pandas_ta.natr; returns % of close)
    natr_series = ta.natr(high, low, close, length=natr_window)

    # Z-normalize over trailing 90-bar window
    vmu = natr_series.rolling(window=znorm_window, min_periods=znorm_window).mean()
    vsd = natr_series.rolling(window=znorm_window, min_periods=znorm_window).std(ddof=1)

    z = (natr_series - vmu) / vsd.replace(0.0, np.nan)

    # Shift by 1 so bar t's feature uses only data from bars <= t-1
    df["vol_state_z_natr_30"] = z.shift(1).clip(-clip, clip)

    return df


def add_volatility_v1_features(
    df: pd.DataFrame,
    natr_window: int = VOL_NATR_WINDOW,
    znorm_window: int = VOL_ZNORM_WINDOW,
    clip: float = VOL_ZSCORE_CLIP,
) -> pd.DataFrame:
    """Registry wrapper: add all v1 volatility state features to ``df``.

    Currently adds: ``vol_state_z_natr_30``.

    Called by the v1 features registry (features/__init__.py GROUP_REGISTRY)
    via ``uv run crypto-trade features --track v1 --groups volatility_v1``.

    Parameters
    ----------
    df:
        Kline DataFrame with ``high``, ``low``, ``close`` columns.
    natr_window:
        NATR ATR window in bars (default 30 = 10 days at 8h cadence).
    znorm_window:
        Z-normalization window in bars (default 90 = 30 days at 8h cadence).
    clip:
        Absolute clip for the z-score output (default 5.0).

    Returns
    -------
    pd.DataFrame
        Input df with ``vol_state_z_natr_30`` column appended.
    """
    return compute_vol_state_z_natr_30(
        df, natr_window=natr_window, znorm_window=znorm_window, clip=clip
    )


__all__ = [
    "VOL_NATR_WINDOW",
    "VOL_ZNORM_WINDOW",
    "VOL_ZSCORE_CLIP",
    "compute_vol_state_z_natr_30",
    "add_volatility_v1_features",
]
