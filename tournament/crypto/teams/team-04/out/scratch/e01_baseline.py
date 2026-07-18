"""e01 — baseline defaults + structural diagnostics (breadth, net exposure, funding split)."""

import sys

sys.path.insert(
    0,
    "/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament/tournament/crypto/teams/team-04/out/scratch",
)
sys.path.insert(0, "/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament/analysis")

import pandas as pd
import tslib
from portfolio_tournament import constants as tc
from portfolio_tournament import engine as te

pn, aux, scoring = tslib.panels()
raw = tslib.build_signal(pn["close"])  # defaults: H=(21,63,126,252), Z=2, invvol, E=1, V=63
res = tslib.score(raw, "e01-baseline")
print(tslib.fmt([res]))

# ---- structural diagnostics on the capped, lagged book ----
raw_c = te.conform_raw(raw, pn)
net, w, parts = te.net_series(raw_c, pn, scoring)
ws = w[(w.index >= tc.TRN_IS_START) & (w.index < tc.TRN_IS_HI)]
active = ws.abs().sum(axis=1) > 0
nL = (ws > 1e-12).sum(axis=1)[active]
nS = (ws < -1e-12).sum(axis=1)[active]
netexp = ws.sum(axis=1)[active]

q = pd.Grouper(freq="QE")
tab = pd.DataFrame(
    {
        "medL": nL.groupby(q).median(),
        "medS": nS.groupby(q).median(),
        "minS": nS.groupby(q).min(),
        "net": netexp.groupby(q).mean().round(3),
    }
)
print("\nquarterly breadth/net (capped book):")
print(tab.to_string())

print("\nfraction of active candles with <5 shorts:", round(float((nS < 5).mean()), 3))
print("fraction of active candles with <5 longs:", round(float((nL < 5).mean()), 3))

mo = net[(net.index >= tc.TRN_IS_START) & (net.index < tc.TRN_IS_HI)]
mo = mo.groupby(mo.index.to_period("M")).sum()
print("\nmonthly net returns (vol-targeted):")
print((mo * 100).round(2).to_string())

# funding split by regime
reg = te.regime_of(parts["fpnl"].index)
fp = parts["fpnl"][(parts["fpnl"].index >= tc.TRN_IS_START) & (parts["fpnl"].index < tc.TRN_IS_HI)]
print("\nfunding pnl by regime (pre-vol-target):")
print(fp.groupby(reg[fp.index]).sum().round(4).to_string())
