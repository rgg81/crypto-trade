# Iteration 153 Engineering Report

## Extended Grid Results (target=0.3, lookback=45)

| min_scale | IS Sharpe | OOS Sharpe | OOS MaxDD | OOS PF | avg_scale |
|-----------|-----------|-----------|-----------|--------|-----------|
| 0.10 | 1.2192 | +2.6714 | 17.97% | **2.09** | 0.29 |
| 0.15 | 1.2603 | +2.7470 | 17.32% | 1.99 | 0.33 |
| 0.20 | 1.2943 | +2.7970 | **16.68%** | 1.91 | 0.37 |
| 0.25 | 1.3184 | +2.8223 | 16.92% | 1.84 | 0.41 |
| 0.30 | 1.3296 | **+2.8306** | 19.98% | 1.78 | 0.45 |
| **0.33 (PROD)** | **1.3320** | +2.8286 | 21.81% | 1.76 | 0.47 |
| 0.50 | 1.3056 | +2.7356 | 32.22% | 1.64 | 0.61 |

## Findings

**IS Sharpe peaks at 0.33** within tested range. Going lower hurts IS because
aggressive deleveraging during IS vol periods reduces PnL more than volatility.

**OOS behavior**: MaxDD and PF continue to improve as floor drops, but Sharpe
flattens. Lower floors (0.15-0.25) give better risk-adjusted single-trade metrics
but similar time-averaged Sharpe.

**Walk-forward pick**: IS-best is 0.33 (production). Confirms iter 152.

## Robustness Check

Across min_scale ∈ [0.10, 0.75]: OOS Sharpe stays in [+2.67, +2.83]. Strategy
is well-behaved across a 7x range of risk floor. Not sensitive to exact choice.

## Decision: NO-MERGE

IS Sharpe at min_scale=0.10 is 1.2192, below 0.33's 1.3320. Walk-forward rules
select 0.33. Current production config remains optimal.
