"""Fine base-lookback surface for FLOW and LOWRISK, phase-agnostic at cadence 6."""
from __future__ import annotations
import sys
import numpy as np
sys.path.insert(0, "tournament/cup20/teams/team-12/research")
from panel import Panel
import sleeves as SL, fastsim as FS, metricsfast as MF
p = Panel(); n = len(p.times); elig = p.eligible[p.t0:p.t0+n]
CAD = 6
def pm(name, W):
    o = []
    for ph in range(CAD):
        sc = MF.scored_vector(FS.run_book(W, SL.hold_cadence(W, CAD, ph), p), p, trial_count=2)
        o.append([sc["G"], sc["net_sharpe"], sc["worst_fold_sharpe"], sc["max_drawdown"]])
    a = np.array(o); m = a.mean(axis=0)
    print(f"{name:34s} G={m[0]:6.2f}[{a[:,0].min():6.1f},{a[:,0].max():6.1f}] Sh1={m[1]:.3f} worst={m[2]:+.3f} DD1={m[3]:.3f}")
    sys.stdout.flush()
print("== FLOW base b -> (b, 2b) ==")
for b in (42, 48, 55, 63, 72, 80, 90, 105):
    pm(f"flow ({b},{2*b})", SL.takerflow_blend(p, elig, lookbacks=(b, 2*b)))
print("== LOWRISK-maxdd base b -> (b,2b,3b) ==")
for b in (140, 160, 175, 189, 205, 220, 240, 260):
    pm(f"lowrisk ({b},{2*b},{3*b})", SL.lowrisk_blend(p, elig, lookbacks=(b, 2*b, 3*b), measures=("maxdd",)))
print("== TREND base b -> (b/2, b, 3b/2) ==")
for b in (70, 80, 90, 100, 110, 126):
    pm(f"trend ({b//2},{b},{3*b//2})", SL.trend_blend(p, elig, lookbacks=(b//2, b, 3*b//2)))
print("== CARRY base b ==")
for b in (84, 105, 126, 147, 168):
    pm(f"carry ({b},)", SL.carry_blend(p, elig, lookbacks=(b,)))
