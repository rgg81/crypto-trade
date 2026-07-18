"""e05 — form C (stagnation-weighted fade) grid: L x q, gross + 1x + 2x."""

import sys

import numpy as np

sys.path.insert(0, "/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament/analysis")
from portfolio_tournament import constants as tc
from portfolio_tournament import engine as te

from common import build_and_move, crank, line, panels, score

pn, aux, scoring = panels()
rf = pn["ret_fwd"]
lr1 = np.log(pn["close"].where(pn["close"] > 0)).diff()
sig_vol = lr1.rolling(42, min_periods=30).std()


def form_C(L, q):
    b, r = build_and_move(pn, aux, L)
    stag = 1.0 - crank((r.abs() / sig_vol).where(b.notna()))
    g = (crank(b) - q).clip(lower=0.0) / (1.0 - q)
    return -(g * np.sign(r) * stag)


def gross_sharpe(sig):
    raw = te.conform_raw(sig.fillna(0.0), pn)
    masked = raw.where(scoring["elig"], 0.0)
    w = te.normalize_and_cap(masked).shift(1)
    pnl = (w * rf.reindex(columns=w.columns)).sum(axis=1)
    yr = pnl.groupby(pnl.index.year).sum().round(3)
    return te.msharpe(pnl.dropna(), tc.TRN_IS_START, tc.TRN_IS_HI), pnl.sum(), dict(yr)


for q in (0.6, 0.75):
    for L in (6, 9, 21, 42):
        s = form_C(L, q).fillna(0.0)
        gs, cum, yr = gross_sharpe(s)
        _, _, _, m1 = score(s)
        _, _, _, m2 = score(s, cost_mult=2.0, slip_mult=2.0)
        print(line(f"C L={L:2d} q={q} @1x", m1))
        print(f"{'':22s} grossS={gs:+.3f} cum={cum:+.3f} yr={yr}  S2x={m2.sharpe:+.3f}")
