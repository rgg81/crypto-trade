"""Free pre-flight: run the real strategy object over the real snapshot through the organiser's
own target generator, then score it with the team's approximate simulator. No trial, no scoring
authority -- this only catches bugs before a trial is spent."""
from __future__ import annotations
import sys, time, importlib.util, numpy as np, pandas as pd
sys.path.insert(0, "tournament/cup20/teams/team-07/research")
from crypto_trade.cup20.snapshot import load_snapshot, resolve_is_start
from crypto_trade.tournament.engine_v2 import generate_targets
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN
from strat import data
from sim2 import simulate, reference_scalars, metrics, G, show

cand = sys.argv[1]
spec = importlib.util.spec_from_file_location(
    f"cand_{cand.replace('-','_')}", f"tournament/cup20/teams/team-07/candidates/{cand}/strategy.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

snap = load_snapshot("data/cup20/is")
is_start = resolve_is_start(snap.membership, target_size=20)
p = data(); grid = p["grid"]
times = [t for t in grid if t >= is_start]
t0 = time.time()
tg = generate_targets(mod.build_strategy(), snap.bars, snap.funding, snap.membership, times,
                      seed=20260807, interval_hours=8)
print(f"generate_targets: {time.time()-t0:.1f}s  rows={len(tg)}")
cols = [c for c in tg.columns if c != REBALANCE_INSTRUCTION_COLUMN]
reb = tg[REBALANCE_INSTRUCTION_COLUMN].astype(bool)
print(f"rebalancing boundaries: {int(reb.sum())} of {len(reb)}")
W = tg[cols].reindex(columns=p["open"].columns).fillna(0.0)
tl = [None if not reb.iloc[i] else W.iloc[i].to_numpy() for i in range(len(W))]
ref,_ = simulate(tl, p["fwd_price"], p["fwd_fund"], 1.0)
sc = reference_scalars(ref, grid)
r1, tr = simulate(tl, p["fwd_price"], p["fwd_fund"], 1.0, sc)
r2, _ = simulate(tl, p["fwd_price"], p["fwd_fund"], 2.0, sc)
m1, m2 = metrics(r1, tr), metrics(r2, tr)
show(cand, m1, m2, tr)
print(f"  gross edge {r1['gross'].sum()/r1['turnover'].sum()*1e4:.1f} bps/turnover   "
      f"G(approx)={G(m2):.1f}")
e=[r1.index[0]]+[pd.Timestamp(x,tz='UTC') for x in ['2021-08-01','2022-08-01','2023-08-01']]+[r1.index[-1]+pd.Timedelta(hours=8)]
print("  legs: " + "  ".join(
    f"[p{r1[(r1.index>=a)&(r1.index<b)]['price'].sum():+.3f} f{r1[(r1.index>=a)&(r1.index<b)]['fund'].sum():+.3f}]"
    for a,b in zip(e[:-1],e[1:])))
