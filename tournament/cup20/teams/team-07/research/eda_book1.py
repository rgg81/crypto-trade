"""EDA 2 — baseline cross-sectional funding carry, no protection."""
from __future__ import annotations
import sys, numpy as np, pandas as pd
sys.path.insert(0, "tournament/cup20/teams/team-07/research")
from panel import build_panel
from sim import run, metrics, G

p = build_panel()
g = p["grid"]; op = p["open"]; el = p["eligible"]; fr = p["funding"]
start = el.sum(axis=1).ge(20).idxmax()
m = g >= start
g = g[m]; op = op.loc[g]; el = el.loc[g]; fr = fr.loc[g]

fwd_price = (op.shift(-1) / op - 1.0)
fwd_fund = fr.shift(-1)
ok = el & fwd_price.notna()

def carry_weights(lookback, top_n=None, mode="zscore"):
    sig = fr.rolling(lookback, min_periods=max(1, lookback // 2)).mean().shift(1)
    sig = sig.where(ok)
    if mode == "zscore":
        d = sig.sub(sig.mean(axis=1), axis=0)
        W = -d
    else:  # rank thirds
        r = sig.rank(axis=1, pct=True)
        W = pd.DataFrame(0.0, index=sig.index, columns=sig.columns)
        W = W.where(sig.isna() | True)
        n = int(top_n)
        rk = sig.rank(axis=1, ascending=False)
        cnt = sig.notna().sum(axis=1)
        short = rk.le(n) & sig.notna()
        long = rk.gt(cnt.values[:, None] - n) & sig.notna()
        W = short.astype(float) * -1.0 + long.astype(float) * 1.0
    W = W.where(ok, 0.0).fillna(0.0)
    return W

for lb in (1, 3, 6, 9, 21, 42, 63, 126):
    W = carry_weights(lb, mode="zscore")
    r1, Wx, tr = run(W, fwd_price, fwd_fund, 1.0)
    r2, _, _ = run(W, fwd_price, fwd_fund, 2.0)
    m1 = metrics(r1, tr); m2 = metrics(r2, tr)
    print(f"z lb={lb:3d}  1x Sh={m1['sharpe']:+.2f} ret={m1['ann_ret']:+.1%} vol={m1['vol']:.1%} dd={m1['maxdd']:.1%} "
          f"turn={m1['turn_ann']:.1f}x cs={m1['cost_share']:.2f} | 2x Sh={m2['sharpe']:+.2f} folds={m2['folds']} "
          f"wf={m2['worst_fold']:+.2f} G={G(m1,m2):.1f} tr={tr}")

print()
for n in (3, 4, 5, 6, 7):
    for lb in (3, 9, 21, 63):
        W = carry_weights(lb, top_n=n, mode="rank")
        r1, Wx, tr = run(W, fwd_price, fwd_fund, 1.0)
        r2, _, _ = run(W, fwd_price, fwd_fund, 2.0)
        m1 = metrics(r1, tr); m2 = metrics(r2, tr)
        print(f"rank n={n} lb={lb:3d}  1x Sh={m1['sharpe']:+.2f} ret={m1['ann_ret']:+.1%} vol={m1['vol']:.1%} "
              f"dd={m1['maxdd']:.1%} turn={m1['turn_ann']:.1f}x | 2x Sh={m2['sharpe']:+.2f} "
              f"folds={m2['folds']} G={G(m1,m2):.1f} tr={tr}")
