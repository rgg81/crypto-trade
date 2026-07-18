"""Breakout family signal forms (scratch reference implementation; QE re-implements)."""

from __future__ import annotations

import numpy as np
import pandas as pd


def donchian_state(close: pd.DataFrame, N: int, M: int) -> pd.DataFrame:
    """Form D: per-name Donchian state machine with hysteresis.

    entry_hi[t]=max(close[t-N..t-1]) (min_periods=N), entry_lo symmetric;
    exit_lo[t]=min(close[t-M..t-1]) (min_periods=M), exit_hi symmetric.
    Order per candle: exit first, then entry. NaN close -> state 0.
    """
    entry_hi = close.rolling(N, min_periods=N).max().shift(1).to_numpy()
    entry_lo = close.rolling(N, min_periods=N).min().shift(1).to_numpy()
    exit_lo = close.rolling(M, min_periods=M).min().shift(1).to_numpy()
    exit_hi = close.rolling(M, min_periods=M).max().shift(1).to_numpy()
    c = close.to_numpy()
    T, K = c.shape
    state = np.zeros((T, K), dtype=np.float64)
    prev = np.zeros(K, dtype=np.float64)
    for t in range(T):
        s = prev.copy()
        ct = c[t]
        dead = ~np.isfinite(ct)
        s[dead] = 0.0
        # exits (hysteresis channel)
        xl, xh = exit_lo[t], exit_hi[t]
        s[(s > 0) & np.isfinite(xl) & (ct < xl)] = 0.0
        s[(s < 0) & np.isfinite(xh) & (ct > xh)] = 0.0
        # entries (only from flat)
        eh, el = entry_hi[t], entry_lo[t]
        s[(s == 0) & np.isfinite(eh) & (ct > eh)] = 1.0
        s[(s == 0) & np.isfinite(el) & (ct < el)] = -1.0
        state[t] = s
        prev = s
    return pd.DataFrame(state, index=close.index, columns=close.columns)


def channel_pos(close: pd.DataFrame, N: int, d: float = 0.25) -> pd.DataFrame:
    """Form E: channel position in [-1,1] with deadband d (window includes t)."""
    hi = close.rolling(N, min_periods=N).max()
    lo = close.rolling(N, min_periods=N).min()
    rng = hi - lo
    c = (2.0 * (close - lo).div(rng) - 1.0).where(rng > 0, 0.0)
    s = np.sign(c) * ((c.abs() - d).clip(lower=0.0)) / (1.0 - d)
    return s
