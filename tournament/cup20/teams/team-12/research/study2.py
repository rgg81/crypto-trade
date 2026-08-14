from __future__ import annotations
import sys, json
import numpy as np
sys.path.insert(0, "tournament/cup20/teams/team-12/research")
from panel import Panel
import sleeves as SL, fastsim as FS, metricsfast as MF

p = Panel(); n = len(p.times); elig = p.eligible[p.t0:p.t0+n]
which = sys.argv[1]

def ev(label, W, cad, ph=0):
    rb = SL.hold_cadence(W, cad, ph)
    if rb.sum() < 50: return
    sc = MF.scored_vector(FS.run_book(W, rb, p), p, trial_count=2)
    print(MF.show(sc, label)); sys.stdout.flush()

if which == "trend":
    for lbs in ([45,90,135],[60,90,120],[30,90,180],[45,90,180,270],[63,126,189,252],
                [21,42,63,84],[90],[75,90,105]):
        W = SL.trend_blend(p, elig, lookbacks=lbs)
        for cad in (3, 9, 21):
            ev(f"trendblend {lbs} cad={cad}", W, cad)
elif which == "carry":
    for lbs in ([63,126,252],[42,84,168],[126],[63,126],[21,63,126,252]):
        W = SL.carry_blend(p, elig, lookbacks=lbs)
        for cad in (3, 9, 21):
            ev(f"carryblend {lbs} cad={cad}", W, cad)
elif which == "lowrisk":
    for lbs in ([252,504],[126,252,504],[504],[252],[189,378,567]):
        for meas in (("vol","downside","maxdd"),("maxdd",),("vol","downside"),("downside","maxdd")):
            W = SL.lowrisk_blend(p, elig, lookbacks=lbs, measures=meas)
            for cad in (9, 21):
                ev(f"lowriskblend {lbs} {meas} cad={cad}", W, cad)
elif which == "flow":
    for lb in (9, 21, 63, 126, 252):
        for sg in (1.0, -1.0):
            W = SL.takerflow(p, elig, lookback=lb, sign=sg)
            for cad in (3, 9, 21):
                ev(f"takerflow lb={lb} sign={sg:+.0f} cad={cad}", W, cad)
elif which == "rev":
    for lb in (1, 2, 3, 6, 9, 21):
        for sg in (-1.0, 1.0):
            W = SL.revshock(p, elig, lookback=lb, sign=sg)
            for cad in (1, 3):
                ev(f"revshock lb={lb} sign={sg:+.0f} cad={cad}", W, cad)
