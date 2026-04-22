# Iteration 181 — R5 LINK soft-cap (rejected)

**Date**: 2026-04-22
**Type**: EXPLOITATION (mechanical concentration control)
**Baseline**: v0.176 — unchanged
**Decision**: NO-MERGE

## Experiment

Post-hoc simulation of R5 concentration soft-cap: scale LINK's weighted_pnl by a fixed factor (representing a runner-level reduction in LINK's `max_amount_usd`). Measure impact on pooled portfolio metrics.

## Result

| LINK scale | IS Sharpe | OOS Sharpe | OOS MaxDD | OOS PnL   | LINK% |
|-----------:|----------:|-----------:|----------:|----------:|------:|
| 1.00 (v0.176) | +1.338 | +1.414     | 27.20%    | +83.75%   | 78.0% |
| 0.90       | +1.341    | +1.343     | 27.11%    | +77.22%   | 76.1% |
| 0.80       | +1.341    | +1.264     | 27.01%    | +70.68%   | 73.9% |
| 0.60       | +1.327    | +1.083     | 26.83%    | +57.62%   | 68.0% |
| 0.50       | +1.312    | +0.980     | 26.98%    | +51.09%   | 63.9% |
| 0.30       | +1.261    | +0.754     | 35.21% IS | +38.02%   | 51.5% |

Each 10% scale reduction costs ~0.07 OOS Sharpe and ~6.5% OOS PnL, while only moving LINK concentration by ~2.5 pp. At scale=0.50, OOS Sharpe drops below the 1.0 merge floor. At scale=0.30, concentration is still 51.5% (above target 30%).

## Why R5 weight-scaling doesn't work here

LINK is the portfolio's highest-signal model. Mechanically reducing its contribution reduces portfolio Sharpe roughly linearly because:

1. LINK's trades have high expected return per unit weight (51% WR at 2:1 RR).
2. Reducing LINK's weight reduces both its contribution and its variance proportionally, so per-trade Sharpe from LINK stays the same — just scaled.
3. Pooled Sharpe is a weighted average of the component symbols; reducing the best component's weight drags down the average.

R5 via simple scaling is equivalent to "trade LINK less aggressively" — it costs alpha to buy diversification. For a portfolio where LINK is objectively the highest-signal model, that's a bad trade.

## What would work (for future iterations)

1. **Running-balance R5** (time-varying): Only scale LINK down AFTER its cumulative share crosses a threshold. This preserves LINK's early-period contributions (which are healthy) and only intervenes when concentration becomes problematic. More complex to implement (requires merged-chronological-trade view at runtime).
2. **Improve other models' signal strength**: The real way to reduce concentration is to make BTC/ETH/LTC/DOT more competitive. That's a model-level change, not a risk-mitigation one.
3. **Accept current concentration**: Baseline v0.176's LINK% of 78% is the tradeoff for its IS+OOS Sharpe of +1.34/+1.41. Structurally, a 4-symbol portfolio can't reach 30% concentration unless each symbol contributes exactly 25%. That's asking for uniform signal across symbols we've not been able to achieve.

## Decision

NO-MERGE. Baseline v0.176 stands as the production baseline.

## Exploration/Exploitation Tracker

Window (171-181): [E, X, E, E, X, E, E, E, X, E, X] → 7E/4X.

## Next Iteration Ideas

- **Iter 182**: R3 OOD detector (Mahalanobis z-score). The canonical "model is out-of-distribution" defence. More complex to implement but directly addresses the 2022-style failure mode.
- **Iter 183**: Time-varying R5 (running-balance). Schedule trade-level scaling based on cumulative per-symbol share, not a fixed factor.
- **Iter 184+**: Model A improvement. Model A contributes only ~10% of OOS PnL at Sharpe +0.24 — lots of headroom. Per-symbol sub-models (with pruned feature sets) could extract more signal from BTC and ETH.
