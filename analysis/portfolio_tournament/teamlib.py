"""teamlib — the ONLY module a crypto-cup-01 team strategy may import.

Pure metric helpers + grid constants. NO file access, NO network, NO tournament paths.
Self-contained on purpose (imports numpy/pandas only) so importing it can never pull in
evaluator internals; a parity test asserts the constants match ``constants.py``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

STEP_MS = 8 * 60 * 60 * 1000  # 8h candle grid
CANDLES_PER_YEAR = 1095  # 3 candles/day × 365


def msharpe(net: pd.Series, lo=None, hi=None) -> float:
    """Annualised Sharpe from MONTHLY summed returns over [lo, hi) (√12 annualisation).

    This is the tournament's LOCKED objective metric — use it instead of re-implementing.
    """
    s = net
    if lo is not None:
        s = s[s.index >= lo]
    if hi is not None:
        s = s[s.index < hi]
    g = s.groupby(s.index.to_period("M")).sum()
    return float(g.mean() / g.std() * np.sqrt(12)) if len(g) > 1 and g.std() > 0 else float("nan")


def maxdd(net: pd.Series) -> float:
    """Max drawdown of the compounded equity curve (negative fraction)."""
    eq = (1 + net).cumprod()
    return float((eq / eq.cummax() - 1).min())


def turnover(w: pd.DataFrame | pd.Series) -> float:
    """Mean per-candle gross turnover Σ|Δw|."""
    t = (w - w.shift(1)).abs()
    if isinstance(t, pd.DataFrame):
        t = t.sum(axis=1)
    return float(t.mean())
