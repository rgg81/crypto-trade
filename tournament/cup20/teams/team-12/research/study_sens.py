from __future__ import annotations
import sys
import numpy as np
sys.path.insert(0, "tournament/cup20/teams/team-12/research")
from panel import Panel
import combo as CO, metricsfast as MF
from sleevegen import sleeve_matrix

p = Panel(); n = len(p.times)
mats = {s: sleeve_matrix(p, s, {}) for s in CO.SLEEVES}

print("=== NOMINEE POINT: cadence 6, phase 3, RISK_PARITY_BARS 270, all four sleeves ===")
W, _ = CO.combine(p, mats, bars=270)
sc = CO.score(p, W, 6, 3, trial_count=2, label="mse-01 nominee")
for k in ("net_sharpe","double_cost_sharpe","triple_cost_sharpe","annualized_return",
          "double_cost_annualized_return","max_drawdown","annualized_volatility",
          "positive_quarter_fraction","positive_fold_count","worst_fold_sharpe",
          "median_fold_sharpe","calmar","annualized_turnover","gross_edge_bps_per_turnover",
          "cost_share_of_positive_gross","top5_day_share","max_fold_positive_pnl_share",
          "trade_count","long_gross_pnl","short_gross_pnl","double_cost_max_drawdown",
          "double_cost_positive_quarter_fraction","B","trial_adjusted_confidence","G"):
    print(f"   {k:38s} {sc[k]}")
print("   folds 2x:", [round(v,4) for v in sc["fold_sharpes_2x"]])

print("\n=== RISK_PARITY_BARS sensitivity (cadence 6, phase 3) ===")
for b in (135, 180, 225, 270, 315, 360, 450, 540):
    Wb, _ = CO.combine(p, mats, bars=b)
    CO.score(p, Wb, 6, 3, label=f"RPB={b}")

print("\n=== CADENCE sensitivity (phase-mean over every phase) ===")
for cad in (1, 3, 6, 9, 12, 21):
    Ws, _ = CO.combine(p, mats, bars=270)
    a = np.array([[CO.score(p, Ws, cad, ph)[k] for k in ("G","net_sharpe","worst_fold_sharpe","max_drawdown","annualized_turnover")]
                  for ph in range(cad)])
    m = a.mean(axis=0)
    print(f"  cad={cad:3d} G={m[0]:6.2f}[{a[:,0].min():6.1f},{a[:,0].max():6.1f}] Sh1={m[1]:.3f} worst={m[2]:+.3f} DD1={m[3]:.3f} trn={m[4]:.1f}")

print("\n=== PHASE detail at cadence 6 ===")
for ph in range(6):
    CO.score(p, W, 6, ph, label=f"phase {ph}")
