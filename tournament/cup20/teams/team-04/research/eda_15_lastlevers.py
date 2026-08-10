"""EDA 15 -- the remaining in-lane levers on Sharpe, before concluding the lane is unsupported.

The only floor `resid-narrow-short` failed on trial #32 is trial-adjusted confidence, and that
floor is arithmetic: at the eight-trial minimum it needs a neighbourhood-median bootstrap fraction
of 0.9875, which on this window is an in-sample Sharpe near 1.13 held as a PLATEAU median rather
than reached at one point. This exhausts the levers that could plausibly move it without leaving
the lane: inverse-volatility sleeve weighting, a multi-horizon formation composite, and BTC as the
market factor instead of the equal-weight cross-section.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-04/research")
from crypto_trade.cup20.bootstrap import (  # noqa: E402
    circular_block_bootstrap_positive_fraction as Bfrac,
)
from crypto_trade.cup20.bootstrap import (
    trial_adjusted_confidence as conf,
)

from book import fold_sharpes, quarter_fraction, simulate, stats  # noqa: E402
from eda_03_portfolio import FUND, elig, grid, make_signal, opens, start, symbols  # noqa: E402
from panel import load_panel, log_returns, rolling_sum  # noqa: E402
from sim import TURNOVER_HAIRCUT  # noqa: E402

N, KS = len(grid), len(symbols)
P = load_panel()
R = np.where(elig, log_returns(P["closes"]), np.nan)
VOL = np.full_like(R, np.nan)
_v = np.sqrt(rolling_sum(R * R, 90) / 90.0)
VOL[1:] = _v[:-1]


def build(sig, K, phase, lf, sf, weighting="equal"):
    w = np.zeros((N, KS))
    reb = np.zeros(N, dtype=bool)
    for i in range(start, N):
        if (i - start) % K != phase % K:
            continue
        s, e = sig[i], elig[i]
        ok = np.isfinite(s) & e
        if weighting == "invvol":
            ok = ok & np.isfinite(VOL[i]) & (VOL[i] > 0)
        cnt = int(ok.sum())
        if cnt < 9:
            continue
        idx = np.where(ok)[0]
        order = idx[np.argsort(s[idx])]
        lw, sw = max(1, int(round(cnt * lf))), max(1, int(round(cnt * sf)))
        hi, lo = order[-lw:], order[:sw]
        vec = np.zeros(KS)
        if weighting == "equal":
            vec[hi] = 0.5 / lw
            vec[lo] = -0.5 / sw
        else:
            iv = 1.0 / VOL[i]
            vec[hi] = 0.5 * iv[hi] / iv[hi].sum()
            vec[lo] = -0.5 * iv[lo] / iv[lo].sum()
        w[i] = vec / np.abs(vec).sum()
        reb[i] = True
    return w, reb


def zscore(sig):
    z = np.full_like(sig, np.nan)
    for i in range(start, sig.shape[0]):
        ok = np.isfinite(sig[i]) & elig[i]
        if ok.sum() < 9:
            continue
        v = sig[i][ok]
        z[i][ok] = (v - v.mean()) / (v.std() + 1e-12)
    return z


def composite(Fs, B=270, skip=1):
    acc = None
    for F in Fs:
        s, _ = make_signal("resid", B, F, skip)
        z = zscore(s)
        acc = z if acc is None else np.where(np.isnan(acc) | np.isnan(z), np.nan, acc + z)
    return acc / len(Fs)


def report(tag, sig, K, lf, sf, weighting="equal"):
    rows = []
    for p in range(K):
        w, reb = build(sig, K, p, lf, sf, weighting)
        res = simulate(w, reb, opens, FUND, start)
        st = stats(res, grid, start)
        st["folds"] = fold_sharpes(res, grid, start)
        st["minfold"] = min(st["folds"])
        st["posq"] = quarter_fraction(res, grid, start)
        st["B"] = Bfrac(pd.Series(res["net"], index=grid[start:]).resample("1D").sum())
        rows.append(st)
    a = lambda k: np.array([r[k] for r in rows])  # noqa: E731
    bm = float(np.median(a("B")))
    sp = a("short_pnl")
    print(
        f"{tag:<36} Sh={np.median(a('sharpe')):>5.2f} B={bm:.4f} conf@8={conf(bm, 8):.3f} "
        f"S>0 {int((sp > 0).sum()):>2}/{len(sp):<3} mf={np.median(a('minfold')):+.2f} "
        f"to*={a('turnover_yr').mean() * TURNOVER_HAIRCUT:5.1f} dd={a('maxdd').mean():.3f}"
    )


if __name__ == "__main__":
    base, _ = make_signal("resid", 270, 63, 1)
    print("reference")
    report("resid F=63 K=21 L.34/S.20 equal", base, 21, 0.34, 0.20)
    print("\nlever A -- inverse-volatility sleeve weighting")
    for K in (21, 24):
        report(f"resid F=63 K={K} L.34/S.20 invvol", base, K, 0.34, 0.20, "invvol")
    print("\nlever B -- multi-horizon formation composite")
    for Fs in ([42, 63, 84], [42, 63, 126], [63, 84, 105]):
        c = composite(Fs)
        report(f"comp {Fs} K=21 L.34/S.20", c, 21, 0.34, 0.20)
    print("\nlever C -- BTC as the market factor")
    for K in (21, 24):
        s, _ = make_signal("resid", 270, 63, 1)  # placeholder replaced below
    from eda_02_ic import signals  # noqa: E402

    for K in (21,):
        raw_b, res_b, _ = signals(270, 63, 1, "btc", False)
        report(f"resid(btc) F=63 K={K} L.34/S.20", res_b, K, 0.34, 0.20)
        raw_m, res_m, _ = signals(270, 63, 1, "median", False)
        report(f"resid(median) F=63 K={K} L.34/S.20", res_m, K, 0.34, 0.20)
