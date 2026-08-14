"""Cadence and rebalance-phase sweeps for each sleeve family (standalone, offline)."""
from __future__ import annotations
import sys
import numpy as np
sys.path.insert(0, "tournament/cup20/teams/team-12/research")
from panel import Panel
import sleeves as SL, fastsim as FS, metricsfast as MF

p = Panel(); n = len(p.times); elig = p.eligible[p.t0:p.t0+n]

def ev(label, W, cad, ph):
    rb = SL.hold_cadence(W, cad, ph)
    if rb.sum() < 50: return None
    sc = MF.scored_vector(FS.run_book(W, rb, p), p, trial_count=2)
    print(MF.show(sc, label)); sys.stdout.flush()
    return sc

cfgs = {
    "flow63": SL.takerflow(p, elig, lookback=63, sign=1.0),
    "flow126": SL.takerflow(p, elig, lookback=126, sign=1.0),
    "trend45_90_135": SL.trend_blend(p, elig, lookbacks=(45, 90, 135)),
    "lowriskMDD189": SL.lowrisk_blend(p, elig, lookbacks=(189, 378, 567), measures=("maxdd",)),
    "carry126": SL.carry_blend(p, elig, lookbacks=(126,)),
}
import json
res = {}
for name, W in cfgs.items():
    print(f"\n----- {name} : cadence/phase -----")
    for cad in (3, 6, 9, 12, 21):
        gs = []
        for ph in range(cad):
            sc = ev(f"{name} cad={cad} ph={ph}", W, cad, ph)
            if sc: gs.append((sc["G"], sc["net_sharpe"], sc["worst_fold_sharpe"], sc["max_drawdown"]))
        if gs:
            a = np.array(gs)
            print(f"  >>> {name} cad={cad}: phase-mean G={a[:,0].mean():6.2f} "
                  f"min={a[:,0].min():6.2f} max={a[:,0].max():6.2f} | "
                  f"Sh1 mean={a[:,1].mean():.3f} sd={a[:,1].std():.3f} | "
                  f"worst-fold mean={a[:,2].mean():.3f} | DD1 mean={a[:,3].mean():.3f}")
            res[f"{name}|{cad}"] = a.tolist()
json.dump(res, open("tournament/cup20/teams/team-12/research/study3_phase.json","w"))
