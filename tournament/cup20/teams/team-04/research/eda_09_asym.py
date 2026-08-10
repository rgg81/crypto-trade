"""EDA 9 -- asymmetric sleeve widths, measured on the EXECUTED book.

The common risk unit turns out to matter for the short-sleeve floor as much as the signal does:
`s_t = clamp(0.10/sigma_t, 0.2, 3.0)` shrinks the book through 2020-21, which is exactly the fold
where a short sleeve bleeds. Everything here is measured after that scalar, because that is the
book the floor is evaluated on.
"""

from __future__ import annotations

import sys

import numpy as np

sys.path.insert(0, "tournament/cup20/teams/team-04/research")
from book import fold_sharpes, quarter_fraction, simulate, stats  # noqa: E402
from eda_03_portfolio import FUND, elig, grid, make_signal, opens, start, symbols  # noqa: E402

N, KS = len(grid), len(symbols)


def build(sig, K, phase, m_long, m_short, *, gross_long=0.5, invvol=None):
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
        lo, hi = order[:m_short], order[-m_long:]
        vec = np.zeros(KS)
        if invvol is None:
            vec[hi] = gross_long / len(hi)
            vec[lo] = -(1.0 - gross_long) / len(lo)
        else:
            iv = 1.0 / np.maximum(invvol[i], 1e-6)
            vec[hi] = gross_long * iv[hi] / iv[hi].sum()
            vec[lo] = -(1.0 - gross_long) * iv[lo] / iv[lo].sum()
        w[i] = vec
        reb[i] = True
    return w, reb


def run(sig, K, m_long, m_short, cm=1.0, **kw):
    out = []
    for p in range(K):
        w, reb = build(sig, K, p, m_long, m_short, **kw)
        res = simulate(w, reb, opens, FUND, start, cost_mult=cm)
        st = stats(res, grid, start)
        fs = fold_sharpes(res, grid, start)
        st["folds"] = fs
        st["minfold"] = min(fs)
        st["nposfold"] = sum(1 for x in fs if x > 0)
        st["posq"] = quarter_fraction(res, grid, start)
        out.append(st)
    return out


def line(tag, rows):
    a = lambda k: np.array([r[k] for r in rows])  # noqa: E731
    F = np.array([r["folds"] for r in rows])
    print(
        f"{tag:<30} Sh={a('sharpe').mean():+.2f}±{a('sharpe').std():.2f} "
        f"dd={a('maxdd').mean():.3f} vol={a('ann_vol').mean():.3f} to={a('turnover_yr').mean():5.1f} "
        f"edge={a('gross_edge_bps').mean():5.0f} L={a('long_pnl').mean():+.3f} "
        f"S={a('short_pnl').mean():+.3f}[{a('short_pnl').min():+.3f}] "
        f"t5={a('top5_day_share').mean():.3f} q={a('posq').mean():.2f} "
        f"mf={a('minfold').mean():+.2f} folds={np.round(F.mean(0), 2)}"
    )


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "width"
    if what == "width":
        for F in (63,):
            sig, _ = make_signal("resid", 270, F, 1)
            for K in (21, 30):
                for ml, ms in ((7, 7), (7, 5), (7, 4), (7, 3), (6, 3), (5, 3), (7, 2)):
                    line(f"resid F={F} K={K} L{ml}/S{ms}", run(sig, K, ml, ms))
                print()
    elif what == "tilt":
        sig, _ = make_signal("resid", 270, 63, 1)
        for gl in (0.50, 0.55, 0.60, 0.65):
            for ml, ms in ((7, 7), (7, 4)):
                line(f"resid K=21 L{ml}/S{ms} gl={gl}", run(sig, 21, ml, ms, gross_long=gl))
    elif what == "raw":
        sig, _ = make_signal("raw", 270, 63, 1)
        for K in (21, 30):
            for ml, ms in ((7, 7), (7, 4), (7, 3)):
                line(f"raw   F=63 K={K} L{ml}/S{ms}", run(sig, K, ml, ms))
