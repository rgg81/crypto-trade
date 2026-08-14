"""Does the offline combination reproduce the real mse-01 candidate's emitted weights exactly?"""
from __future__ import annotations
import sys, importlib.util
import numpy as np
sys.path.insert(0, "tournament/cup20/teams/team-12/research")
from panel import Panel
import combo as CO
from sleevegen import sleeve_matrix
from crypto_trade.tournament.engine_v2 import generate_targets
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN

p = Panel()
mats = {s: sleeve_matrix(p, s, {}) for s in CO.SLEEVES}
W, mus = CO.combine(p, mats, bars=270)
n = len(p.times)
rb = CO.rebalance(n, 6, 3, W)

spec = importlib.util.spec_from_file_location(
    "cand", "tournament/cup20/teams/team-12/candidates/mse-01/strategy.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
tg = generate_targets(mod.build_strategy(), p.snapshot.bars, p.snapshot.funding,
                      p.snapshot.membership, list(p.times), seed=20200817, interval_hours=8)
A = tg.reindex(columns=p.symbols).fillna(0.0).to_numpy(dtype=float)
Ar = tg[REBALANCE_INSTRUCTION_COLUMN].to_numpy(dtype=bool)
def ug(M):
    g = np.abs(M).sum(axis=1); return M / np.where(g > 0, g, 1.0)[:, None]
An, Wn = ug(A), ug(W)
print("rebalance flag mismatches:", int((Ar != rb).sum()))
m = Ar & rb
print("max |dW| on rebalance rows:", float(np.abs(An - Wn)[m].max()))
print("mean |dW| on rebalance rows:", float(np.abs(An - Wn)[m].mean()))
for k in CO.SLEEVES:
    mu = mus[k]
    print(f"  multiplier {k:8s} median={np.median(mu[270:]):8.2f} "
          f"p10={np.percentile(mu[270:],10):8.2f} p90={np.percentile(mu[270:],90):8.2f}")
# effective gross share of each sleeve in the combined book
tot = sum(np.abs(mus[k][:, None] * mats[k]).sum(axis=1) for k in CO.SLEEVES)
for k in CO.SLEEVES:
    sh = np.abs(mus[k][:, None] * mats[k]).sum(axis=1) / np.where(tot > 0, tot, 1)
    print(f"  gross share {k:8s} median={np.median(sh[270:]):.3f}")
