"""Causal volatility-regime measures for team-10.

Every array returned here is indexed by DECISION boundary t and uses only bars that have CLOSED
by t. In panel coordinates a bar with index i opens at grid[i] and closes at grid[i+1], so the
last bar visible at decision t is index t-1. Every measure is therefore built from a per-bar
quantity and then shifted by one so that row t holds a statistic over bars <= t-1. The shift is
applied once, centrally, in ``_causal`` -- never re-implemented per measure.

The measures are grouped by the four regime channels the mandate names -- level, term structure,
cross-sectional dispersion, correlation to BTC -- plus two the mandate implies rather than states:
asymmetry (which half of the variance was down) and time-aggregation (whether variance grows
faster or slower than linearly in the holding horizon, i.e. whether the regime is persistent or
choppy).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from panel import Panel

BARS_PER_YEAR = 365 * 24 / 8


def _causal(x: np.ndarray) -> np.ndarray:
    """Shift a per-bar statistic forward one row: row t then holds bars <= t-1."""
    out = np.full_like(x, np.nan, dtype=float)
    out[1:] = x[:-1]
    return out


def _roll_mean(x: np.ndarray, k: int) -> np.ndarray:
    """Trailing mean over k rows, NaN-aware, along axis 0."""
    v = np.nan_to_num(x, nan=0.0)
    m = (~np.isnan(x)).astype(float)
    cv = np.cumsum(v, axis=0)
    cm = np.cumsum(m, axis=0)
    out = np.full_like(x, np.nan, dtype=float)
    num = cv.copy()
    den = cm.copy()
    num[k:] = cv[k:] - cv[:-k]
    den[k:] = cm[k:] - cm[:-k]
    with np.errstate(invalid="ignore", divide="ignore"):
        out = np.where(den > 0.5 * k, num / np.maximum(den, 1e-12), np.nan)
    return out


def _roll_std(x: np.ndarray, k: int) -> np.ndarray:
    m1 = _roll_mean(x, k)
    m2 = _roll_mean(x * x, k)
    return np.sqrt(np.clip(m2 - m1 * m1, 0.0, None))


def _roll_sum(x: np.ndarray, k: int) -> np.ndarray:
    v = np.nan_to_num(x, nan=0.0)
    cv = np.cumsum(v, axis=0)
    out = cv.copy()
    out[k:] = cv[k:] - cv[:-k]
    out[: k - 1] = np.nan
    return out


class Regime:
    """All causal regime measures for one panel, computed once."""

    def __init__(self, p: Panel):
        self.p = p
        close = p.close
        prev = np.vstack([np.full((1, close.shape[1]), np.nan), close[:-1]])
        with np.errstate(invalid="ignore", divide="ignore"):
            self.ret = np.log(close / prev)  # (T,S) per-bar log return, bar t
        self.ret[~np.isfinite(self.ret)] = np.nan
        # Only member bars count toward the market aggregate.
        mask = p.member & np.isfinite(self.ret)
        r = np.where(mask, self.ret, np.nan)
        self.ret_member = r
        n = mask.sum(axis=1)
        self.n_members = n
        with np.errstate(invalid="ignore"):
            self.mret = np.nanmean(r, axis=1)  # equal-weight market log return per bar
            self.xdisp = np.nanstd(r, axis=1)  # cross-sectional dispersion per bar
        self.mret[n < 5] = np.nan
        self.xdisp[n < 5] = np.nan

        with np.errstate(invalid="ignore", divide="ignore"):
            self.hl = np.log(p.high / p.low)
        self.hl[~np.isfinite(self.hl)] = np.nan
        self.hl_m = np.where(p.member, self.hl, np.nan)
        with np.errstate(invalid="ignore"):
            self.mhl = np.nanmean(self.hl_m, axis=1)

        btc = p.symbols.index("BTCUSDT")
        self.btc_ret = self.ret[:, btc]

    # ---- channel 1: level -------------------------------------------------------------------
    def rv(self, k: int) -> np.ndarray:
        """Annualised realised volatility of the equal-weight market return over k bars."""
        x = self.mret
        return _causal(np.sqrt(_roll_mean((x * x)[:, None], k)[:, 0]) * np.sqrt(BARS_PER_YEAR))

    def rv_btc(self, k: int) -> np.ndarray:
        x = self.btc_ret
        return _causal(np.sqrt(_roll_mean((x * x)[:, None], k)[:, 0]) * np.sqrt(BARS_PER_YEAR))

    def rv_symbol(self, k: int) -> np.ndarray:
        """(T,S) per-symbol annualised realised volatility, causal."""
        r = self.ret
        return _causal(np.sqrt(_roll_mean(r * r, k)) * np.sqrt(BARS_PER_YEAR))

    def parkinson(self, k: int) -> np.ndarray:
        x = self.mhl
        return _causal(
            np.sqrt(_roll_mean((x * x)[:, None], k)[:, 0] / (4.0 * np.log(2.0)))
            * np.sqrt(BARS_PER_YEAR)
        )

    # ---- channel 2: term structure ---------------------------------------------------------
    def term(self, short: int, long: int) -> np.ndarray:
        """log(RV_short / RV_long): positive means the near end of the vol curve is elevated."""
        with np.errstate(invalid="ignore", divide="ignore"):
            return np.log(self.rv(short) / self.rv(long))

    def range_ratio(self, k: int) -> np.ndarray:
        """log(Parkinson / close-to-close RV): intraday range against bar-to-bar variance."""
        with np.errstate(invalid="ignore", divide="ignore"):
            return np.log(self.parkinson(k) / self.rv(k))

    def vol_of_vol(self, k_inner: int, k_outer: int) -> np.ndarray:
        inner = np.sqrt(_roll_mean((self.mret * self.mret)[:, None], k_inner)[:, 0])
        return _causal(_roll_std(inner[:, None], k_outer)[:, 0] / np.maximum(
            _roll_mean(inner[:, None], k_outer)[:, 0], 1e-12))

    def variance_ratio(self, q: int, k: int) -> np.ndarray:
        """Var(q-bar return) / (q * Var(1-bar return)) over a k-bar window.

        Above one: variance grows faster than linearly, so moves compound -- a persistent,
        trending regime. Below one: a choppy, mean-reverting regime. Pure second moments; it
        never reads the sign of a return.
        """
        x = self.mret
        agg = _roll_sum(x[:, None], q)[:, 0]
        v1 = _roll_mean((x * x)[:, None], k)[:, 0]
        vq = _roll_mean((agg * agg)[:, None], k)[:, 0]
        with np.errstate(invalid="ignore", divide="ignore"):
            return _causal(vq / (q * np.maximum(v1, 1e-16)))

    # ---- channel 3: cross-sectional dispersion ---------------------------------------------
    def dispersion(self, k: int) -> np.ndarray:
        return _causal(_roll_mean(self.xdisp[:, None], k)[:, 0] * np.sqrt(BARS_PER_YEAR))

    def dispersion_ratio(self, k: int) -> np.ndarray:
        """Idiosyncratic share: cross-sectional dispersion relative to market volatility."""
        d = _roll_mean(self.xdisp[:, None], k)[:, 0]
        m = np.sqrt(_roll_mean((self.mret * self.mret)[:, None], k)[:, 0])
        with np.errstate(invalid="ignore", divide="ignore"):
            return _causal(d / np.maximum(m, 1e-12))

    # ---- channel 4: correlation ------------------------------------------------------------
    def avg_correlation(self, k: int) -> np.ndarray:
        """Average pairwise correlation implied by market variance against mean symbol variance."""
        r = self.ret_member
        var_i = _roll_mean(r * r, k) - _roll_mean(r, k) ** 2
        with np.errstate(invalid="ignore"):
            mean_var = np.nanmean(var_i, axis=1)
        m = self.mret
        var_m = _roll_mean((m * m)[:, None], k)[:, 0] - _roll_mean(m[:, None], k)[:, 0] ** 2
        n = np.maximum(_roll_mean(self.n_members.astype(float)[:, None], k)[:, 0], 2.0)
        with np.errstate(invalid="ignore", divide="ignore"):
            rho = (n * var_m / np.maximum(mean_var, 1e-18) - 1.0) / (n - 1.0)
        return _causal(np.clip(rho, -1.0, 1.0))

    def btc_correlation(self, k: int) -> np.ndarray:
        """Cross-sectional mean of each member's trailing correlation to BTC."""
        r = self.ret_member
        b = np.repeat(self.btc_ret[:, None], r.shape[1], axis=1)
        b = np.where(np.isfinite(r), b, np.nan)
        cov = _roll_mean(r * b, k) - _roll_mean(r, k) * _roll_mean(b, k)
        sr = np.sqrt(np.clip(_roll_mean(r * r, k) - _roll_mean(r, k) ** 2, 0, None))
        sb = np.sqrt(np.clip(_roll_mean(b * b, k) - _roll_mean(b, k) ** 2, 0, None))
        with np.errstate(invalid="ignore", divide="ignore"):
            c = cov / np.maximum(sr * sb, 1e-18)
        with np.errstate(invalid="ignore"):
            return _causal(np.nanmean(np.clip(c, -1, 1), axis=1))

    def btc_share(self, k: int) -> np.ndarray:
        """Share of market variance carried by BTC's own variance."""
        with np.errstate(invalid="ignore", divide="ignore"):
            return np.log(self.rv_btc(k) / self.rv(k))

    # ---- channel 5: asymmetry (a decomposition of realised variance) -----------------------
    def semivariance_share(self, k: int) -> np.ndarray:
        """Downside share of realised variance: sum(r^2 | r<0) / sum(r^2)."""
        x = self.mret
        down = np.where(x < 0, x * x, 0.0)
        down[np.isnan(x)] = np.nan
        tot = x * x
        num = _roll_mean(down[:, None], k)[:, 0]
        den = _roll_mean(tot[:, None], k)[:, 0]
        with np.errstate(invalid="ignore", divide="ignore"):
            return _causal(num / np.maximum(den, 1e-18))

    def semivariance_share_symbol(self, k: int) -> np.ndarray:
        r = self.ret
        down = np.where(r < 0, r * r, 0.0)
        down[np.isnan(r)] = np.nan
        num = _roll_mean(down, k)
        den = _roll_mean(r * r, k)
        with np.errstate(invalid="ignore", divide="ignore"):
            return _causal(num / np.maximum(den, 1e-18))

    # ---- helpers ---------------------------------------------------------------------------
    def zscore(self, x: np.ndarray, k: int) -> np.ndarray:
        """Trailing z-score of an already-causal series against its own k-bar history."""
        m = _roll_mean(x[:, None] if x.ndim == 1 else x, k)
        s = _roll_std(x[:, None] if x.ndim == 1 else x, k)
        base = x[:, None] if x.ndim == 1 else x
        with np.errstate(invalid="ignore", divide="ignore"):
            z = (base - m) / np.maximum(s, 1e-12)
        return z[:, 0] if x.ndim == 1 else z

    def pctile(self, x: np.ndarray, k: int) -> np.ndarray:
        """Trailing percentile rank of an already-causal 1-D series within its own k-bar history."""
        T = len(x)
        out = np.full(T, np.nan)
        for t in range(k, T):
            w = x[t - k : t]
            v = x[t]
            if not np.isfinite(v):
                continue
            f = np.isfinite(w)
            if f.sum() < k // 2:
                continue
            out[t] = float((w[f] < v).mean())
        return out

    def forward_market(self, h: int) -> np.ndarray:
        """Forward h-bar market log return, measured on the OPEN-to-OPEN grid the book trades.

        Row t holds the return the book earns if it takes exposure at boundary t and holds h
        bars. Purely diagnostic: it is never an input to anything the strategy reads.
        """
        op = np.where(self.p.member, self.p.open, np.nan)
        with np.errstate(invalid="ignore", divide="ignore"):
            step = np.log(op[1:] / op[:-1])
        step = np.vstack([np.nanmean(step, axis=1)[:, None], [[np.nan]]])[:, 0]
        T = len(step)
        out = np.full(T, np.nan)
        cs = np.nancumsum(np.nan_to_num(step))
        for t in range(T - h):
            out[t] = cs[t + h - 1] - (cs[t - 1] if t > 0 else 0.0)
        return out
