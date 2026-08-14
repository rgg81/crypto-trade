"""Offline standalone study of each sleeve family. No trials spent; fastsim only."""
from __future__ import annotations
import sys, itertools, json
import numpy as np
sys.path.insert(0, "tournament/cup20/teams/team-12/research")
from panel import Panel
import sleeves as SL
import fastsim as FS
import metricsfast as MF

p = Panel()
n = len(p.times); elig = p.eligible[p.t0:p.t0+n]
which = sys.argv[1] if len(sys.argv) > 1 else "all"
rows = []

def ev(label, W, cad, ph):
    rb = SL.hold_cadence(W, cad, ph)
    if rb.sum() < 50:
        return None
    run = FS.run_book(W, rb, p)
    sc = MF.scored_vector(run, p, trial_count=2)
    print(MF.show(sc, label)); sys.stdout.flush()
    rows.append({"label": label, **{k: (v if not isinstance(v, list) else v)
                                    for k, v in sc.items() if k != "fold_sharpes_2x"},
                 "folds": sc["fold_sharpes_2x"]})
    return sc

if which in ("all", "carry"):
    print("\n===== CARRY (cross-sectional funding) =====")
    for lb in (21, 63, 126, 252, 504):
        W = SL.carry(p, elig, lookback=lb)
        for cad, ph in ((3, 0), (9, 0), (21, 0)):
            ev(f"carry lb={lb} cad={cad} ph={ph}", W, cad, ph)

if which in ("all", "trend"):
    print("\n===== TREND (per-coin TSMOM) =====")
    for lb in (30, 60, 90, 126, 189, 252, 378):
        for vs in (True, False):
            W = SL.trend(p, elig, lookback=lb, vol_scale=vs)
            for cad, ph in ((3, 0), (9, 0), (21, 0)):
                ev(f"trend lb={lb} vs={int(vs)} cad={cad} ph={ph}", W, cad, ph)

if which in ("all", "lowrisk"):
    print("\n===== LOWRISK (cross-sectional risk selection) =====")
    for meas in ("vol", "downside", "maxdd"):
        for lb in (63, 126, 252, 504):
            W = SL.lowrisk(p, elig, lookback=lb, measure=meas)
            for cad, ph in ((3, 0), (9, 0), (21, 0)):
                ev(f"lowrisk {meas} lb={lb} cad={cad} ph={ph}", W, cad, ph)

if which in ("all", "clock"):
    print("\n===== CLOCK (settlement/session seasonality) =====")
    for b in ("hour", "dow", "dowhour"):
        W = SL.clock(p, elig, bucket=b)
        for cad, ph in ((1, 0), (3, 0)):
            ev(f"clock {b} cad={cad}", W, cad, ph)

json.dump(rows, open(f"tournament/cup20/teams/team-12/research/study_{which}.json", "w"), indent=1)
print("\nrows:", len(rows))
