"""Team-11 measure library: every calendar-derived quantity, built causally.

Conventions that matter and were checked rather than assumed:

* The evaluator earns ``open[t+1]/open[t] - 1`` on exposure taken at boundary ``t``. A formation
  built from ``open`` returns therefore SHARES the price ``open[t]`` with the forward return and
  carries a mechanical negative bias (bid-ask bounce). Every formation here is built from CLOSE
  prices of bars that have already closed at the decision, so no price is shared with the forward.
* At decision ``t`` the last fully observed bar is the one spanning ``[t-8h, t]``; its row index in
  the panel is ``t-1``. Every rolling window below ends at row ``t-1``.
"""

from __future__ import annotations

import numpy as np

EPS = 1e-12


def _shift(a: np.ndarray, k: int) -> np.ndarray:
    out = np.full_like(a, np.nan)
    if k > 0:
        out[k:] = a[:-k]
    elif k == 0:
        out[:] = a
    return out


def causal_rolling_sum(x: np.ndarray, window: int) -> np.ndarray:
    """Sum of ``x`` over the ``window`` rows ending at ``t-1`` (strictly past)."""
    v = np.nan_to_num(x, nan=0.0)
    ok = np.isfinite(x).astype(float)
    cs = np.cumsum(v, axis=0)
    co = np.cumsum(ok, axis=0)
    out = np.full_like(x, np.nan)
    n = x.shape[0]
    for t in range(window, n):
        tot = cs[t - 1] - (cs[t - 1 - window] if t - 1 - window >= 0 else 0.0)
        cnt = co[t - 1] - (co[t - 1 - window] if t - 1 - window >= 0 else 0.0)
        out[t] = np.where(cnt >= window * 0.8, tot, np.nan)
    return out


def causal_masked_sum(x: np.ndarray, rowmask: np.ndarray, window: int) -> np.ndarray:
    """Sum of ``x`` over the ``window`` rows ending at ``t-1``, counting only rows where
    ``rowmask`` is True. ``window`` counts ALL rows, so the mask selects a calendar subset of a
    fixed wall-clock window -- which is what a calendar contrast needs."""
    v = np.where(rowmask[:, None], np.nan_to_num(x, nan=0.0), 0.0)
    ok = np.where(rowmask[:, None], np.isfinite(x), False).astype(float)
    cs = np.cumsum(v, axis=0)
    co = np.cumsum(ok, axis=0)
    out = np.full_like(x, np.nan)
    n = x.shape[0]
    for t in range(window, n):
        tot = cs[t - 1] - (cs[t - 1 - window] if t - 1 - window >= 0 else 0.0)
        cnt = co[t - 1] - (co[t - 1 - window] if t - 1 - window >= 0 else 0.0)
        out[t] = np.where(cnt >= 1, tot, np.nan)
    return out


def close_log_return(close: np.ndarray) -> np.ndarray:
    """Bar close-to-close log return, row ``t`` = return of the bar spanning ``[t, t+8h]``."""
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.log(close / _shift(close, 1))


def intrabar_log_return(open_: np.ndarray, close: np.ndarray) -> np.ndarray:
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.log(close / open_)


def share_of_activity(
    quantity: np.ndarray, rowmask: np.ndarray, window: int
) -> np.ndarray:
    """Fraction of ``quantity`` accumulated in the masked calendar cell over the past window.

    A slow per-coin CHARACTERISTIC, not a return signal: it says *when in the day this coin
    trades*, which is a statement about who owns it.
    """
    part = causal_masked_sum(quantity, rowmask, window)
    total = causal_rolling_sum(quantity, window)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = part / np.where(np.abs(total) > EPS, total, np.nan)
    return out


def cross_section_rank(x: np.ndarray, mask: np.ndarray, min_names: int = 8) -> np.ndarray:
    """Row-wise rank mapped to [-1, +1], NaN where the mask is false or too few names."""
    out = np.full(x.shape, np.nan)
    for i in range(x.shape[0]):
        m = mask[i] & np.isfinite(x[i])
        n = int(m.sum())
        if n < min_names:
            continue
        v = x[i, m]
        order = np.argsort(np.argsort(v)).astype(float)
        out[i, m] = (order - (n - 1) / 2.0) / max((n - 1) / 2.0, EPS)
    return out


def demean(x: np.ndarray, mask: np.ndarray) -> np.ndarray:
    out = np.where(mask, x, np.nan)
    mu = np.nanmean(out, axis=1, keepdims=True)
    return out - mu
