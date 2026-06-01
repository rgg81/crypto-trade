"""v1 statistical higher-moment features — iter-v1/047 (feature-family EXPLORATION cycle-6 2/10).

Track-isolated: ZERO imports from crypto_trade.features_v2 or crypto_trade.features_v3.

Feature exported:
  - ``skew_zscore_21``: rolling-21bar realized skewness (unbiased G1 estimator, scipy.stats.skew
    with bias=False), z-normalized over a rolling 90-bar window.

Feature definition (canonical):

    log_returns[t]   = log(close[t] / close[t-1])
    skew_21bar[t]    = G1(log_returns[t-20:t+1])   (21 bars ending AT t; unbiased, bias=False)
    skew_mean_90[t]  = mean(skew_21bar[t-89:t+1])  (90-bar rolling mean of skew_21bar)
    skew_std_90[t]   = std(skew_21bar[t-89:t+1])   (90-bar rolling std of skew_21bar)
    skew_zscore_21[t]= (skew_21bar[t] - skew_mean_90[t]) / skew_std_90[t]

Decision at candle t+1 uses skew_zscore_21[t]. No look-ahead.

EDA finding (iter-v1/047 Section 2.1):
    21-bar inner window = 7 calendar days at 8h cadence.
    90-bar z-norm window = 30 calendar days (matches funding_rate_zscore_30 convention).
    Warmup: first 21 + 90 - 1 = 110 bars are NaN.

Stationarity:
    ADF p-value < 1e-9 expected for all 5 v1 IS symbols (z-score of bounded-3rd-moment
    statistic; documented in Section 2.2 EDA artifact).

Past-only discipline:
    - log_returns[t] uses close[t] / close[t-1] via .shift(1) — no future leak.
    - skew_21bar[t] = rolling(21).apply(...) uses only bars [t-20, t].
    - skew_mean_90[t] and skew_std_90[t] use only bars [t-89, t] of skew_21bar.
    Verified by tests/test_iteration_v1_047.py::test_past_only.

Track isolation enforcement:
    Phase 6.0 pre-flight Critic verifies:
        grep -r "from crypto_trade.features_v2" src/crypto_trade/features_v1/
        grep -r "from crypto_trade.features_v3" src/crypto_trade/features_v1/
    Both must return empty. This module has ZERO such imports.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import scipy.stats as st


def compute_skew_zscore_21(
    df: pd.DataFrame,
    skew_window: int = 21,
    znorm_window: int = 90,
) -> pd.DataFrame:
    """Append ``skew_zscore_21`` to *df*. Past-only. Returns df with column added.

    Parameters
    ----------
    df:
        Kline DataFrame with at least ``close`` (float-castable) column.
    skew_window:
        Rolling window in bars for the realized skewness computation (default 21 = 7 days at 8h).
    znorm_window:
        Rolling window in bars for z-normalization of the skew series (default 90 = 30 days at 8h).

    Returns
    -------
    pd.DataFrame
        Copy of ``df`` with ``skew_zscore_21`` column appended.
        First ``skew_window + znorm_window - 1`` rows are NaN (burn-in).

    Notes
    -----
    Past-only by construction:
    - log_returns[t] = log(close[t] / close[t-1]) via .shift(1) — no future close accessed.
    - skew_21bar[t] = G1(log_returns[t-skew_window+1:t+1]) — rolling ending AT t.
    - skew_mean_90[t], skew_std_90[t] = stats of skew_21bar[t-znorm_window+1:t+1].

    scipy.stats.skew with bias=False uses the G1 unbiased sample-skewness estimator:
        G1 = (n / ((n-1)(n-2))) * Σ((xi - x̄) / s)^3
    where s is the sample standard deviation (ddof=1).
    """
    df = df.copy()
    close = df["close"].astype(float)

    log_returns = np.log(close / close.shift(1))

    skew_series = log_returns.rolling(window=skew_window, min_periods=skew_window).apply(
        lambda x: st.skew(x, bias=False), raw=True
    )

    skew_mean = skew_series.rolling(window=znorm_window, min_periods=znorm_window).mean()
    skew_std = skew_series.rolling(window=znorm_window, min_periods=znorm_window).std()

    df["skew_zscore_21"] = (skew_series - skew_mean) / skew_std
    return df


def add_statistical_v1_features(
    df: pd.DataFrame,
    skew_window: int = 21,
    znorm_window: int = 90,
) -> pd.DataFrame:
    """Registry wrapper: add all v1 statistical higher-moment features to ``df``.

    Currently adds: ``skew_zscore_21``.

    Called by the v1 features registry (features/__init__.py GROUP_REGISTRY)
    via ``uv run crypto-trade features --track v1 --groups statistical_v1``.

    Parameters
    ----------
    df:
        Kline DataFrame with at least ``close`` (float-castable) column.
    skew_window:
        Rolling skew window in bars (default 21 = 7 days at 8h cadence).
    znorm_window:
        Z-normalization window in bars (default 90 = 30 days at 8h cadence).

    Returns
    -------
    pd.DataFrame
        Input df with ``skew_zscore_21`` column appended.
    """
    return compute_skew_zscore_21(df, skew_window=skew_window, znorm_window=znorm_window)


__all__ = [
    "compute_skew_zscore_21",
    "add_statistical_v1_features",
]
