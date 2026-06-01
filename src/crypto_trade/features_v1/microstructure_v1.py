"""v1 microstructure-primitive features — iter-v1/048 (feature-family EXPLORATION cycle-6 3/10).

Track-isolated: ZERO imports from crypto_trade.features_v2 or crypto_trade.features_v3.

Feature exported:
  - ``trade_count_zscore_30``: rolling-30bar z-score of the ``trades`` kline field
    (Binance kline field 8 = number of trades; exposed as ``trades`` in the kline
    DataFrame / ``models.Kline.trades``).

UNUSED-primitive defense: ``trades`` (number_of_trades) is the only major kline field
with ZERO feature-level descendants in V1_FEATURE_COLUMNS_PRUNED. Defends against the
/047 NEG-CLEAN-PRE-EDA algebraic-sister failure mode (skew_zscore_21 |IC|=0.81 vs
stat_skew_20).

Kline column mapping:
    Binance docs name  : ``number_of_trades``  (field index 8 in the REST response array)
    models.Kline field : ``trades``
    kline_array df col : ``trades``
    Feature uses       : ``df["trades"]``
    Feature name       : ``trade_count_zscore_30``

Past-only discipline verified by tests/test_iteration_v1_048.py::test_past_only.
ADF stationarity per-symbol verified by Section 2.2 EDA artifact.

Track isolation enforcement:
    Phase 6.0 pre-flight Critic verifies:
        grep -r "from crypto_trade.features_v2" src/crypto_trade/features_v1/
        grep -r "from crypto_trade.features_v3" src/crypto_trade/features_v1/
    Both must return empty. This module has ZERO such imports.
"""

from __future__ import annotations

import pandas as pd


def compute_trade_count_zscore_30(
    df: pd.DataFrame,
    window: int = 30,
) -> pd.DataFrame:
    """Append ``trade_count_zscore_30`` to df. Past-only. Returns df with column added.

    Parameters
    ----------
    df:
        Kline DataFrame with at least ``trades`` (int/float-castable) column.
        The ``trades`` column corresponds to Binance's ``number_of_trades`` kline
        field (REST array index 8; ``models.Kline.trades``).
    window:
        Rolling window in bars for mean, std, and z-score computation (default 30 =
        10 calendar days at 8h cadence; matches ``funding_rate_zscore_30`` /
        ``oi_delta_30_z90`` window conventions).

    Returns
    -------
    pd.DataFrame
        Input df (modified in-place) with ``trade_count_zscore_30`` column appended.
        First ``window`` rows are NaN (min_periods=window burn-in).

    Notes
    -----
    Past-only by construction:
    - ``tc[t]`` = ``df["trades"][t]`` uses only the CLOSED kline at time t.
    - ``tc_mean[t]`` and ``tc_std[t]`` = rolling stats of ``tc[t-window+1 : t+1]``
      (window bars ending AT t inclusive).
    - Decision at candle t+1 consumes ``trade_count_zscore_30[t]``.
    No future kline value is accessed.

    Scale-invariance:
    - Z-score normalization removes units; output is dimensionless (approx [-3, +3]
      under Gaussian assumptions; fat-tail regimes can exceed).

    Warmup:
    - First 30 bars per symbol are NaN (min_periods=30). At 8h cadence ≈ 10 calendar
      days. All v1 symbols have ≥4 years history; warmup loss is negligible.
    """
    tc = df["trades"].astype(float)
    tc_mean = tc.rolling(window=window, min_periods=window).mean()
    tc_std = tc.rolling(window=window, min_periods=window).std()
    df["trade_count_zscore_30"] = (tc - tc_mean) / tc_std
    return df


def add_microstructure_v1_features(
    df: pd.DataFrame,
    window: int = 30,
) -> pd.DataFrame:
    """Registry wrapper. Called by features registry via --groups microstructure_v1.

    Parameters
    ----------
    df:
        Kline DataFrame with ``trades`` column.
    window:
        Rolling window (default 30).

    Returns
    -------
    pd.DataFrame
        Input df with ``trade_count_zscore_30`` column appended.
    """
    return compute_trade_count_zscore_30(df, window=window)


__all__ = ["compute_trade_count_zscore_30", "add_microstructure_v1_features"]
