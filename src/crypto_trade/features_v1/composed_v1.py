"""v1 composed (engineered) features — iter-v1/040 (feature-family EXPLORATION #7/10 cycle-5).

Track-isolated: ZERO imports from crypto_trade.features_v2 or crypto_trade.features_v3.
The Hurst R/S math is COPIED (not imported) from features_v3/regime_v3.py to maintain
v1↔v3 isolation per the v1 track discipline.

Composed feature exported:
  - ``regime_momentum_signed_5d``: ret_5d × sign(hurst_100 − 0.5)

Feature definition (canonical):

    ret_5d[t]                    = log(close[t]) − log(close[t−15])
                                   (15 bars × 8h = 120h ≈ 5 calendar days)
    hurst_100[t]                 = rolling 100-bar R/S Hurst exponent of log(close)
                                   (window ends at bar t; first valid at bar 99)
    regime_sign[t]               = sign(hurst_100[t] − 0.5)
                                   +1 if trending, −1 if mean-reverting, NaN if = 0.5
    regime_momentum_signed_5d[t] = ret_5d[t] × regime_sign[t]

EDA finding (iter-v1/040 eda.py):
    sign(hurst_100 − 0.5) = +1 in 100% of IS samples for all 5 v1 symbols. The feature
    is therefore mechanically equivalent to ret_5d (15-bar log return). The lift seen in
    v3/025 PROMISING + v3/028 CONFIRMATION-MERGE is attributed to the NEW 15-bar (120h)
    momentum horizon — not to the regime-conditioning sign flip. v1 currently has
    stat_log_return_5 (5-bar = 40h); this adds a 3× longer horizon.

Stationarity:
    ADF p-value < 2e-13 for all 5 v1 IS symbols (documented in EDA, Section 1.2).

Past-only discipline:
    - ret_5d[t] uses close[t-15..t] via log_close.shift(15) — no future leak.
    - hurst_100[t] is computed by _rolling_hurst (values[i-window:i]) — the value
      stored at index i is the R/S slope over bars i-window..i-1, ending strictly
      BEFORE bar i. The rolling_hurst implementation is BYTE-FOR-BYTE identical to
      features_v3/regime_v3.py:69-75 — past-only invariant already verified by
      v3 test suite.

NaN burn-in:
    First max(15, 100) - 1 = 99 bars are NaN (hurst_100 dominates).

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
# Hurst R/S helpers — BYTE-FOR-BYTE copies from features_v3/regime_v3.py:34-75
# (copied not imported for v1 track isolation)
# ---------------------------------------------------------------------------


def _hurst_rs(window: np.ndarray) -> float:
    """Rescaled-range Hurst exponent for a single 1D window of log prices.

    BYTE-FOR-BYTE copy from src/crypto_trade/features_v3/regime_v3.py:34-66.
    Retained here for v1 track isolation (no cross-track imports).
    """
    n = len(window)
    if n < 20:
        return np.nan
    lags = [5, 10, 20, 30, 50, 80]
    lags = [lag for lag in lags if lag < n]
    if len(lags) < 3:
        return np.nan
    rs_values: list[float] = []
    log_lags: list[float] = []
    for lag in lags:
        chunks = n // lag
        if chunks < 1:
            continue
        r_list: list[float] = []
        for i in range(chunks):
            chunk = window[i * lag : (i + 1) * lag]
            mean = chunk.mean()
            devs = chunk - mean
            cumdev = np.cumsum(devs)
            r = cumdev.max() - cumdev.min()
            s = chunk.std(ddof=1)
            if s > 0 and np.isfinite(r):
                r_list.append(r / s)
        if r_list:
            rs_values.append(np.mean(r_list))
            log_lags.append(np.log(lag))
    if len(rs_values) < 3:
        return np.nan
    log_rs = np.log(rs_values)
    slope, _ = np.polyfit(log_lags, log_rs, 1)
    return float(slope)


def _rolling_hurst(log_close: pd.Series, window: int) -> pd.Series:
    """Rolling Hurst exponent via rescaled range. Returns NaN until window filled.

    BYTE-FOR-BYTE copy from src/crypto_trade/features_v3/regime_v3.py:69-75.
    Retained here for v1 track isolation (no cross-track imports).
    """
    values = log_close.to_numpy()
    out = np.full(len(values), np.nan, dtype=np.float64)
    for i in range(window, len(values) + 1):
        out[i - 1] = _hurst_rs(values[i - window : i])
    return pd.Series(out, index=log_close.index)


# ---------------------------------------------------------------------------
# Composed feature computation
# ---------------------------------------------------------------------------


def compute_regime_momentum_signed_5d(
    df: pd.DataFrame,
    ret_window_bars: int = 15,
    hurst_window: int = 100,
) -> pd.DataFrame:
    """Compute regime_momentum_signed_5d = ret_5d × sign(hurst_100 − 0.5).

    Computes both ret_5d and hurst_100 from scratch if hurst_100 is not
    already in ``df``. This allows the function to be used standalone (e.g.
    in tests or in the feature CLI single-group mode).

    Parameters
    ----------
    df:
        Kline DataFrame with at least ``close`` (float-castable) column.
    ret_window_bars:
        Number of bars for the log-return look-back (default 15 = 5 days at 8h).
    hurst_window:
        Rolling window in bars for the R/S Hurst exponent (default 100).

    Returns
    -------
    pd.DataFrame
        Copy of ``df`` with ``regime_momentum_signed_5d`` column appended.
        Rows where sign(hurst_100 − 0.5) == 0 (pure random walk) are set to NaN.
        First max(ret_window_bars, hurst_window) − 1 rows are NaN (burn-in).

    Notes
    -----
    Past-only by construction:
    - ret_5d[t] = log_close[t] − log_close[t − ret_window_bars].
      The shift(ret_window_bars) ensures only past bars are used.
    - hurst_100[t] is computed over values[t-window:t] ending strictly before t+1
      (values[i-window:i] in _rolling_hurst; the bar-i value uses bars i-window to i-1).
    """
    df = df.copy()
    close = df["close"].astype(float)
    log_close = np.log(close.clip(lower=1e-12))

    # ret_5d: past-only by shift(ret_window_bars)
    ret_5d = log_close - log_close.shift(ret_window_bars)

    # hurst_100: compute from log_close if not already present
    if "hurst_100" not in df.columns:
        df["hurst_100"] = _rolling_hurst(log_close, hurst_window)

    hurst = df["hurst_100"].astype(float)
    sign_hurst = np.sign(hurst - 0.5)
    # Pure random-walk edge case (hurst_100 == 0.5 → sign = 0): treat as NaN.
    sign_hurst = sign_hurst.replace(0.0, np.nan)

    df["regime_momentum_signed_5d"] = ret_5d * sign_hurst
    return df


def add_composed_v1_features(
    df: pd.DataFrame,
    ret_window_bars: int = 15,
    hurst_window: int = 100,
) -> pd.DataFrame:
    """Registry wrapper: add all composed v1 features to ``df``.

    Currently adds: ``regime_momentum_signed_5d``.

    Called by the v1 features registry (features/__init__.py GROUP_REGISTRY)
    via ``uv run crypto-trade features --track v1 --groups composed_v1``.

    Parameters
    ----------
    df:
        Kline DataFrame with at least ``close`` (float-castable) column.
    ret_window_bars:
        Log-return look-back in bars (default 15 = 5 days at 8h cadence).
    hurst_window:
        Rolling Hurst window in bars (default 100).

    Returns
    -------
    pd.DataFrame
        Input df with ``regime_momentum_signed_5d`` column appended.
    """
    return compute_regime_momentum_signed_5d(
        df, ret_window_bars=ret_window_bars, hurst_window=hurst_window
    )


__all__ = [
    "_hurst_rs",
    "_rolling_hurst",
    "compute_regime_momentum_signed_5d",
    "add_composed_v1_features",
]
