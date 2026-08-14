"""Phase-agnostic (mean over all phases at cadence 6) comparison of final sleeve candidates."""
from __future__ import annotations
import sys
import numpy as np
sys.path.insert(0, "tournament/cup20/teams/team-12/research")
from panel import Panel
import sleeves as SL, fastsim as FS, metricsfast as MF

p = Panel(); n = len(p.times); elig = p.eligible[p.t0:p.t0+n]
CAD = 6

def phase_mean(name, W):
    out = []
    for ph in range(CAD):
        rb = SL.hold_cadence(W, CAD, ph)
        sc = MF.scored_vector(FS.run_book(W, rb, p), p, trial_count=2)
        out.append([sc["G"], sc["net_sharpe"], sc["double_cost_sharpe"], sc["worst_fold_sharpe"],
                    sc["median_fold_sharpe"], sc["max_drawdown"], sc["double_cost_max_drawdown"],
                    sc["calmar"], sc["annualized_turnover"], sc["annualized_volatility"]])
    a = np.array(out)
    m = a.mean(axis=0)
    print(f"{name:44s} G={m[0]:6.2f}[{a[:,0].min():6.2f},{a[:,0].max():6.2f}] Sh1={m[1]:.3f} "
          f"Sh2={m[2]:.3f} worst={m[3]:+.3f} med={m[4]:.3f} DD1={m[5]:.3f} DD2={m[6]:.3f} "
          f"cal={m[7]:.2f} trn={m[8]:5.1f} vol={m[9]:.3f}")
    sys.stdout.flush()
    return m

print("== FLOW ==")
for lbs in [(63,), (126,), (252,), (63,126,252), (63,126), (126,252), (42,84,168), (84,168,336)]:
    phase_mean(f"flow {lbs}", SL.takerflow_blend(p, elig, lookbacks=lbs))
print("== LOWRISK (maxdd) ==")
for lbs in [(189,378,567), (126,252,378), (252,504,756), (189,), (378,), (126,252,504)]:
    phase_mean(f"lowrisk-maxdd {lbs}", SL.lowrisk_blend(p, elig, lookbacks=lbs, measures=("maxdd",)))
print("== TREND ==")
for lbs in [(45,90,135), (60,120,180), (30,60,90), (45,90,180), (90,)]:
    phase_mean(f"trend {lbs}", SL.trend_blend(p, elig, lookbacks=lbs))
print("== CARRY ==")
for lbs in [(126,), (63,126,189), (63,126,252), (84,168,252), (189,)]:
    phase_mean(f"carry {lbs}", SL.carry_blend(p, elig, lookbacks=lbs))
