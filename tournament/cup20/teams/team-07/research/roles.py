"""Long / short / chop role check for the nominated book. Regime split is the team's own
approximate simulation (research/sim2.py), used to describe behaviour, not to score."""
from __future__ import annotations
import sys, importlib.util, numpy as np, pandas as pd
sys.path.insert(0, "tournament/cup20/teams/team-07/research")
from crypto_trade.cup20.snapshot import load_snapshot, resolve_is_start
from crypto_trade.tournament.engine_v2 import generate_targets
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN
from strat import data
from sim2 import simulate, reference_scalars, metrics

spec = importlib.util.spec_from_file_location("nom",
    "tournament/cup20/teams/team-07/candidates/carry-crowd-guard/strategy.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
snap = load_snapshot("data/cup20/is")
is_start = resolve_is_start(snap.membership, target_size=20)
p = data(); grid = p["grid"]; times = [t for t in grid if t >= is_start]
tg = generate_targets(mod.build_strategy(), snap.bars, snap.funding, snap.membership, times,
                      seed=20260807, interval_hours=8)
cols = [c for c in tg.columns if c != REBALANCE_INSTRUCTION_COLUMN]
reb = tg[REBALANCE_INSTRUCTION_COLUMN].astype(bool)
W = tg[cols].reindex(columns=p["open"].columns).fillna(0.0)
tl = [None if not reb.iloc[i] else W.iloc[i].to_numpy() for i in range(len(W))]
ref,_ = simulate(tl, p["fwd_price"], p["fwd_fund"], 1.0)
sc = reference_scalars(ref, grid)
r1, tr = simulate(tl, p["fwd_price"], p["fwd_fund"], 1.0, sc)

print("=== leg decomposition of the NOMINATED book (approximate simulator) ===")
edges=[r1.index[0]]+[pd.Timestamp(x,tz="UTC") for x in ["2021-08-01","2022-08-01","2023-08-01"]]+[r1.index[-1]+pd.Timedelta(hours=8)]
print(f"{'fold':10s} {'price':>8} {'funding':>8} {'cost':>8} {'net':>8}")
for i,(a,b) in enumerate(zip(edges[:-1],edges[1:])):
    s = r1[(r1.index>=a)&(r1.index<b)]
    print(f"F{i+1:<9d} {s['price'].sum():+8.3f} {s['fund'].sum():+8.3f} {-s['cost'].sum():+8.3f} {s['net'].sum():+8.3f}")
s=r1
print(f"{'TOTAL':10s} {s['price'].sum():+8.3f} {s['fund'].sum():+8.3f} {-s['cost'].sum():+8.3f} {s['net'].sum():+8.3f}")

print("\n=== role check: market-regime buckets (equal-weight eligible universe, 63-boundary trend) ===")
ok = p["ok"]; mkt = p["open"].where(ok).pct_change().mean(axis=1)
trend = mkt.rolling(63).sum().shift(1).reindex(r1.index)
vol = mkt.rolling(63).std().shift(1).reindex(r1.index) * np.sqrt(3*365)
q = pd.qcut(trend.dropna(), 3, labels=["trail_low","trail_mid","trail_high"])
BPY = 3*365
for lab in ["trail_low","trail_mid","trail_high"]:
    idx = q[q == lab].index
    seg = r1.loc[idx]
    sh = seg["net"].mean()/seg["net"].std()*np.sqrt(BPY)
    print(f"  {lab:10s} n={len(seg):5d}  net/yr={seg['net'].mean()*BPY:+.2%}  Sharpe={sh:+.2f}  "
          f"price={seg['price'].sum():+.3f} funding={seg['fund'].sum():+.3f}  "
          f"mkt/yr={mkt.reindex(idx).mean()*BPY:+.1%}")
qv = pd.qcut(vol.dropna(), 3, labels=["calm","mid","stressed"])
print()
for lab in ["calm","mid","stressed"]:
    idx = qv[qv == lab].index
    seg = r1.loc[idx]
    sh = seg["net"].mean()/seg["net"].std()*np.sqrt(BPY)
    print(f"  {lab:8s} n={len(seg):5d}  net/yr={seg['net'].mean()*BPY:+.2%}  Sharpe={sh:+.2f}  "
          f"price={seg['price'].sum():+.3f} funding={seg['fund'].sum():+.3f}")
