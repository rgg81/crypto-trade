# Iteration 184 — R4 realized-vol kill-switch (rejected)

**Date**: 2026-04-22
**Type**: EXPLOITATION (risk-mitigation design, evidence-driven)
**Baseline**: v0.176
**Decision**: NO-MERGE

## Section 0 — Data Split (non-negotiable)

- OOS cutoff: 2025-03-24 (fixed)
- Analysis uses pooled v0.176 trades rebuilt from `reports/iteration_152`, `165`, `172`.

## Phase 1 — EDA (IS + OOS — this is a post-hoc analysis, QR sees both)

Per trade, computed the 30-day realized log-return volatility of the underlying
at the moment the trade opened. Bucketed all 976 v0.176 trades into per-segment
quintiles.

### IS bucket table (2022-01 → 2025-03-24)

| bucket | trades | vol30 mean | WR    | mean net_pnl_pct | sum weighted_pnl |
|-------:|-------:|-----------:|------:|-----------------:|-----------------:|
| Q0     | 147    | 38.50%     | 46.9% | +0.60%           | +62.74%          |
| Q1     | 146    | 52.43%     | 39.7% | −0.15%           | −9.40%           |
| Q2     | 147    | 65.35%     | 39.5% | +0.08%           | +15.97%          |
| Q3     | 146    | 82.18%     | **48.6%** | **+1.06%**   | **+102.52%**     |
| Q4     | 147    | 111.85%    | 45.6% | +0.99%           | +80.27%          |

### OOS bucket table (2025-03-24 onwards)

| bucket | trades | vol30 mean | WR    | mean net_pnl_pct | sum weighted_pnl |
|-------:|-------:|-----------:|------:|-----------------:|-----------------:|
| Q0     | 49     | 39.75%     | 28.6% | −0.58%           | −4.27%           |
| Q1     | 48     | 57.36%     | 45.8% | +1.13%           | +22.65%          |
| Q2     | 49     | 67.77%     | 42.9% | +0.73%           | +3.50%           |
| Q3     | 48     | 74.18%     | 43.8% | +0.56%           | +24.81%          |
| Q4     | 49     | 97.21%     | **49.0%** | **+2.09%**   | **+37.06%**      |

## Finding

**Higher realized vol → higher expected PnL, in both IS and OOS.**
The top vol quintile has the best mean PnL and the highest WR in OOS.
Low-vol periods (Q0) are the least profitable — in OOS, Q0 is actually net-negative.

## Kill-switch simulation

Applied a per-symbol vol cutoff that drops trades with `vol30` above the Nth
percentile of that symbol's IS distribution.

| cutoff | IS Sharpe | IS PnL | OOS Sharpe | OOS PnL |
|-------:|----------:|-------:|-----------:|--------:|
| 1.00 (baseline) | **+1.338** | +252.10% | **+1.414** | +83.75% |
| 0.95   | +1.163    | +204.08% | +1.301    | +74.58% |
| 0.90   | +0.986    | +164.95% | +1.100    | +62.23% |
| 0.80   | +1.037    | +156.65% | +1.041    | +56.80% |
| 0.70   | +0.946    | +128.11% | +1.001    | +46.91% |
| 0.50   | +0.661    |  +69.28% | +1.148    | +49.42% |

Every threshold degrades both IS and OOS Sharpe. The most aggressive cutoff (0.50)
drops IS Sharpe by half.

## Why R4 fails

1. **Per-symbol vol-targeting is already in place.** v0.176 scales position size
   inversely to 45-day vol via `vt_scale`. The model already trades smaller in
   high-vol regimes; a kill-switch would on top of that suppress the most
   informative trading environments.
2. **The model's edge concentrates in volatile regimes.** High-vol bars often
   coincide with the directional-momentum events (breakouts, liquidation
   cascades) that 8h-candle LightGBM is designed to catch. Silencing these
   removes alpha, not risk.
3. **R4 as written is symmetric.** A proper kill-switch would distinguish
   "high vol because of sharp move in model's favor" from "high vol because of
   regime shift toward untrained distribution" — but that's the R3 OOD problem,
   not a pure vol kill-switch.

## Decision

NO-MERGE. v0.176 stands.

## Next Iteration Ideas

- **Iter 185**: The R3 OOD detector is the only remaining risk mitigation from
  the skill's R1-R5 list. Prototype Mahalanobis z-score on a small scale-invariant
  feature subset (RSI, returns, vol ratios) — block trades when z > threshold
  calibrated on IS tail.
- **Iter 186**: Post-hoc seed-robustness sweep of v0.176. Rerun the full portfolio
  with 3 alternative ensemble seed groupings and report mean/std of OOS Sharpe.
  Budget: ~30 min per config.
- **Iter 187+**: Stop doing mechanical risk mitigations; look for a positive-alpha
  improvement. Candidates: cross-asset features (BTC-ETH spread, BTC-LINK spread),
  a daily-timeframe trend filter, or sample-weight re-balancing using AFML
  uniqueness.

## Exploration/Exploitation Tracker

Window (174-184): [E, E, X, E, E, E, X, E, X, E, **X**] → 7E/4X → **7E/5X** after
this iteration. Tracker now balanced.
