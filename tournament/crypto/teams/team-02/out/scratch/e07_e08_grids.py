"""e07/e08 — breakout core grids: form D (Donchian state) and form E (channel position)."""

import sys

sys.path.insert(0, "/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament/analysis")
from portfolio_tournament import constants as tc
from portfolio_tournament import engine as te

from breakout import channel_pos, donchian_state
from common import line, panels, score

pn, aux, scoring = panels()
close = pn["close"]
rf = pn["ret_fwd"]


def gross_sharpe(sig):
    raw = te.conform_raw(sig.fillna(0.0), pn)
    masked = raw.where(scoring["elig"], 0.0)
    w = te.normalize_and_cap(masked).shift(1)
    pnl = (w * rf.reindex(columns=w.columns)).sum(axis=1)
    return te.msharpe(pnl.dropna(), tc.TRN_IS_START, tc.TRN_IS_HI)


print("== e07: form D (Donchian state, M=round(N/3), raw, k=1) ==")
for N in (30, 60, 90, 180):
    M = round(N / 3)
    s = donchian_state(close, N, M).fillna(0.0)
    _, _, _, m1 = score(s)
    _, _, _, m2 = score(s, cost_mult=2.0, slip_mult=2.0)
    print(line(f"D N={N:3d} M={M:2d} @1x", m1) + f"  grossS={gross_sharpe(s):+.3f}  S2x={m2.sharpe:+.3f}")

print("\n== e08: form E (channel position, d=0.25, raw, k=1) ==")
for N in (30, 60, 90, 180):
    s = channel_pos(close, N, 0.25).fillna(0.0)
    _, _, _, m1 = score(s)
    _, _, _, m2 = score(s, cost_mult=2.0, slip_mult=2.0)
    print(line(f"E N={N:3d} d=.25 @1x", m1) + f"  grossS={gross_sharpe(s):+.3f}  S2x={m2.sharpe:+.3f}")
