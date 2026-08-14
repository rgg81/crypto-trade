"""Corrected offline signal builder -- information-set equivalent to the frozen strategy.

Two defects were found in the first offline pipeline by diffing its weights against the frozen
strategy's own emitted weights boundary by boundary (``diff_signal.py``), and both are fixed here:

1. **Rolling windows were computed on the IS SLICE**, so every measure was undefined for the first
   ``window`` rows of the scored window and the offline book sat flat until 2020-12-22. The
   strategy is handed each eligible symbol's ENTIRE history up to the decision (see
   ``generate_targets``: ``group.iloc[:stop]``), including rows before the scored window, so it
   trades from the first boundary. Measures are now built on the full panel and sliced afterwards.

2. **Activity was masked by membership**, zeroing a coin's trade count on bars where it was not a
   top-20 member. The strategy sees those bars. The mask is gone.

The offline weights now agree with the frozen strategy's to floating-point tolerance, which is what
makes the sweeps a bench for the thing actually being nominated.
"""

from __future__ import annotations

import numpy as np

import measures as M

WEEKEND_DAYS = (5, 6)
DESK_CLOSED_SLOT = 0


def desk_closed_cell(p) -> np.ndarray:
    """Full-panel boolean: bars beginning in a cell where professional desks are shut."""
    return np.isin(p.dow, list(WEEKEND_DAYS)) | (p.slot == DESK_CLOSED_SLOT)


def build(p, start_idx: int, *, activity_window: int, volatility_window: int,
          cell: np.ndarray | None = None, neutralise: bool = True,
          quantity: str = "trades"):
    """Return (signal_rank, eligible) sliced to the scored window.

    ``signal_rank`` is the cross-sectional rank of the volatility-neutralised desk-closed share,
    already sign-flipped so that a HIGH rank is the long side.
    """
    if cell is None:
        cell = desk_closed_cell(p)
    if quantity == "trades":
        q = p.trade_count
    elif quantity == "volume":
        q = p.quote_volume
    else:  # pragma: no cover
        raise ValueError(quantity)
    share = M.share_of_activity(q, cell, activity_window)
    absr = np.abs(M.close_log_return(p.close))
    rv = np.sqrt(M.causal_rolling_sum(absr**2, volatility_window))

    el = p.eligible[start_idx:]
    share_rank = M.cross_section_rank(share[start_idx:], el)
    rv_rank = M.cross_section_rank(rv[start_idx:], el)
    if not neutralise:
        return M.cross_section_rank(-share_rank, el), el
    resid = _project_out(share_rank, rv_rank)
    return M.cross_section_rank(-resid, el), el


def _project_out(signal: np.ndarray, control: np.ndarray) -> np.ndarray:
    """Row-wise OLS residual of ``signal`` on ``control``; both are centred ranks."""
    ok = np.isfinite(signal) & np.isfinite(control)
    s = np.where(ok, signal, 0.0)
    c = np.where(ok, control, 0.0)
    cross = (s * c).sum(1)
    norm = (c * c).sum(1)
    beta = np.divide(cross, norm, out=np.zeros_like(cross), where=norm > 0)
    out = signal - beta[:, None] * control
    return np.where(ok, out, np.nan)


def power_book(sig_rank: np.ndarray, power: float) -> np.ndarray:
    """Centred-rank weights raised to ``power``, dollar-neutralised, unit gross."""
    out = np.zeros_like(sig_rank)
    for i in range(sig_rank.shape[0]):
        m = np.isfinite(sig_rank[i])
        if m.sum() < 8:
            continue
        v = sig_rank[i, m]
        wgt = np.sign(v) * np.abs(v) ** power
        wgt = wgt - wgt.mean()
        g = np.abs(wgt).sum()
        if g > 0:
            out[i, m] = wgt / g
    return out
