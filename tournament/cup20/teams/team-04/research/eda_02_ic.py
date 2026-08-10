"""EDA 2 -- rank IC of RAW vs RESIDUAL cross-sectional momentum, causally computed.

Alignment contract (this is the part that decides whether the lane is honest):
  * row i of `r` is the log return of the bar OPENING at grid[i]; it closes at grid[i+1], so it is
    first visible at decision grid[i+1]. A signal used at decision i may therefore read r rows
    0..i-1 only. Every rolling statistic below is shifted by one row for exactly that reason.
  * the beta used at decision i is fitted on rows <= i-1. No row at or after the decision enters
    the fit.
  * the forward return scored against the signal is open[i+H]/open[i], the organiser's own
    next-bar-open fill convention.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd
from scipy.stats import rankdata

sys.path.insert(0, "tournament/cup20/teams/team-04/research")
from panel import load_panel, log_returns, rolling_sum  # noqa: E402

P = load_panel()
grid, elig = P["grid"], P["eligible"]
r = log_returns(P["closes"])
r = np.where(elig, r, np.nan)
opens = P["opens"].to_numpy(dtype=float)
start = grid.searchsorted(P["is_start"])
n = len(grid)


def market(kind: str) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        if kind == "mean":
            return np.nanmean(r, axis=1)
        if kind == "median":
            return np.nanmedian(r, axis=1)
    return r[:, P["symbols"].index("BTCUSDT")]


def causal_beta(rr: np.ndarray, m: np.ndarray, B: int) -> np.ndarray:
    """Rolling OLS slope of each column on m over the trailing B rows, WITH intercept."""
    M = np.repeat(m[:, None], rr.shape[1], axis=1)
    M = np.where(np.isnan(rr), np.nan, M)
    s_y, s_x = rolling_sum(rr, B), rolling_sum(M, B)
    s_xy, s_xx = rolling_sum(rr * M, B), rolling_sum(M * M, B)
    cov = s_xy / B - (s_x / B) * (s_y / B)
    var = s_xx / B - (s_x / B) ** 2
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(var > 0, cov / var, np.nan)


def shift1(a: np.ndarray) -> np.ndarray:
    out = np.full_like(a, np.nan)
    out[1:] = a[:-1]
    return out


def signals(B: int, F: int, S: int, kind: str, alpha: bool):
    m = market(kind)
    beta = causal_beta(r, m, B)
    M = np.repeat(m[:, None], r.shape[1], axis=1)
    M = np.where(np.isnan(r), np.nan, M)
    # trailing-F sums ending S rows back
    def trail(x):
        s = rolling_sum(x, F)
        if S:
            out = np.full_like(s, np.nan)
            out[S:] = s[:-S]
            return out
        return s

    sr, sm = trail(r), trail(M)
    raw = sr
    resid = sr - beta * sm
    if alpha:
        # subtract F * fitted intercept, a = mean_B(y) - beta*mean_B(x)
        a = rolling_sum(r, B) / B - beta * (rolling_sum(M, B) / B)
        if S:
            a_s = np.full_like(a, np.nan)
            a_s[S:] = a[:-S]
            a = a_s
        resid = resid - F * a
    return shift1(raw), shift1(resid), shift1(beta)


def rank_ic(sig: np.ndarray, H: int, step: int = 3) -> tuple[float, float, int]:
    """Mean cross-sectional Spearman IC vs forward H-bar open-to-open log return."""
    with np.errstate(invalid="ignore", divide="ignore"):
        fwd = np.full_like(opens, np.nan)
        fwd[: n - H] = np.log(opens[H:] / opens[: n - H])
    fwd = np.where(elig, fwd, np.nan)
    ics = []
    for i in range(start, n - H, step):
        s, f = sig[i], fwd[i]
        ok = np.isfinite(s) & np.isfinite(f) & elig[i]
        if ok.sum() < 10:
            continue
        ics.append(np.corrcoef(rankdata(s[ok]), rankdata(f[ok]))[0, 1])
    a = np.array(ics)
    return float(a.mean()), float(a.mean() / a.std() * np.sqrt(len(a))), len(a)


if __name__ == "__main__":
    B = int(sys.argv[1]) if len(sys.argv) > 1 else 270
    kind = sys.argv[2] if len(sys.argv) > 2 else "mean"
    alpha = (sys.argv[3] if len(sys.argv) > 3 else "1") == "1"
    print(f"beta window B={B} bars ({B/3:.0f}d)  factor={kind}  subtract_alpha={alpha}")
    print(f"{'F':>4} {'S':>3} {'H':>4} | {'IC_raw':>8} {'t_raw':>7} | {'IC_res':>8} {'t_res':>7}"
          f" | {'rankcorr':>8}")
    for F in (3, 6, 12, 21, 42, 63, 90):
        for S in (0, 1):
            raw, res, _ = signals(B, F, S, kind, alpha)
            # how much does residualisation move the rank vector?
            rc = []
            for i in range(start, n, 25):
                ok = np.isfinite(raw[i]) & np.isfinite(res[i]) & elig[i]
                if ok.sum() >= 10:
                    rc.append(np.corrcoef(rankdata(raw[i][ok]), rankdata(res[i][ok]))[0, 1])
            rcm = float(np.mean(rc))
            for H in (3, 9, 21, 42):
                ic_r, t_r, _ = rank_ic(raw, H)
                ic_e, t_e, k = rank_ic(res, H)
                print(f"{F:>4} {S:>3} {H:>4} | {ic_r:>8.4f} {t_r:>7.2f} | {ic_e:>8.4f} "
                      f"{t_e:>7.2f} | {rcm:>8.3f}")
