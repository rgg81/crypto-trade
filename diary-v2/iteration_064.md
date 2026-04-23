# iter-v2/064 Diary

**Date**: 2026-04-23
**Type**: EXPLOITATION (per-symbol position cap, no architecture change)
**Parent baseline**: iter-v2/059-clean
**Decision**: **NO-MERGE** — concentration fixed, but OOS monthly −14% too aggressive

## Summary

Applied NEAR position cap at 0.7× base ($700 notional vs $1000). Fixed
NEAR concentration (44.44% → 35.89%) but gave up 14% OOS monthly Sharpe
(+1.66 → +1.43). Combined monthly dropped 9% (2.70 → 2.46) — primary
MERGE rule fails.

## Key findings

### 1. Concentration fix WORKS

NEAR dropped from 44.44% to 35.89% of OOS positive wpnl, max share
dropped from 44.44% (NEAR) to 38.71% (XRP). Both under n=4 40% cap.

### 2. max_amount_usd alone does NOT cap concentration

Initial implementation set `BacktestConfig.max_amount_usd=700` for NEAR.
That had ZERO effect on weighted_pnl or concentration because
`weighted_pnl = net_pnl_pct × weight_factor`, and `max_amount_usd` only
sets notional (affects `amount_usd` stored on Order but not trade PnL
percentage). Correct fix: post-process trades to scale
`weight_factor` and `weighted_pnl` directly.

Lesson: any future position-sizing intervention must target
`weight_factor`, not `max_amount_usd`.

### 3. 0.7× cap is too aggressive

Monthly Sharpe regression math:
- 30% NEAR reduction → 13.3% total PnL reduction (NEAR was 44% of
  positive wpnl)
- Sharpe regression is ~14% — slightly worse than proportional because
  removing one symbol's contribution doesn't reduce std proportionally

### 4. Pre-registered failure mode check

The brief predicted: *"if OOS daily Sharpe drops >15%, the cap is
destroying a hedge."* Actual daily Sharpe drop: −5.4%. Well within the
15% guardrail — the hedging-loss concern did NOT materialize.

But the brief's formal criterion was OOS MONTHLY ≥ 0.90 × baseline.
Monthly dropped 14% vs the 10% tolerance. Monthly is stricter than daily
because it reflects period-by-period performance more cleanly. This was
the miss.

## MERGE criteria

| # | Criterion | Target | Actual | Pass |
|---|---|---|---|---|
| 1 | Combined monthly Sharpe ≥ 2.70 | ≥ 2.70 | 2.46 | FAIL |
| 2 | NEAR concentration < 40% | < 40% | 35.89% | PASS |
| 3 | OOS monthly ≥ 0.90 × baseline | ≥ +1.49 | +1.43 | FAIL |
| 4 | IS monthly ≥ 0.85 × baseline | ≥ +0.88 | +1.03 | PASS |
| 5 | OOS PF, Sharpe > 0, trades ≥ 50 | — | 1.74, +1.57, 57 | PASS |
| 6 | OOS MaxDD ≤ 1.2 × baseline | ≤ 27.1% | 26.57% | PASS |

2 FAILs. **NO-MERGE**.

## Next Iteration Ideas — iter-v2/065

### 1. (primary) Retry with NEAR at 0.8× cap

Softer cap should achieve concentration target with less Sharpe cost.
Predicted math:

- NEAR wpnl: 35.54 × 0.8 = 28.43 → share ≈ 39.0% (just under 40% cap)
- Total positive wpnl: 72.87 (vs 79.98 baseline, −9%)
- Expected OOS Sharpe: ~−4-5% vs baseline instead of −14%

This should land at combined monthly ≈ 2.60-2.65, within MERGE tolerance.
The concentration margin is tighter (39% vs 40% cap) — pass with 1pp
margin instead of 4pp. Acceptable given the Sharpe savings.

Very cheap to run: same trick of applying the cap to iter-v2/059-clean's
trade list + regenerating reports. No backtest compute needed (~30s).

### 2. (alternative) Search over cap grid 0.75, 0.80, 0.85

Parameter sweep across 3-4 cap values, all derived from iter-v2/059-clean
trades. Find the best combined Sharpe that still passes 40% cap. ~2 min
compute.

### 3. Per-symbol cap on TOP 2 symbols

Cap NEAR 0.8× AND XRP 0.9×. Rationale: after NEAR cap, XRP becomes the
max (38.71%). Capping both may rebalance further. But adds a parameter.

**Recommended iter-v2/065**: option 2 (full parameter sweep) to find the
optimal cap with minimal Sharpe cost. Since iter-v2/059-clean trades
reused, it's essentially free.
