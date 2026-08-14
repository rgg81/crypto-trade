"""THE combined evaluation. The weight rule was journaled at sequence #121 before this ran."""
from __future__ import annotations
import sys, json
import numpy as np, pandas as pd
sys.path.insert(0, "tournament/cup20/teams/team-12/research")
from panel import Panel
import combo as CO, fastsim as FS, metricsfast as MF
from sleevegen import sleeve_matrix

p = Panel(); n = len(p.times)
mats = {s: sleeve_matrix(p, s, {}) for s in CO.SLEEVES}
CAD = 6
def block(label, W):
    rows = []
    for ph in range(CAD):
        sc = CO.score(p, W, CAD, ph)
        rows.append(sc)
    a = np.array([[r["G"], r["net_sharpe"], r["double_cost_sharpe"], r["worst_fold_sharpe"],
                   r["median_fold_sharpe"], r["max_drawdown"], r["double_cost_max_drawdown"],
                   r["calmar"], r["double_cost_positive_quarter_fraction"],
                   r["annualized_volatility"], r["annualized_turnover"], r["B"],
                   r["long_gross_pnl"], r["short_gross_pnl"], r["trade_count"]] for r in rows])
    m = a.mean(axis=0)
    print(f"{label:26s} G={m[0]:6.2f}[{a[:,0].min():6.1f},{a[:,0].max():6.1f}] Sh1={m[1]:.3f} "
          f"Sh2={m[2]:.3f} worst={m[3]:+.3f} med={m[4]:.3f} DD1={m[5]:.3f} DD2={m[6]:.3f} "
          f"cal={m[7]:.2f} q2={m[8]:.2f} vol={m[9]:.3f} trn={m[10]:5.1f} B={m[11]:.4f} "
          f"L={m[12]:+.2f} S={m[13]:+.2f} n={int(m[14])}")
    sys.stdout.flush()
    return rows, m

print("=== SLEEVES STANDALONE (each own unit-gross book) ===")
sleeve_rows = {}
for s in CO.SLEEVES:
    sleeve_rows[s], _ = block(f"sleeve {s}", mats[s])

print("\n=== COMBINED, preregistered inverse-vol rule ===")
W, mus = CO.combine(p, mats, bars=270)
comb_rows, comb_m = block("ENSEMBLE (rule)", W)

print("\n=== CONTROL: equal notional (same sleeves, no risk parity) ===")
Wen, _ = CO.combine(p, mats, equal_notional=True)
block("ensemble equal-notional", Wen)

print("\n=== CONTROL: leave-one-out (rule preserved on the remaining sleeves) ===")
for drop in CO.SLEEVES:
    names = tuple(s for s in CO.SLEEVES if s != drop)
    Wd, _ = CO.combine(p, mats, names=names, bars=270)
    block(f"drop {drop}", Wd)

print("\n=== ORTHOGONALITY: sleeve daily-return correlations (own standalone books, 1x) ===")
d = {}
for s in CO.SLEEVES:
    rb = CO.rebalance(n, CAD, 3, mats[s])
    r = FS.run_book(mats[s], rb, p)
    d[s] = FS.daily(r["results"][1]["net_return"], p.times)
D = pd.DataFrame(d)
print(D.corr().round(3).to_string())
print("\n--- underwater (drawdown) series correlations ---")
U = {}
for s in CO.SLEEVES:
    eq = (1 + D[s]).cumprod()
    U[s] = eq / eq.cummax() - 1.0
UD = pd.DataFrame(U)
print(UD.corr().round(3).to_string())
print("\n--- fraction of days both sleeves are >5% underwater ---")
deep = (UD < -0.05)
for i, a in enumerate(CO.SLEEVES):
    print("  " + a[:8].ljust(9) + " ".join(f"{float((deep[a]&deep[b]).mean()):.3f}" for b in CO.SLEEVES))
print("  cols     " + " ".join(s[:5].ljust(5) for s in CO.SLEEVES))
