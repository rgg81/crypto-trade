"""EDA 5 -- cadence, sleeve hysteresis and a no-trade band.

Two ways to hold turnover under the floor: rebalance rarely (a cadence, which has a phase and
therefore a phase lottery), or rebalance whenever the book has actually moved (a band, which has
no phase at all). This measures both, and it measures the cadence result as a phase MEAN.
"""

from __future__ import annotations

import sys

import numpy as np

sys.path.insert(0, "tournament/cup20/teams/team-04/research")
from book import fold_sharpes, quarter_fraction, simulate, stats  # noqa: E402
from eda_03_portfolio import FUND, elig, grid, make_signal, opens, start, symbols  # noqa: E402

N = len(grid)
K_SYM = len(symbols)


def book_band(sig, K, phase, *, entry=1 / 3, exit_frac=None, band=0.0):
    """Sleeve membership with optional rank hysteresis; emit only when the book has moved."""
    w = np.zeros((N, K_SYM))
    reb = np.zeros(N, dtype=bool)
    prev = np.zeros(K_SYM)
    held_long: set[int] = set()
    held_short: set[int] = set()
    for i in range(start, N):
        if K > 1 and (i - start) % K != phase % K:
            continue
        s, e = sig[i], elig[i]
        ok = np.isfinite(s) & e
        cnt = int(ok.sum())
        if cnt < 9:
            continue
        idx = np.where(ok)[0]
        order = idx[np.argsort(s[idx])]          # ascending: worst first
        m_in = max(1, int(round(cnt * entry)))
        m_out = m_in if exit_frac is None else max(m_in, int(round(cnt * exit_frac)))
        top_in, bot_in = set(order[-m_in:]), set(order[:m_in])
        top_out, bot_out = set(order[-m_out:]), set(order[:m_out])
        new_long = (held_long & top_out) | top_in
        new_short = (held_short & bot_out) | bot_in
        new_long &= set(idx)
        new_short &= set(idx)
        overlap = new_long & new_short
        new_long -= overlap
        new_short -= overlap
        if not new_long or not new_short:
            continue
        vec = np.zeros(K_SYM)
        vec[list(new_long)] = 1.0 / len(new_long)
        vec[list(new_short)] = -1.0 / len(new_short)
        vec /= np.abs(vec).sum()
        if np.abs(vec - prev).sum() < band:
            continue                              # nothing material changed: hold quantities
        held_long, held_short = new_long, new_short
        w[i] = vec
        reb[i] = True
        prev = vec
    return w, reb


def evaluate(sig, K, phase, cm=1.0, **kw):
    w, reb = book_band(sig, K, phase, **kw)
    res = simulate(w, reb, opens, FUND, start, cost_mult=cm)
    st = stats(res, grid, start)
    fs = fold_sharpes(res, grid, start)
    st["folds"] = fs
    st["minfold"] = min(fs)
    st["nposfold"] = sum(1 for x in fs if x > 0)
    st["posq"] = quarter_fraction(res, grid, start)
    return st


def summarise(tag, rows):
    a = lambda k: np.array([r[k] for r in rows])  # noqa: E731
    F = np.array([r["folds"] for r in rows])
    print(
        f"{tag:<40} Sh={a('sharpe').mean():+.2f}±{a('sharpe').std():.2f}"
        f"[{a('sharpe').min():+.2f}] dd={a('maxdd').mean():.3f} to={a('turnover_yr').mean():5.1f} "
        f"edge={a('gross_edge_bps').mean():5.0f} tr={a('trades').mean():6.0f} "
        f"q={a('posq').mean():.2f} mf={a('minfold').mean():+.2f}[{a('minfold').min():+.2f}] "
        f"folds={np.round(F.mean(0), 2)}"
    )


if __name__ == "__main__":
    what = sys.argv[1]
    if what == "cadence":
        for F in (42, 63, 90):
            sig, _ = make_signal("resid", 270, F, 1)
            for K in (1, 3, 6, 9, 15, 21, 30, 42):
                rows = [evaluate(sig, K, p) for p in range(min(K, 21))]
                summarise(f"resid F={F} K={K}", rows)
            print()
    elif what == "hyst":
        for F in (63,):
            sig, _ = make_signal("resid", 270, F, 1)
            for K in (1, 3, 9, 21):
                for ex in (None, 0.40, 0.45, 0.50):
                    rows = [evaluate(sig, K, p, exit_frac=ex) for p in range(min(K, 21))]
                    summarise(f"resid F={F} K={K} exit={ex}", rows)
                print()
    elif what == "band":
        sig, _ = make_signal("resid", 270, 63, 1)
        for ex in (None, 0.45):
            for band in (0.0, 0.15, 0.25, 0.35, 0.50, 0.70):
                rows = [evaluate(sig, 1, 0, exit_frac=ex, band=band)]
                summarise(f"resid F=63 K=1 exit={ex} band={band}", rows)
            print()
    elif what == "abl":
        for kind in ("raw", "resid"):
            sig, _ = make_signal(kind, 270, 63, 1)
            for ex, band in ((0.45, 0.25), (0.45, 0.35), (None, 0.35)):
                rows = [evaluate(sig, 1, 0, exit_frac=ex, band=band)]
                summarise(f"{kind} F=63 K=1 exit={ex} band={band}", rows)
