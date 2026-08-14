"""Book construction: turn a calendar measure into a weight matrix, with every design axis
exposed as a parameter so the offline sweep can explore them without editing code.
"""

from __future__ import annotations

import numpy as np

import measures as M

SLOT_ASIA, SLOT_EURO, SLOT_US = 0, 1, 2


def session_share(panel, w, quantity: str, window: int, slots) -> np.ndarray:
    """Share of ``quantity`` a coin accumulates in the given clock cells over the past window."""
    el = panel.eligible[w]
    if quantity == "volume":
        q = np.where(el, panel.quote_volume[w], np.nan)
    elif quantity == "volatility":
        q = np.abs(M.close_log_return(panel.close[w]))
    elif quantity == "trades":
        q = np.where(el, panel.trade_count[w], np.nan)
    elif quantity == "range":
        hi, lo, cl = panel.high[w], panel.low[w], panel.close[w]
        q = (hi - lo) / np.where(cl > 0, cl, np.nan)
    else:  # pragma: no cover
        raise ValueError(quantity)
    mask = np.isin(panel.slot[w], list(slots))
    return M.share_of_activity(q, mask, window)


def weekend_share(panel, w, quantity: str, window: int) -> np.ndarray:
    el = panel.eligible[w]
    q = np.where(el, panel.quote_volume[w], np.nan) if quantity == "volume" else np.abs(
        M.close_log_return(panel.close[w])
    )
    mask = np.isin(panel.dow[w], [5, 6])
    return M.share_of_activity(q, mask, window)


def rank_book(
    signal: np.ndarray,
    eligible: np.ndarray,
    *,
    sign: float = 1.0,
    long_fraction: float = 0.30,
    short_fraction: float = 0.30,
    scheme: str = "rank",
) -> np.ndarray:
    """Cross-sectional long/short weights from a signal, dollar-neutral within each row."""
    r = M.cross_section_rank(signal * sign, eligible)
    n = r.shape[0]
    out = np.zeros_like(r)
    for i in range(n):
        m = np.isfinite(r[i])
        k = int(m.sum())
        if k < 8:
            continue
        v = r[i, m]
        if scheme == "rank":
            wgt = v.copy()
        elif scheme == "tercile":
            nl = max(1, int(round(k * long_fraction)))
            ns = max(1, int(round(k * short_fraction)))
            order = np.argsort(v)
            wgt = np.zeros(k)
            wgt[order[-nl:]] = 1.0 / nl
            wgt[order[:ns]] = -1.0 / ns
        elif scheme == "sign":
            wgt = np.sign(v)
        else:  # pragma: no cover
            raise ValueError(scheme)
        wgt = wgt - wgt.mean()
        g = np.abs(wgt).sum()
        if g <= 0:
            continue
        out[i, m] = wgt / g
    return out


def cadence_mask(n: int, cadence: int, phase: int) -> np.ndarray:
    reb = np.zeros(n, dtype=bool)
    reb[phase % cadence :: cadence] = True
    return reb


def neutralise(signal: np.ndarray, controls: list[np.ndarray], eligible: np.ndarray) -> np.ndarray:
    from eda_neutralise import residualise

    sr = M.cross_section_rank(signal, eligible)
    ranked = [M.cross_section_rank(c, eligible) for c in controls]
    return residualise(sr, ranked, eligible)
