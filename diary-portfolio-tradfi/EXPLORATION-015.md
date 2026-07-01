# EXPLORATION-015 — Cost discipline: band + rebalance-frequency (iter-015)

**Date:** 2026-07-01 · **Status (Critic-revised):** cost-capture at the **LEAST-AGGRESSIVE ROBUST**
cell **δ=0.010 / freq=1** — makes the baseline 2×-cost-ROBUST with gross AND net-β held. OOS UNTOUCHED (IS-only).
**Cost cycle on baseline iter-013.** Prior corner headline (δ=0.020/freq=10) RETRACTED — it breaches net-β.

## Goal
Close the gross(+0.81)→net gap on iter-013 (net +0.61 @6bps, +0.42 @12bps = 2×-FRAGILE). Cost reduction only —
preserve the gross edge + 13/16 years + controlled net-β (≤~0.15). Judge IS-only; do NOT tune to the revealed OOS.

## Critic BLOCK-PENDING-FIX resolved
Old headline was a grid-CORNER max-net pick, **net-β never computed**, interior unmapped. Now: (1) net-β
(realized OLS beta of deployed net on EW-69 fwd return, `iter_013.net_beta`, VIX-off; baseline reproduces
iter-013 β +0.12 exactly) added to EVERY cell; (2) FULL joint grid δ∈{0.005,0.010,0.015,0.020,**0.025**}×freq∈{1,2,5,10};
(3) selection = SMALLEST band+freq step clearing **net@2×≥+0.50 AND gross≥+0.78 AND net-β≤0.15 AND +yrs≥13** (ties prefer freq=1).

## FULL joint grid (net@2× / gross / **net-β** / +yrs; `[✓]`=clears all four)
| δ\freq | 1 | 2 | 5 | 10 |
|--|--|--|--|--|
| 0.005 | +0.42/+0.81/.120/13 | +0.49/+0.80/.115/12 | +0.51/+0.72/.126/13 | +0.53/+0.69/.125/14 |
| 0.010 | **+0.52/+0.81/.129/13 [✓]** | +0.51/+0.75/.121/12 | +0.51/+0.68/.133/12 | +0.51/+0.65/.134/13 |
| 0.015 | +0.43/+0.66/.138/13 | +0.44/+0.62/.129/13 | +0.46/+0.61/.142/14 | +0.54/+0.66/.141/13 |
| 0.020 | +0.53/+0.72/.149/13 | +0.49/+0.64/.138/12 | +0.64/+0.76/.145/12 | +0.68/+0.78/**.156**/14 |
| 0.025 | +0.69/+0.84/**.151**/13 | +0.53/+0.66/.133/13 | +0.57/+0.67/.154/14 | +0.49/+0.57/.135/13 |

**Exactly one cell clears all four gates: δ=0.010/freq=1.** The two highest-net cells (corner
0.020/f10 = +0.68 and 0.025/f1 = +0.69) both carry **β>0.15** (0.156, 0.151) → REJECTED.

## CHOSEN (least-aggressive robust) = δ=0.010, freq=1
| | net@1× | net@2× | turnover | gross | **net-β** | +yrs |
|--|--------|--------|----------|-------|-----------|------|
| iter-013 | +0.61 | +0.42 (fragile) | 0.0939 | +0.81 | +0.120 | 13/16 |
| **iter-015** | **+0.67** | **+0.52 (robust)** | 0.0700 (−25%) | **+0.81** | **+0.129** | **13/16** |

**Real cost-capture, not de-lever:** gross exactly held +0.81→+0.81 while net@2× rises +0.10; net-β
+0.120→+0.129 (≤0.15 MET). Single band step (0.005→0.010), freq stays daily → **no live-parity risk**.

## Per-year (δ=0.010/f1 vs iter-013): ZERO sign flips
+yrs 13/16→13/16. Same 3 structural negatives (2010 ragged, 2018-Q4 bear, 2019 TSMOM whipsaw); every
other year holds/improves. **Deliberately avoids the 13→14 noise "flip"** the Critic flagged in the old
corner — no marginal monthly-Sharpe count crossing is claimed. Leak PASS (pinned to deployed cell). OOS untouched.

## Verdict / next
Turns the 2×-cost-fragile confirmed baseline into a 2×-cost-ROBUST book at the SMALLEST safe change,
with the gross edge, year-profile (13/16), and net-β (≤0.15) all intact — a **strict improvement** on
the cost axis with no regression. Leading candidate to REPLACE iter-013 as baseline, pending QR
CONFIRMATION + held-out OOS check (not tuned). More net@2× would require β>0.15 on this grid, so future
work must target the fast-momentum churn engine (per-sleeve cadence / slower horizon), not band+freq widening.
