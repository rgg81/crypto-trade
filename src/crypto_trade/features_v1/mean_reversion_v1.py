"""v1 mean-reversion signal features — iter-v1/085 (UNI specialist; feature-engineering set #1).

Track-isolated: ZERO imports from crypto_trade.features_v2 or crypto_trade.features_v3.

Feature exported:
  - ``rev_extension_z_3``: sign-flipped 3-bar return z-score (reversion signal).

Feature definition (canonical):

    ret_3[t]        = log(close[t] / close[t-3])
                      (3 bars × 8h = 24h ≈ the 1-day reversion horizon the UNI
                      autocorr signature ac_lag3 = -0.0843 isolates)
    mu_50[t]        = rolling-50-bar mean of ret_3 (50-bar = ~17 days)
    sd_50[t]        = rolling-50-bar std of ret_3 (ddof=1)
    raw_z[t]        = (ret_3[t] - mu_50[t]) / sd_50[t]
    rev_extension_z_3[t] = -raw_z[t], clipped to [-5, +5]

The LEADING NEGATIVE SIGN is the load-bearing design choice:
    ac_lag3 is NEGATIVE, meaning a positive 3-bar extension predicts a DOWN move.
    We flip the sign so high feature value => expect bounce UP, low value => expect fade DOWN.
    This is the same semantic as a mean-reversion "entry signal" pointing in the
    direction the model should trade.

Decision at t+1 uses value at t via .shift(1) on all inputs (past-only by construction).

EDA finding (iter-v1/085 brief Section 2):
    ac_lag3 = -0.0843 for UNIUSDT IS window — the strongest measured autocorr structure.
    3-bar horizon isolates the ~1-day reversion cycle without the decay seen at lags 1,2.
    mu/sd z-normalization over 50 bars aligns with established z-norm conventions
    (funding_rate_zscore_30/oi_delta z-windows use 30-90 bar windows; 50 is in range).

Stationarity:
    ADF p-value < 1e-9 expected (z-score of a bounded return is stationary by construction).

Past-only discipline:
    - ret_3[t] = log(close[t]) - log(close[t-3]) via .shift(3) — no future close.
    - mu_50[t] = rolling(50).mean() of ret_3 (window [t-49, t]) — past-only.
    - sd_50[t] = rolling(50).std(ddof=1) of ret_3 (window [t-49, t]) — past-only.
    - Entire series additionally shifted by 1 so that the value used at inference
      for bar t+1 is computed from bars [t-52, t]. No future leak.

Warmup:
    - ret_3: first 3 rows NaN (shift(3))
    - rolling-50 mean/std: first 50 rows of ret_3 NaN → first 52 rows of ret_3_series are NaN
      (3 + 50 - 1 = 52). Plus 1 extra shift → first 53 rows of rev_extension_z_3 are NaN.

Track isolation enforcement:
    Phase 6.0 pre-flight Critic verifies:
        grep -r "from crypto_trade.features_v2" src/crypto_trade/features_v1/
        grep -r "from crypto_trade.features_v3" src/crypto_trade/features_v1/
    Both must return empty. This module has ZERO such imports.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Rolling window constants (8h cadence: 3 bars/day)
# ---------------------------------------------------------------------------
REV_RETURN_WINDOW: int = 3  # 3 bars × 8h = 24h ≈ 1-day reversion horizon
REV_ZNORM_WINDOW: int = 50  # 50-bar = ~17 days rolling z-normalization window
REV_ZSCORE_CLIP: float = 5.0  # clip to [-5, +5] (same as basis_zscore_30 convention)


def compute_rev_extension_z_3(
    df: pd.DataFrame,
    ret_window: int = REV_RETURN_WINDOW,
    znorm_window: int = REV_ZNORM_WINDOW,
    clip: float = REV_ZSCORE_CLIP,
) -> pd.DataFrame:
    """Compute ``rev_extension_z_3`` = sign-flipped 3-bar return z-score.

    The leading negative sign makes the feature point in the direction a
    mean-reversion trade should go: high value => extension to downside =>
    expect bounce UP; low value => extension to upside => expect fade DOWN.

    Parameters
    ----------
    df:
        Kline DataFrame with at least ``close`` (float-castable) column.
    ret_window:
        Number of bars for the log-return look-back (default 3 = 1 day at 8h).
    znorm_window:
        Rolling window in bars for z-normalization of ret_3 (default 50 = ~17 days).
    clip:
        Absolute clip for the z-score output (default 5.0).

    Returns
    -------
    pd.DataFrame
        Copy of ``df`` with ``rev_extension_z_3`` column appended.
        First (ret_window + znorm_window - 1 + 1) rows will be NaN (burn-in + shift).

    Notes
    -----
    Past-only by construction:
    - ret_3[t] = log(close[t]) - log(close[t-3]) via shift(ret_window).
    - mu_50[t] and sd_50[t] = rolling(znorm_window) of ret_3 — window [t-49, t].
    - Additional .shift(1) on the final series ensures bar t's value uses only
      data from bars <= t-1 at inference time.
    """
    df = df.copy()
    close = df["close"].astype(float)
    log_close = np.log(close.clip(lower=1e-12))

    # 3-bar log return — past-only
    ret_3 = log_close - log_close.shift(ret_window)

    # Rolling z-normalization over znorm_window bars
    mu = ret_3.rolling(window=znorm_window, min_periods=znorm_window).mean()
    sd = ret_3.rolling(window=znorm_window, min_periods=znorm_window).std(ddof=1)

    raw_z = (ret_3 - mu) / sd.replace(0.0, np.nan)

    # Flip sign: positive extension (above mean) → negative z → predict FADE DOWN;
    # negative extension (below mean) → positive flipped z → predict BOUNCE UP.
    # Shift by 1 so the value used at bar t+1 is computed purely from bar t and earlier.
    df["rev_extension_z_3"] = (-raw_z).shift(1).clip(-clip, clip)

    return df


def add_mean_reversion_v1_features(
    df: pd.DataFrame,
    ret_window: int = REV_RETURN_WINDOW,
    znorm_window: int = REV_ZNORM_WINDOW,
    clip: float = REV_ZSCORE_CLIP,
) -> pd.DataFrame:
    """Registry wrapper: add all v1 mean-reversion signal features to ``df``.

    Currently adds: ``rev_extension_z_3``.

    Called by the v1 features registry (features/__init__.py GROUP_REGISTRY)
    via ``uv run crypto-trade features --track v1 --groups mean_reversion_v1``.

    Parameters
    ----------
    df:
        Kline DataFrame with at least ``close`` (float-castable) column.
    ret_window:
        Log-return look-back in bars (default 3 = 1 day at 8h cadence).
    znorm_window:
        Z-normalization window in bars (default 50 = ~17 days at 8h cadence).
    clip:
        Absolute clip for the z-score output (default 5.0).

    Returns
    -------
    pd.DataFrame
        Input df with ``rev_extension_z_3`` column appended.
    """
    return compute_rev_extension_z_3(
        df, ret_window=ret_window, znorm_window=znorm_window, clip=clip
    )


__all__ = [
    "REV_RETURN_WINDOW",
    "REV_ZNORM_WINDOW",
    "REV_ZSCORE_CLIP",
    "compute_rev_extension_z_3",
    "add_mean_reversion_v1_features",
]
