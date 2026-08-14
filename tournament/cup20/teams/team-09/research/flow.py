"""Taker-flow measure library.

Every measure ``F`` obeys one convention: ``F[i]`` is computed from panel rows strictly before
``i``, so a decision taken at boundary ``i`` may read ``F[i]`` without look-ahead. That mirrors
``generate_targets``, which hands a strategy the bars whose close time is <= the decision time.

Denomination is explicit everywhere. ``quote_volume`` and ``taker_buy_quote_volume`` are USDT;
``volume`` and ``taker_buy_volume`` are base units. A ratio is only ever formed inside one
denomination. The quote pair is the default because a book sized in USDT cares about USDT flow.
"""

from __future__ import annotations

import numpy as np


def prev_sum(x: np.ndarray, w: int) -> np.ndarray:
    """``out[i] = nansum(x[i-w:i])`` — strictly past rows only."""
    z = np.nan_to_num(x, nan=0.0)
    cs = np.concatenate([np.zeros((1, x.shape[1])), np.cumsum(z, axis=0)])
    out = np.full_like(x, np.nan)
    out[w:] = cs[w:-1] - cs[: -w - 1]
    return out


def prev_count(x: np.ndarray, w: int) -> np.ndarray:
    ok = np.isfinite(x).astype(float)
    cs = np.concatenate([np.zeros((1, x.shape[1])), np.cumsum(ok, axis=0)])
    out = np.full_like(x, np.nan)
    out[w:] = cs[w:-1] - cs[: -w - 1]
    return out


def prev_mean(x: np.ndarray, w: int) -> np.ndarray:
    c = prev_count(x, w)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(c > 0, prev_sum(x, w) / c, np.nan)


def prev_std(x: np.ndarray, w: int) -> np.ndarray:
    c = prev_count(x, w)
    m = prev_mean(x, w)
    m2 = prev_mean(x * x, w)
    with np.errstate(invalid="ignore"):
        var = (m2 - m * m) * np.where(c > 1, c / (c - 1), np.nan)
    return np.sqrt(np.maximum(var, 0.0))


def prev_z(x: np.ndarray, w: int) -> np.ndarray:
    m, s = prev_mean(x, w), prev_std(x, w)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(s > 0, (x_shift(x) - m) / s, np.nan)


def x_shift(x: np.ndarray) -> np.ndarray:
    """The most recent strictly-past row: ``out[i] = x[i-1]``."""
    out = np.full_like(x, np.nan)
    out[1:] = x[:-1]
    return out


def zscore_rows(x: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Cross-sectional z-score within the eligible set of each row."""
    m = np.where(mask & np.isfinite(x), x, np.nan)
    mu = np.nanmean(m, axis=1, keepdims=True)
    sd = np.nanstd(m, axis=1, ddof=1, keepdims=True)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(sd > 0, (m - mu) / sd, 0.0)


def rank_rows(x: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Cross-sectional rank in [-1, 1] within the eligible set; NaN outside."""
    out = np.full(x.shape, np.nan)
    valid = mask & np.isfinite(x)
    for i in range(x.shape[0]):
        idx = np.flatnonzero(valid[i])
        if idx.size < 3:
            continue
        order = np.argsort(np.argsort(x[i, idx], kind="stable"))
        out[i, idx] = 2.0 * order / (idx.size - 1) - 1.0
    return out


def cs_residual(y: np.ndarray, X: list[np.ndarray], mask: np.ndarray) -> np.ndarray:
    """Row-by-row cross-sectional OLS residual of ``y`` on ``X`` (intercept added).

    Causal by construction: every input is a same-boundary quantity across names. Nothing from
    another boundary enters, so there is no window to leak through.
    """
    n, m = y.shape
    out = np.full((n, m), np.nan)
    for i in range(n):
        cols = mask[i] & np.isfinite(y[i])
        for xi in X:
            cols &= np.isfinite(xi[i])
        idx = np.flatnonzero(cols)
        if idx.size < len(X) + 3:
            continue
        A = np.column_stack([np.ones(idx.size)] + [xi[i, idx] for xi in X])
        yy = y[i, idx]
        try:
            beta, *_ = np.linalg.lstsq(A, yy, rcond=None)
        except np.linalg.LinAlgError:
            continue
        out[i, idx] = yy - A @ beta
    return out


class Flow:
    """Primitive per-bar flow quantities, plus windowed measures on demand."""

    def __init__(self, p) -> None:
        self.p = p
        qv = p.quote_volume
        tbq = p.taker_buy_quote_volume
        vb = p.volume
        tbb = p.taker_buy_volume
        nt = p.trade_count.astype(float)
        with np.errstate(invalid="ignore", divide="ignore"):
            self.qv = qv
            self.tbq = tbq
            self.net_quote = 2.0 * tbq - qv          # signed taker flow, USDT
            self.imb = np.where(qv > 0, self.net_quote / qv, np.nan)
            self.net_base = 2.0 * tbb - vb
            self.imb_base = np.where(vb > 0, self.net_base / vb, np.nan)
            self.nt = np.where(nt > 0, nt, np.nan)
            self.ats = np.where(nt > 0, qv / nt, np.nan)   # avg trade size, USDT
            self.log_ats = np.log(np.where(self.ats > 0, self.ats, np.nan))
            self.log_nt = np.log(self.nt)
            self.log_qv = np.log(np.where(qv > 0, qv, np.nan))
            self.ret = np.log(p.close / p.open)             # intrabar log return
            self.c2c = np.full_like(p.close, np.nan)
            self.c2c[1:] = np.log(p.close[1:] / p.close[:-1])
            self.rng = np.where(p.open > 0, (p.high - p.low) / p.open, np.nan)

    # ------------------------------------------------------------- windowed
    def netflow(self, w: int) -> np.ndarray:
        """Volume-weighted signed taker imbalance over the last w bars, in [-1, 1]."""
        num = prev_sum(self.net_quote, w)
        den = prev_sum(self.qv, w)
        with np.errstate(invalid="ignore", divide="ignore"):
            return np.where(den > 0, num / den, np.nan)

    def flow_intensity(self, w: int, base: int) -> np.ndarray:
        """Net taker flow over w bars measured against the symbol's own longer-run turnover."""
        num = prev_sum(self.net_quote, w)
        den = prev_sum(self.qv, base)
        with np.errstate(invalid="ignore", divide="ignore"):
            return np.where(den > 0, num / (den / base * w), np.nan)

    def ret_w(self, w: int) -> np.ndarray:
        return prev_sum(self.c2c, w)

    def vol_shock(self, w: int, base: int) -> np.ndarray:
        a = prev_mean(self.log_qv, w)
        b = prev_mean(self.log_qv, base)
        return a - b

    def ats_shock(self, w: int, base: int) -> np.ndarray:
        return prev_mean(self.log_ats, w) - prev_mean(self.log_ats, base)

    def nt_shock(self, w: int, base: int) -> np.ndarray:
        return prev_mean(self.log_nt, w) - prev_mean(self.log_nt, base)

    def realised_vol(self, w: int) -> np.ndarray:
        return prev_std(self.c2c, w)

    def amihud(self, w: int) -> np.ndarray:
        """Price impact per unit of traded USDT: mean(|ret| / quote_volume), log-scaled."""
        with np.errstate(invalid="ignore", divide="ignore"):
            ill = np.where(self.qv > 0, np.abs(self.c2c) / self.qv, np.nan)
        return np.log(prev_mean(ill, w))
