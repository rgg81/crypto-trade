# EXPLORATION-015 — Cost discipline: band + rebalance-frequency (iter-015)

**Date:** 2026-07-01 · **Status:** STRONG candidate — makes the baseline 2×-cost-ROBUST, gross held. OOS UNTOUCHED (IS-only).
**Commit:** `8420b06b` · cost cycle on baseline iter-013

## Goal
Close the gross(+0.81)→net gap on iter-013 (net +0.61 @6bps, +0.42 @12bps = 2×-FRAGILE). Cost reduction only —
preserve the gross edge + 13/16 years. Judge IS-only; do NOT tune to the revealed OOS.

## Teardown (cost_teardown.py)
MOM sleeve = **75%** of turnover (fast 3-1m churns 3× the slow: 0.163 vs 0.054), LTR 14%, TSMOM 11%, bear-gate ~0.
81% of trade EVENTS = only 13% of turnover → cost is the fewer LARGER rebalances → FREQUENCY is the bigger lever.

## Sweeps (IS-only; δ→net@1×/net@2×/turn/gross/+yrs, VIX-ON)
Band (freq=1): 0.005 +0.61/+0.42/0.094/+0.81/13 · **0.010 +0.67/+0.52/0.070/+0.81/13** · 0.020 +0.63/+0.53/0.044/+0.72/13 · 0.030 +0.65/+0.59/0.031/+0.71/13 · 0.050 +0.50/+0.46/0.020/+0.54/10.
Freq (δ=0.005): 2 +0.64/+0.49 · 5 +0.61/+0.51 · 10 +0.61/+0.53.

## BEST (joint) = δ=0.020, freq=10
| | net@1× | net@2× | turnover | gross | +yrs |
|--|--------|--------|----------|-------|------|
| iter-013 | +0.61 | +0.42 (fragile) | 0.094 | +0.81 | 13/16 |
| **iter-015** | **+0.73** | **+0.68 (robust)** | 0.024 (−75%) | +0.78 | **14/16** |

**Real cost-capture, not de-lever:** gross held +0.81→+0.78 (Δ−0.03) while net@2× jumps +0.26. Broad
δ=0.02×freq{5,10} plateau (not a knife-edge). Leak PASS (two_lever_future_bar_no_leak). OOS untouched.

## Verdict / next
Turns the 2×-cost-fragile confirmed baseline into a 2×-cost-ROBUST book with the gross edge + year-profile
intact (14/16). Leading candidate to REPLACE iter-013 as baseline — pending Critic (leak on the 10-day hold +
band, overfit on δ=0.02/freq=10, cost realism for a slower book) + held-out OOS check (not tuned).
