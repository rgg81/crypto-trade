# Iteration 182 — R2 on LINK and LTC (rejected)

**Date**: 2026-04-22
**Type**: EXPLOITATION
**Baseline**: v0.176 — unchanged
**Decision**: NO-MERGE

## Experiment

Post-hoc simulation: extend R2 drawdown-scaling beyond DOT to LINK and/or LTC. 8 variants tested.

## Result

| Variant                                     | IS Sharpe | OOS Sharpe | OOS MaxDD | OOS PnL | LINK% |
|---------------------------------------------|----------:|-----------:|----------:|--------:|------:|
| v0.176 baseline (LINK R1, LTC R1, DOT R1R2) | +1.338    | **+1.414** | **27.20%**| +83.75% | 78.0% |
| +LINK R2(10,25,0.5)                         | +1.295    | +1.359     | 27.48%    | +79.70% | 76.9% |
| +LTC R2(5,15,0.33)                          | +1.347    | +1.415     | 29.43%    | +77.83% | 83.9% |
| +BOTH LINK+LTC R2(5,15,0.33)                | +1.293    | +1.209     | 27.45%    | +63.47% | 80.3% |

No variant strictly beats v0.176 on OOS Sharpe+MaxDD. `LTC R1+R2(5,15,0.33)` ties OOS Sharpe (+1.415) but regresses MaxDD. Adding R2 to LINK always costs OOS Sharpe (LINK's trades are mostly winning — scaling them down during drawdown removes upside with the downside).

## Why R2 helps DOT but not LINK/LTC

DOT's OOS MaxDD without R2 was 19.65% on a standalone symbol with high variance. R2 cut it to 6.49%. That's a massive compression.

LINK and LTC already have healthy MaxDD profiles (LINK's drawdowns come with fast recoveries). Scaling them during drawdown misses the recovery trades. R2's benefit is asymmetric — it helps assets with deep, slow drawdowns like DOT's 2022.

## Decision

NO-MERGE. v0.176 remains the production baseline.

## Exploration/Exploitation Tracker

Window (172-182): [E, X, E, E, X, E, E, E, X, E, X] → 7E/4X.
