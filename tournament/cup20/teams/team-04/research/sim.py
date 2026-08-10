"""Canonical offline book builder -- byte-for-byte the same selection rule as `strategy.py`.

An earlier EDA module built sleeves of a FIXED width (7 long, N short) while the frozen strategy
takes a PROPORTION of whatever cross-section survived the history requirement. Those are not the
same book: the residual score needs BETA_WINDOW + FORMATION_BARS bars of clean history, so newly
admitted members are unrankable and the usable cross-section is frequently smaller than twenty.
Everything from here on uses this builder, which mirrors the frozen selection exactly:

    long_width  = max(1, round(n * SLEEVE_FRACTION))
    short_width = max(1, round(n * SHORT_SLEEVE_FRACTION))
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from book import fold_sharpes, quarter_fraction, simulate, stats
from eda_03_portfolio import FUND, elig, grid, make_signal, opens, start, symbols

N, KS = len(grid), len(symbols)
TURNOVER_HAIRCUT = 1.23  # simulator against the harness, measured on trial #30


def build(sig, K, phase, long_frac=0.34, short_frac=0.34, minimum=9):
    w = np.zeros((N, KS))
    reb = np.zeros(N, dtype=bool)
    for i in range(start, N):
        if K > 1 and (i - start) % K != phase % K:
            continue
        s, e = sig[i], elig[i]
        ok = np.isfinite(s) & e
        cnt = int(ok.sum())
        if cnt < minimum:
            continue
        idx = np.where(ok)[0]
        order = idx[np.argsort(s[idx])]
        lw = max(1, int(round(cnt * long_frac)))
        sw = max(1, int(round(cnt * short_frac)))
        vec = np.zeros(KS)
        vec[order[-lw:]] = 0.5 / lw
        vec[order[:sw]] = -0.5 / sw
        g = np.abs(vec).sum()
        if g <= 0:
            continue
        w[i] = vec / g
        reb[i] = True
    return w, reb


def evaluate(sig, K, phase, **kw):
    w, reb = build(sig, K, phase, **kw)
    res = simulate(w, reb, opens, FUND, start)
    st = stats(res, grid, start)
    st["folds"] = fold_sharpes(res, grid, start)
    st["minfold"] = min(st["folds"])
    st["posq"] = quarter_fraction(res, grid, start)
    st["daily"] = pd.Series(res["net"], index=grid[start:]).resample("1D").sum()
    return st


def sweep(kind, F, K, *, B=270, skip=1, long_frac=0.34, short_frac=0.34):
    sig, _ = make_signal(kind, B, F, skip)
    return [evaluate(sig, K, p, long_frac=long_frac, short_frac=short_frac) for p in range(K)]


def line(tag, rows):
    a = lambda k: np.array([r[k] for r in rows])  # noqa: E731
    F = np.array([r["folds"] for r in rows])
    sp = a("short_pnl")
    print(
        f"{tag:<30} Sh={a('sharpe').mean():+.2f}±{a('sharpe').std():.2f}"
        f"[{a('sharpe').min():+.2f}] dd={a('maxdd').mean():.3f} "
        f"to*={a('turnover_yr').mean() * TURNOVER_HAIRCUT:5.1f} edge={a('gross_edge_bps').mean():5.0f} "
        f"L={a('long_pnl').mean():+.3f} S={sp.mean():+.3f}({int((sp > 0).sum())}/{len(sp)}) "
        f"mf={a('minfold').mean():+.2f} q={a('posq').mean():.2f} folds={np.round(F.mean(0), 2)}"
    )
