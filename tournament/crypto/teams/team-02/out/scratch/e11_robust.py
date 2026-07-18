"""e11 — robustness battery for candidate: form E, N=60, d=0.25, k=6, raw sizing."""

import sys

import pandas as pd

sys.path.insert(0, "/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament/analysis")
from portfolio_tournament import constants as tc
from portfolio_tournament import engine as te

from breakout import channel_pos
from common import line, panels, score

pn, aux, scoring = panels()
close = pn["close"]


def sig_of(N, d, k):
    s = channel_pos(close, N, d).fillna(0.0)
    return s.ewm(span=k).mean() if k > 1 else s


print("== (a) k boundary at N=60 d=0.25 ==")
for k in (6, 9, 12):
    s = sig_of(60, 0.25, k)
    _, _, _, m1 = score(s)
    _, _, _, m2 = score(s, cost_mult=2.0, slip_mult=2.0)
    print(line(f"E N=60 d=.25 k={k:2d} @1x", m1) + f"  S2x={m2.sharpe:+.3f} min={min(m1.sharpe, m2.sharpe):+.3f}")

print("\n== (b) N neighbors at d=0.25 k=6 ==")
for N in (30, 60, 90):
    s = sig_of(N, 0.25, 6)
    _, _, _, m1 = score(s)
    _, _, _, m2 = score(s, cost_mult=2.0, slip_mult=2.0)
    print(line(f"E N={N:3d} d=.25 k=6 @1x", m1) + f"  S2x={m2.sharpe:+.3f}")

print("\n== (c) candidate decomposition ==")
s = sig_of(60, 0.25, 6)
net, w, parts, m = score(s)
print(line("CAND @1x", m))
yr_net = net.groupby(net.index.year).sum().round(3)
yr_pnl = parts["pnl"].groupby(parts["pnl"].index.year).sum().round(3)
yr_f = parts["fpnl"].groupby(parts["fpnl"].index.year).sum().round(3)
yr_c = parts["cost"].groupby(parts["cost"].index.year).sum().round(3)
print(pd.DataFrame({"net(vt)": yr_net, "pnl": yr_pnl, "fpnl": yr_f, "cost": yr_c}).T.to_string())
netf, wf, partsf = te.net_series(te.conform_raw(s, pn), pn, scoring, apply_funding=False)
mf = te.evaluate(netf, wf, partsf, lo=tc.TRN_IS_START, hi=tc.TRN_IS_HI)
print(f"funding-off S={mf.sharpe:+.3f} (informational)")

print("\n== (d) half-sample Sharpe ==")
h1 = te.msharpe(net, pd.Timestamp("2020-01-01"), pd.Timestamp("2022-04-01"))
h2 = te.msharpe(net, pd.Timestamp("2022-04-01"), pd.Timestamp("2024-07-01"))
print(f"H1 2020-01..2022-03: {h1:+.3f}   H2 2022-04..2024-06: {h2:+.3f}")

print("\n== monthly worst-5 ==")
g = net.groupby(net.index.to_period("M")).sum().sort_values()
print((g.head(5) * 100).round(2).to_string())
