"""Direct evidence on the mandate's question: did the sleeves diversify DRAWDOWN, or only average
returns? Offline (replica agrees with the organiser evaluator to ~1e-5 in Sharpe and drawdown)."""
from __future__ import annotations
import sys
import numpy as np, pandas as pd
sys.path.insert(0, "tournament/cup20/teams/team-12/research")
from panel import Panel
import combo as CO, fastsim as FS
from sleevegen import sleeve_matrix

p = Panel(); n = len(p.times)
mats = {s: sleeve_matrix(p, s, {}) for s in CO.SLEEVES}
W, mus = CO.combine(p, mats, bars=270)
books = {"ENSEMBLE": W, **{s: mats[s] for s in CO.SLEEVES}}
D, U = {}, {}
for name, B in books.items():
    res = FS.run_book(B, CO.rebalance(n, 6, 3, B), p)["results"][1]
    d = FS.daily(res["net_return"], p.times); D[name] = d
    eq = (1 + d).cumprod(); U[name] = eq / eq.cummax() - 1.0
D = pd.DataFrame(D); U = pd.DataFrame(U)

print("=== time spent underwater, common risk unit, 1x cost ===")
for th in (0.02, 0.05, 0.08, 0.10):
    print(f"  deeper than {th:.0%}: " + "  ".join(f"{c}={float((U[c] < -th).mean()):.3f}" for c in U.columns))
print("\n=== longest underwater run (days) ===")
for c in U.columns:
    under = (U[c] < -1e-9).to_numpy(); best = cur = 0
    for v in under:
        cur = cur + 1 if v else 0
        best = max(best, cur)
    print(f"  {c:10s} {best}")

print("\n=== diversification ratio: sleeve-vol-weighted sum vs realised ensemble vol ===")
# gross share each sleeve carries in the executed ensemble
tot = sum(np.abs(mus[k][:, None] * mats[k]).sum(axis=1) for k in CO.SLEEVES)
share = {k: float(np.median((np.abs(mus[k][:, None] * mats[k]).sum(axis=1) / np.where(tot > 0, tot, 1))[270:]))
         for k in CO.SLEEVES}
print("  median gross share:", {k: round(v, 3) for k, v in share.items()})
sig = {k: float(D[k].std()) for k in CO.SLEEVES}
weighted = sum(share[k] * sig[k] for k in CO.SLEEVES)
print(f"  weighted-average sleeve daily vol = {weighted:.5f}")
print(f"  realised ENSEMBLE daily vol       = {float(D['ENSEMBLE'].std()):.5f}")
print(f"  diversification ratio             = {weighted / float(D['ENSEMBLE'].std()):.3f}  "
      f"(1.00 = no diversification; the sleeves are re-scaled to a common risk unit so this is "
      f"the pure correlation effect)")

print("\n=== worst 10 ensemble days: which sleeves were also losing ===")
worst = D["ENSEMBLE"].nsmallest(10)
print(D.loc[worst.index].round(4).to_string())

print("\n=== drawdown of the ensemble at each sleeve's own worst moment ===")
for k in CO.SLEEVES:
    t = U[k].idxmin()
    print(f"  {k:8s} trough {U[k].min():+.3f} on {t.date()}   ensemble underwater then: {U.loc[t,'ENSEMBLE']:+.3f}")

print("\n=== quarterly returns, 1x ===")
q = (1 + D).groupby(pd.DatetimeIndex(D.index).tz_convert('UTC').tz_localize(None).to_period('Q')).prod() - 1
print((q * 100).round(2).to_string())
print("\npositive quarters:", {c: int((q[c] > 0).sum()) for c in q.columns}, "of", len(q))
