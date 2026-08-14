"""Parity: the real candidate strategy through the organiser's generate_targets, versus the
offline mirror. Free -- generate_targets reads only the IS snapshot and scores nothing."""
from __future__ import annotations
import sys, time, importlib.util
import numpy as np, pandas as pd
sys.path.insert(0, "tournament/cup20/teams/team-12/research")
from panel import Panel
import combine as CB
from crypto_trade.tournament.engine_v2 import generate_targets
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN

cand = sys.argv[1]
spec = importlib.util.spec_from_file_location(
    "teamstrat", f"tournament/cup20/teams/team-12/candidates/{cand}/strategy.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

p = Panel(); n = len(p.times); elig = p.eligible[p.t0:p.t0+n]
t = time.time()
tg = generate_targets(mod.build_strategy(), p.snapshot.bars, p.snapshot.funding,
                      p.snapshot.membership, list(p.times), seed=20240817, interval_hours=8)
print(f"generate_targets: {time.time()-t:.1f}s   rows={len(tg)} rebal={int(tg[REBALANCE_INSTRUCTION_COLUMN].sum())}")

sl = CB.build_sleeves(p, elig, carry_lb=mod.CARRY_LOOKBACK, trend_base=mod.TREND_BASE_LOOKBACK,
                      lowrisk_base=mod.LOWRISK_BASE_LOOKBACK, flow_base=mod.FLOW_BASE_LOOKBACK)
names = tuple(k for k, u in (("carry", mod.USE_CARRY), ("trend", mod.USE_TREND),
                             ("lowrisk", mod.USE_LOWRISK), ("flow", mod.USE_FLOW)) if u)
W, mult, xs = CB.combine(p, sl, names=names, risk_parity_bars=mod.RISK_PARITY_BARS,
                         equal_notional=bool(mod.EQUAL_NOTIONAL))
rb = (np.arange(n) % mod.REBALANCE_CADENCE == mod.REBALANCE_PHASE % mod.REBALANCE_CADENCE)
rb &= np.abs(W).sum(axis=1) > 0

cols = [c for c in tg.columns if c != REBALANCE_INSTRUCTION_COLUMN]
A = tg.reindex(columns=p.symbols).fillna(0.0).to_numpy(dtype=float)
Ar = tg[REBALANCE_INSTRUCTION_COLUMN].to_numpy(dtype=bool)
# both normalised to unit gross before comparison (the evaluator does this anyway)
def ug(M):
    g = np.abs(M).sum(axis=1); return M / np.where(g > 0, g, 1.0)[:, None]
An, Wn = ug(A), ug(W)
print("rebalance flag mismatches:", int((Ar != rb).sum()))
d = np.abs(An - Wn)
mask = Ar & rb
print("max |dW| on common rebalance rows:", float(d[mask].max()))
print("mean |dW|:", float(d[mask].mean()))
bad = np.where(d.max(axis=1) > 1e-9)[0]
print("rows with any |dW|>1e-9:", len(bad), bad[:10])
np.save("tournament/cup20/teams/team-12/research/_parity_W.npy", W)
