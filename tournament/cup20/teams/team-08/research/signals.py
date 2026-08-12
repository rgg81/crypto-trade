"""Team 08 signal library: funding and basis term-structure dynamics.

Everything here is built out of the funding-event stream the DecisionContext exposes
(funding rows strictly before the boundary), which carries the rate, the mark price and
the mark timestamp. The basis proxy is the perp close at that mark timestamp against the
mark itself.

Vocabulary used throughout:
  level      mean of the last k observations              (team 07's territory; a CONTROL here)
  spread     mean(last k_s) - mean(last k_l)              a coin against its own recent regime
  change     obs[0] - obs[k]                              the crude first difference
  persistence  fraction of the long window whose sign agrees with the spread
  dispersion   cross-sectional standard deviation of a per-coin measure
"""

from __future__ import annotations

import numpy as np


def rolling_means(lags: np.ndarray) -> np.ndarray:
    """Prefix means over the lag axis. ``out[k]`` is the mean of lags 0..k inclusive."""
    x = np.where(np.isfinite(lags), lags, np.nan)
    csum = np.nancumsum(x, axis=0)
    cnt = np.cumsum(np.isfinite(x), axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        out = csum / np.where(cnt > 0, cnt, np.nan)
    out[cnt == 0] = np.nan
    return out


def xs_demean(x: np.ndarray, elig: np.ndarray) -> np.ndarray:
    m = np.where(elig & np.isfinite(x), x, np.nan)
    mu = np.nanmean(m, axis=1, keepdims=True)
    return np.where(elig & np.isfinite(x), x - mu, np.nan)


def xs_z(x: np.ndarray, elig: np.ndarray) -> np.ndarray:
    m = np.where(elig & np.isfinite(x), x, np.nan)
    mu = np.nanmean(m, axis=1, keepdims=True)
    sd = np.nanstd(m, axis=1, keepdims=True)
    sd = np.where(sd > 0, sd, np.nan)
    return np.where(elig & np.isfinite(x), (x - mu) / sd, np.nan)


def xs_rank(x: np.ndarray, elig: np.ndarray) -> np.ndarray:
    """Cross-sectional rank mapped to [-1, 1], NaN outside the eligible set."""
    out = np.full(x.shape, np.nan)
    for t in range(x.shape[0]):
        m = elig[t] & np.isfinite(x[t])
        n = int(m.sum())
        if n < 4:
            continue
        v = x[t, m]
        order = np.argsort(np.argsort(v))
        out[t, m] = (order / (n - 1)) * 2.0 - 1.0
    return out


def xs_orthogonalise(y: np.ndarray, x: np.ndarray, elig: np.ndarray) -> np.ndarray:
    """Residual of ``y`` on ``x`` in each cross-section (both demeaned first).

    The whole point of the lane: it strips out anything the *level* can explain, so what
    is left is dynamics that level does not carry. Returns NaN where the regression has
    no support.
    """
    out = np.full(y.shape, np.nan)
    for t in range(y.shape[0]):
        m = elig[t] & np.isfinite(y[t]) & np.isfinite(x[t])
        n = int(m.sum())
        if n < 6:
            continue
        yy = y[t, m] - y[t, m].mean()
        xx = x[t, m] - x[t, m].mean()
        denom = float((xx * xx).sum())
        beta = float((xx * yy).sum()) / denom if denom > 0 else 0.0
        out[t, m] = yy - beta * xx
    return out


def to_weights(
    score: np.ndarray,
    elig: np.ndarray,
    *,
    n_side: int,
    scheme: str = "equal",
) -> np.ndarray:
    """Long the top ``n_side`` scores, short the bottom ``n_side``, dollar neutral."""
    W = np.zeros(score.shape)
    for t in range(score.shape[0]):
        m = elig[t] & np.isfinite(score[t])
        idx = np.flatnonzero(m)
        if len(idx) < 2 * n_side:
            continue
        v = score[t, idx]
        order = np.argsort(v)
        lo = idx[order[:n_side]]
        hi = idx[order[-n_side:]]
        if scheme == "equal":
            W[t, hi] = 0.5 / n_side
            W[t, lo] = -0.5 / n_side
        elif scheme == "score":
            sel = np.concatenate([lo, hi])
            s = score[t, sel]
            s = s - s.mean()
            a = np.abs(s).sum()
            if a <= 0:
                continue
            W[t, sel] = s / a
    return W


def rebalance_mask(n_t: int, cadence: int, phase: int) -> np.ndarray:
    r = np.zeros(n_t, dtype=bool)
    r[phase % cadence :: cadence] = True
    return r


def hold_forward(W: np.ndarray, reb: np.ndarray) -> np.ndarray:
    """Zero out non-rebalance rows; the simulator holds quantities there."""
    out = np.zeros_like(W)
    out[reb] = W[reb]
    return out
