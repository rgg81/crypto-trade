"""EDA 6 — inside the short sleeve: which crowding state marks a name that should not be shorted?"""
from __future__ import annotations
import sys, numpy as np, pandas as pd
sys.path.insert(0, "tournament/cup20/teams/team-07/research")
from strat import data

p = data()
g=p["grid"]; op=p["open"]; cl=p["close"]; fr=p["funding"]; ok=p["ok"]; mk=p["mark"]
qv=p["quote_volume"]; tbq=p["taker_buy_quote"]
H = 6
fwd = op.shift(-H)/op - 1.0
fwdrel = fwd.sub(fwd.where(ok).mean(axis=1), axis=0)      # excess over the eligible cross-section
r8 = op.pct_change()
L = 63
carry = fr.rolling(L, min_periods=L//2).mean().shift(1).where(ok)
risk  = r8.rolling(L, min_periods=L//2).std().shift(1).where(ok)
score = carry.sub(carry.median(axis=1), axis=0) / risk
rk = score.rank(axis=1, ascending=False)                  # 1 = most crowded / highest carry-to-risk
N = 7
short_side = rk.le(N) & ok
long_side  = rk.gt(score.notna().sum(axis=1).values[:, None] - N) & ok

S = {
 "persist63":   fr.gt(1e-4).rolling(63).mean().shift(1),
 "persist21":   fr.gt(1e-4).rolling(21).mean().shift(1),
 "persist189":  fr.gt(1e-4).rolling(189).mean().shift(1),
 "fund_accel":  (fr.rolling(9).mean() - fr.rolling(63).mean()).shift(1),
 "basis63":     (cl/mk - 1.0).rolling(63).mean().shift(1),
 "basis9":      (cl/mk - 1.0).rolling(9).mean().shift(1),
 "taker63":     (tbq/qv - 0.5).rolling(63).mean().shift(1),
 "mom63":       (op.shift(1)/op.shift(64) - 1.0),
 "mom21":       (op.shift(1)/op.shift(22) - 1.0),
 "vol_ratio":   (r8.rolling(9).std()/r8.rolling(63).std()).shift(1),
 "carry_lvl":   carry,
}

def report(mask, sign, label):
    print(f"### {label} sleeve (sign {sign:+d}) — mean forward-{H} EXCESS return by tercile of state")
    for nm, X in S.items():
        Xm = X.where(mask)
        row = []
        for lab, lo, hi in (("lo",0.0,0.334),("mid",0.334,0.667),("hi",0.667,1.001)):
            q = Xm.rank(axis=1, pct=True)
            sel = (q >= lo) & (q < hi) & mask
            vals = fwdrel.where(sel).stack()
            row.append((lab, vals.mean()*1e4, len(vals)))
        contrib = [(lab, sign*mval, n) for lab, mval, n in row]
        print(f"  {nm:12s} " + "  ".join(f"{lab}:{mv:+7.1f}bps(n={n})" for lab, mv, n in contrib))
    print()

report(short_side, -1, "SHORT")
report(long_side, +1, "LONG")
