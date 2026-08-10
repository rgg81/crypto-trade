"""EDA 11 -- the three shapes that could rescue the short-sleeve floor, and what each costs.

R1  narrow the short sleeve toward the deepest losers (still cross-sectional, still in lane)
R2  conviction weighting by cross-sectional z-score instead of equal weight inside the sleeve
R3  veto shorts whose own trailing return is positive -- i.e. never short something that is
    rising. This one is measured and reported, not adopted: it is a per-coin trend gate, which
    is another team's mechanism, and in a window where the index tripled it turns the book
    long-heavy in exactly the fold that dominates the sample.
"""

from __future__ import annotations

import sys

import numpy as np

sys.path.insert(0, "tournament/cup20/teams/team-04/research")
from book import fold_sharpes, quarter_fraction, simulate, stats  # noqa: E402
from eda_03_portfolio import FUND, elig, grid, make_signal, opens, start, symbols  # noqa: E402
from panel import load_panel, log_returns, rolling_sum  # noqa: E402

N, KS = len(grid), len(symbols)
P = load_panel()
R = np.where(elig, log_returns(P["closes"]), np.nan)
TREND = np.full_like(R, np.nan)
TREND[1:] = rolling_sum(R, 63)[:-1]      # own trailing 63-bar return, shifted to be causal


def build(sig, K, phase, m_long, m_short, *, weighting="equal", veto=False):
    w = np.zeros((N, KS))
    reb = np.zeros(N, dtype=bool)
    for i in range(start, N):
        if K > 1 and (i - start) % K != phase % K:
            continue
        s, e = sig[i], elig[i]
        ok = np.isfinite(s) & e
        cnt = int(ok.sum())
        if cnt < 9:
            continue
        idx = np.where(ok)[0]
        order = idx[np.argsort(s[idx])]
        lo, hi = list(order[:m_short]), list(order[-m_long:])
        if veto:
            lo = [c for c in lo if np.isfinite(TREND[i][c]) and TREND[i][c] < 0.0]
        if not hi:
            continue
        vec = np.zeros(KS)
        if weighting == "equal":
            vec[hi] = 0.5 / len(hi)
            if lo:
                vec[lo] = -0.5 / len(lo)
        else:
            v = s[ok]
            z = (s - v.mean()) / (v.std() + 1e-12)
            wl = np.abs(z[hi])
            vec[hi] = 0.5 * wl / wl.sum()
            if lo:
                ws = np.abs(z[lo])
                vec[lo] = -0.5 * ws / ws.sum()
        if not lo:                      # long-only boundary: keep gross at 1
            vec = vec / np.abs(vec).sum()
        w[i] = vec
        reb[i] = True
    return w, reb


def run(sig, K, ml, ms, **kw):
    out = []
    for p in range(K):
        w, reb = build(sig, K, p, ml, ms, **kw)
        res = simulate(w, reb, opens, FUND, start)
        st = stats(res, grid, start)
        fs = fold_sharpes(res, grid, start)
        st["folds"] = fs
        st["minfold"] = min(fs)
        st["posq"] = quarter_fraction(res, grid, start)
        out.append(st)
    return out


def line(tag, rows):
    a = lambda k: np.array([r[k] for r in rows])  # noqa: E731
    sp = a("short_pnl")
    print(
        f"{tag:<38} Sh={a('sharpe').mean():+.2f}±{a('sharpe').std():.2f} "
        f"dd={a('maxdd').mean():.3f} vol={a('ann_vol').mean():.3f} "
        f"to={a('turnover_yr').mean():5.1f} edge={a('gross_edge_bps').mean():5.0f} "
        f"L={a('long_pnl').mean():+.3f} S={sp.mean():+.3f} S>0 at {int((sp > 0).sum())}/{len(sp)} "
        f"mf={a('minfold').mean():+.2f} folds={np.round(np.array([r['folds'] for r in rows]).mean(0), 2)}"
    )


if __name__ == "__main__":
    sig, _ = make_signal("resid", 270, 63, 1)
    print("--- R2 conviction weighting ---")
    for ml, ms in ((7, 7), (7, 4)):
        line(f"z-weight K=21 L{ml}/S{ms}", run(sig, 21, ml, ms, weighting="z"))
    print("--- R3 short-side absolute-trend veto (measured, not adopted) ---")
    for ml, ms in ((7, 7), (7, 4)):
        line(f"veto K=21 L{ml}/S{ms}", run(sig, 21, ml, ms, veto=True))
