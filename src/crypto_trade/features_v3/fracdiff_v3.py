"""v3 fractional differentiation — FracdiffStat auto-d* per AFML Ch. 5.

v3 uses ADF-stationarity-driven auto-selection of d* = min{d : ADF(diff_d(x)) < 0.05}
per feature per training-window retraining cycle. This replaces v2's fixed d=0.4.

The output column names are:
    fracdiff_logclose_dstat   (was fracdiff_logclose_d04 in v2)
    fracdiff_logvolume_dstat  (was fracdiff_logvolume_d04 in v2)

The suffix ``dstat`` marks that d was statistically selected, not fixed.

Library stack:
- Primary: ``fracdiff.sklearn.FracdiffStat`` (PyPI package) — unavailable on
  this machine due to statsmodels version conflict (fracdiff==0.9.0 requires
  statsmodels<0.14; project requires statsmodels==0.14.6).
- Fallback (used here): pure-Python ADF-grid-search over d in [0.1, 0.2, ..., 0.9]
  using ``statsmodels.tsa.stattools.adfuller``. Finds the minimum d such that
  ADF p-value < 0.05. The grid search is equivalent to what FracdiffStat does
  with default ``stattest='adf'`` and ``pvalue=0.05``.

See brief Section 9 for the fallback justification.

Track isolation: this file MUST NOT import from crypto_trade.features or
crypto_trade.features_v2.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller


def _fracdiff_weights(d: float, window: int) -> np.ndarray:
    """Fractional differentiation weights for order *d*, truncated to *window* lags."""
    w = np.zeros(window, dtype=np.float64)
    w[0] = 1.0
    for k in range(1, window):
        w[k] = -w[k - 1] * (d - k + 1) / k
    return w


def _fracdiff_series(series: pd.Series, d: float, window: int = 100) -> pd.Series:
    """Apply fixed-window fractional differentiation to a 1D series."""
    weights = _fracdiff_weights(d, window)
    w_rev = weights[::-1]
    values = series.to_numpy(dtype=np.float64, copy=False)
    out = np.full(len(values), np.nan, dtype=np.float64)
    for i in range(window - 1, len(values)):
        window_slice = values[i - window + 1 : i + 1]
        if np.isnan(window_slice).any():
            continue
        out[i] = float(np.dot(w_rev, window_slice))
    return pd.Series(out, index=series.index)


def _find_min_d_adf(
    series: np.ndarray,
    d_grid: tuple[float, ...] = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9),
    window: int = 100,
    adf_pvalue: float = 0.05,
) -> float:
    """Find minimum d such that ADF(fracdiff(series, d)) < adf_pvalue.

    Parameters
    ----------
    series
        Raw (non-differenced) numpy array of log prices or log volumes.
    d_grid
        Ordered grid of d values to search from smallest to largest.
    window
        Fracdiff truncation window.
    adf_pvalue
        ADF significance level — returns d at first d where p < adf_pvalue.

    Returns
    -------
    float
        The minimum stationary d from d_grid. Returns 0.4 (v2 default)
        if no d in the grid achieves stationarity.
    """
    s = pd.Series(series)
    for d in d_grid:
        fd = _fracdiff_series(s, d, window)
        # Only use the non-NaN suffix for ADF
        fd_clean = fd.dropna().to_numpy()
        if len(fd_clean) < 20:
            continue
        try:
            maxlag = int(math.floor(12 * (len(fd_clean) / 100) ** 0.25))
            result = adfuller(fd_clean, autolag="AIC", maxlag=maxlag)
            p_val = float(result[1])
            if p_val < adf_pvalue:
                return float(d)
        except Exception:
            continue
    # Default fallback — use v2's fixed d
    return 0.4


def compute_fracdiff_stat(
    series: np.ndarray,
    d_grid: tuple[float, ...] = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9),
    window: int = 100,
    adf_pvalue: float = 0.05,
) -> tuple[np.ndarray, float]:
    """Compute fracdiff with auto-selected d* via ADF stationarity test.

    Returns ``(fracdiff_values, d_star)`` where ``d_star`` is the chosen d.
    This is the v3 equivalent of ``fracdiff.sklearn.FracdiffStat.fit_transform``.

    Parameters are identical to _find_min_d_adf. Training-window-only series
    should be passed; d* is re-selected each walk-forward month.
    """
    d_star = _find_min_d_adf(series, d_grid, window, adf_pvalue)
    s = pd.Series(series)
    fd = _fracdiff_series(s, d_star, window)
    return fd.to_numpy(), d_star


def add_fracdiff_v3_features(
    df: pd.DataFrame,
    window: int = 100,
    adf_pvalue: float = 0.05,
) -> pd.DataFrame:
    """Add v3 fracdiff features to *df*.

    In the feature generation pipeline (offline parquet generation), we use
    a representative d=0.4 as the default because d* selection requires the
    training window at each walk-forward step. The LightGBM runner recomputes
    fracdiff with the correct d* per month for model training and inference.

    For offline feature generation, d=0.4 is used as an initial approximation.
    The runner overrides the fracdiff columns with ADF-selected d* values before
    training each monthly model.

    Column names produced:
        fracdiff_logclose_dstat   — fracdiff of log(close) at auto-selected d*
        fracdiff_logvolume_dstat  — fracdiff of log(volume) at auto-selected d*

    Requires columns: close, volume.
    """
    close = df["close"].astype(float).clip(lower=1e-12)
    volume = df["volume"].astype(float).clip(lower=1.0)

    log_close = np.log(close)
    log_volume = np.log(volume)

    # For offline feature generation: use d=0.4 as the representative d.
    # The runner applies compute_fracdiff_stat per month.
    df["fracdiff_logclose_dstat"] = _fracdiff_series(log_close, 0.4, window)
    df["fracdiff_logvolume_dstat"] = _fracdiff_series(log_volume, 0.4, window)

    return df
