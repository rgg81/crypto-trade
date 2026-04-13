"""v2 fractional differentiation (AFML Ch. 5).

Computes fixed-window fractionally differentiated log(close) and log(volume).
The differencing order ``d`` defaults to 0.4 (typical for crypto close in 8h
bars), balancing stationarity against memory retention. The window is 100 so
weights beyond 100 lags are truncated — the truncation error is bounded by
the choice of ``d`` and windows <= 100 are effectively negligible.

Why ship fracdiff in v2: tree models still benefit from stationary features
with long-term memory (split points generalize across regimes). v1 tested
this inconclusively in iter 100; v2 treats it as a baseline feature.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _fracdiff_weights(d: float, window: int) -> np.ndarray:
    """Generate the fractional differentiation weights for the given d and window size.

    Weights are the binomial coefficients of (1-B)^d, i.e.
        w_0 = 1
        w_k = -w_{k-1} * (d - k + 1) / k
    """
    w = np.zeros(window, dtype=np.float64)
    w[0] = 1.0
    for k in range(1, window):
        w[k] = -w[k - 1] * (d - k + 1) / k
    return w


def _fracdiff_series(series: pd.Series, d: float, window: int) -> pd.Series:
    """Apply fixed-window fractional differentiation to a 1D series."""
    weights = _fracdiff_weights(d, window)
    # Weights are ordered from lag 0 → lag (window-1); reverse so np.dot aligns with window tail
    w_rev = weights[::-1]
    values = series.to_numpy(dtype=np.float64, copy=False)
    out = np.full(len(values), np.nan, dtype=np.float64)
    for i in range(window - 1, len(values)):
        window_slice = values[i - window + 1 : i + 1]
        if np.isnan(window_slice).any():
            continue
        out[i] = float(np.dot(w_rev, window_slice))
    return pd.Series(out, index=series.index)


def add_fracdiff_features(
    df: pd.DataFrame,
    d: float = 0.4,
    window: int = 100,
) -> pd.DataFrame:
    """Add v2 fracdiff features to *df*.

    Requires columns: close, volume.

    Parameters
    ----------
    d
        Differencing order. 0.4 is a reasonable crypto default; values of 0.3-0.5
        typically achieve ADF stationarity for 8h log close on major crypto pairs.
    window
        Fixed window size for truncated fracdiff. 100 keeps compute bounded.
    """
    close = df["close"].astype(float).clip(lower=1e-12)
    volume = df["volume"].astype(float).clip(lower=1.0)

    log_close = np.log(close)
    log_volume = np.log(volume)

    df[f"fracdiff_logclose_d{int(d * 10):02d}"] = _fracdiff_series(log_close, d, window)
    df[f"fracdiff_logvolume_d{int(d * 10):02d}"] = _fracdiff_series(log_volume, d, window)

    return df
