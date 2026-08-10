"""EDA 3 -- thirds long/short books on raw vs residual formation returns.

The mandate's decisive ablation is here: identical construction, identical cadence, one line
different (whether beta * market is removed before ranking).
"""

from __future__ import annotations

import itertools
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-04/research")
from book import build_funding_matrix, fold_sharpes, quarter_fraction, simulate, stats  # noqa: E402
from panel import load_panel, log_returns, rolling_sum  # noqa: E402

P = load_panel()
grid, elig, symbols = P["grid"], P["eligible"], P["symbols"]
opens = P["opens"].to_numpy(dtype=float)
r = np.where(elig, log_returns(P["closes"]), np.nan)
start = int(grid.searchsorted(P["is_start"]))
n = len(grid)
FUND = build_funding_matrix(grid, symbols)


def shift1(a):
    out = np.full_like(a, np.nan)
    out[1:] = a[:-1]
    return out


def market_mean():
    with np.errstate(invalid="ignore"):
        return np.nanmean(r, axis=1)


MKT = market_mean()


def make_signal(kind: str, B: int, F: int, S: int):
    M = np.where(np.isnan(r), np.nan, np.repeat(MKT[:, None], r.shape[1], axis=1))
    s_y, s_x = rolling_sum(r, B), rolling_sum(M, B)
    s_xy, s_xx = rolling_sum(r * M, B), rolling_sum(M * M, B)
    cov = s_xy / B - (s_x / B) * (s_y / B)
    var = s_xx / B - (s_x / B) ** 2
    with np.errstate(invalid="ignore", divide="ignore"):
        beta = np.where(var > 0, cov / var, np.nan)

    def trail(x):
        s = rolling_sum(x, F)
        if S:
            o = np.full_like(s, np.nan)
            o[S:] = s[:-S]
            return o
        return s

    sr, sm = trail(r), trail(M)
    if kind == "raw":
        sig = sr
    elif kind == "resid":
        sig = sr - beta * sm
    elif kind == "resid_alpha":
        a = s_y / B - beta * (s_x / B)
        if S:
            a2 = np.full_like(a, np.nan)
            a2[S:] = a[:-S]
            a = a2
        sig = sr - beta * sm - F * a
    elif kind == "resid_vol":
        e = r - beta * M
        v = np.sqrt(rolling_sum((e - rolling_sum(e, B) / B) ** 2, B) / (B - 1))
        sig = (sr - beta * sm) / (v * np.sqrt(F))
    elif kind == "beta_only":  # placebo: rank on -beta alone, no return information
        sig = -beta
    else:
        raise ValueError(kind)
    return shift1(sig), shift1(beta)


def build_book(sig, beta, K: int, phase: int, *, third: float = 1 / 3, neutral=False, sign=1):
    w = np.zeros((n, len(symbols)))
    reb = np.zeros(n, dtype=bool)
    for i in range(start, n):
        if (i - start) % K != phase % K:
            continue
        s, e = sig[i], elig[i]
        ok = np.isfinite(s) & e
        cnt = int(ok.sum())
        if cnt < 9:
            continue
        idx = np.where(ok)[0]
        order = idx[np.argsort(s[idx])]
        m = max(1, int(round(cnt * third)))
        lo, hi = order[:m], order[-m:]
        vec = np.zeros(len(symbols))
        vec[hi] = sign * 1.0
        vec[lo] = -sign * 1.0
        if neutral:
            b = np.where(np.isfinite(beta[i]), beta[i], 1.0)
            bl, bs = b[hi].mean(), b[lo].mean()
            # scale sleeves so beta exposure nets: kl*bl == ks*bs, kl+ks = 2
            tot = bl + bs
            if tot > 0:
                kl, ks = 2 * bs / tot, 2 * bl / tot
                vec[hi] = sign * kl
                vec[lo] = -sign * ks
        g = np.abs(vec).sum()
        if g == 0:
            continue
        w[i] = vec / g
        reb[i] = True
    return w, reb


def report(tag, w, reb, cost_mult=1.0):
    res = simulate(w, reb, opens, FUND, start, cost_mult=cost_mult)
    st = stats(res, grid, start)
    fs = fold_sharpes(res, grid, start)
    st["folds"] = " ".join(f"{x:+.2f}" for x in fs)
    st["minfold"] = min(fs)
    st["posq"] = quarter_fraction(res, grid, start)
    print(
        f"{tag:<44} Sh={st['sharpe']:+.2f} gSh={st['gross_sharpe']:+.2f} "
        f"ret={st['ann_ret']:+.3f} vol={st['ann_vol']:.3f} dd={st['maxdd']:.3f} "
        f"to={st['turnover_yr']:5.1f} edge={st['gross_edge_bps']:6.1f} "
        f"tr={st['trades']:6d} q={st['posq']:.2f} folds=[{st['folds']}]"
    )
    return st


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "grid"
    if mode == "grid":
        for kind, F, K in itertools.product(
            ("raw", "resid"), (21, 42, 63, 90), (9, 21, 42)
        ):
            sig, beta = make_signal(kind, 270, F, 1)
            w, reb = build_book(sig, beta, K, K // 2)
            report(f"{kind:<11} B=270 F={F:<3} S=1 K={K:<3}", w, reb)
        print()
    elif mode == "ablate":
        F, K = int(sys.argv[2]), int(sys.argv[3])
        for kind in ("raw", "resid", "resid_alpha", "resid_vol", "beta_only"):
            sig, beta = make_signal(kind, 270, F, 1)
            w, reb = build_book(sig, beta, K, K // 2)
            report(f"{kind:<11} F={F} K={K}", w, reb)
        sig, beta = make_signal("resid", 270, F, 1)
        w, reb = build_book(sig, beta, K, K // 2, neutral=True)
        report(f"{'resid+bneut':<11} F={F} K={K}", w, reb)
        w, reb = build_book(sig, beta, K, K // 2, third=0.25)
        report(f"{'resid q4':<11} F={F} K={K}", w, reb)
        w, reb = build_book(sig, beta, K, K // 2, sign=-1)
        report(f"{'resid INVERT':<11} F={F} K={K}", w, reb)
