"""e09 — final-config validation bundle for (ls_accounts, W=90, E=3, rank, clip=3, mp=45)."""

import sys

sys.path.insert(
    0,
    "/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament/tournament/crypto/teams/team-06/out/scratch",
)
import json

import lib06
import pandas as pd

sys.path.insert(0, "/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament/analysis")
from portfolio_tournament import constants as tc
from portfolio_tournament import engine as te

T0 = pd.Timestamp("2023-01-13")
pn, aux, scoring = lib06.load()

# --- neighbors (rank transform) --------------------------------------------------------------
print("== plateau neighbors (rank) ==")
for cfg in [
    {"W": 45, "E": 3}, {"W": 135, "E": 3}, {"W": 90, "E": 1}, {"W": 90, "E": 6},
]:
    raw = lib06.fade_signal("ls_accounts", cfg["W"], ema_span=cfg["E"], mode="rank")
    m = lib06.score(raw, t0=T0, stress=False)
    print(json.dumps({"cfg": cfg, "sharpe_1x": m["sharpe_1x"], "sharpe_hw": m["sharpe_hw"]}))

# --- final config deep dive ------------------------------------------------------------------
raw = lib06.fade_signal("ls_accounts", 90, ema_span=3, mode="rank")
raw = te.conform_raw(raw, pn)
net, w, parts = te.net_series(raw, pn, scoring)
net2, w2, p2 = te.net_series(raw, pn, scoring, cost_mult=2.0, slip_mult=2.0)

print("\n== honest-window regime Sharpe (1x) ==")
hw = net[(net.index >= T0) & (net.index < tc.TRN_IS_HI)]
reg = te.regime_of(hw.index)
for label in sorted(reg.unique()):
    sub = hw[reg == label]
    g = sub.groupby(sub.index.to_period("M")).sum()
    sh = float(g.mean() / g.std() * (12 ** 0.5)) if len(g) > 1 and g.std() > 0 else float("nan")
    print(f"  {label}: months={len(g)} sharpe={sh:.2f}")

print("\n== half-split (honest window) ==")
mid = pd.Timestamp("2023-10-01")
print("  H1 2023-01-13..09-30:", round(te.msharpe(net, T0, mid), 3),
      " | 2x:", round(te.msharpe(net2, T0, mid), 3))
print("  H2 2023-10-01..2024-06-30:", round(te.msharpe(net, mid, tc.TRN_IS_HI), 3),
      " | 2x:", round(te.msharpe(net2, mid, tc.TRN_IS_HI), 3))

print("\n== attribution over honest window (pre-vol-target units) ==")
sel = (parts["pnl"].index >= T0) & (parts["pnl"].index < tc.TRN_IS_HI)
print("  price pnl:", round(float(parts["pnl"][sel].sum()), 4))
print("  funding pnl:", round(float(parts["fpnl"][sel].sum()), 4))
print("  cost:", round(float(parts["cost"][sel].sum()), 4))

print("\n== monthly net (1x), honest window ==")
g = hw.groupby(hw.index.to_period("M")).sum()
print((g.round(4)).to_string())
print("positive months:", int((g > 0).sum()), "/", len(g))
