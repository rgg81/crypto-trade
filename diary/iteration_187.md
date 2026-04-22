# Iteration 187 — Drop BTC? (rejected, Model A pool stays)

**Date**: 2026-04-22
**Type**: EXPLOITATION
**Baseline**: v0.186 — unchanged
**Decision**: NO-MERGE

## TL;DR

BTC contributed −7.6% of v0.186's OOS PnL. Post-hoc simulation: dropping
BTC moves OOS Sharpe by +0.019 (noise), costs −20% of trades, and lifts
MaxDD by +3.00 pp. Model A (BTC+ETH pool) is a net contributor because
pooled training benefits both. Keep as-is.

## Findings

| slice | OOS Sharpe | OOS MaxDD | OOS trades |
|-------|-----------:|----------:|-----------:|
| All (v0.186) | **+1.737** | 29.31% | 210 |
| Drop BTC | +1.756 | 32.31% | 167 |
| Drop BTC + ETH | +1.387 | 23.10% | 118 |
| BTC standalone | +0.308 | 13.34% | 43 |
| ETH standalone | +1.110 | 25.21% | 49 |

Dropping BTC+ETH together costs a clear −0.35 OOS Sharpe. The pool
contributes meaningful alpha even when decomposed-BTC looks weak.

## Why Model A pool works where standalone doesn't

BTC IS Sharpe +0.50, ETH IS Sharpe +0.16 — both weak individually.
Pooled Model A has OOS Sharpe that fits into a +1.74 portfolio. The
LightGBM model learns the cross-pattern between BTC and ETH features
(their common macro regimes, their shared covariate dynamics) and
predicts both better than either standalone model could.

This is the same argument that says v1-style ensembling helps: averaging
or pooling related signals beats individual weak learners. Dropping BTC
removes the cross-signal, not just the BTC trades.

## 2026 Q1 softness

BTC WR 20% and ETH WR 22% in early 2026 — sample sizes of 10 and 18.
Likely noise, but monitor. If Q2 continues the pattern, Model A might
need a retrain with different features or hyperparameters.

## Exploration/Exploitation Tracker

Window (177-187): [E, E, E, X, E, X, E, X, X, X, **X**] → **5E/6X**.
Balanced.

## Next Iteration Ideas

- **Iter 188**: Tighter OOD cutoffs. Try per-symbol post-hoc at 0.60 /
  0.50 on v0.186 trades. If IS Sharpe holds and OOS improves, retrain
  with the tighter cutoff.
- **Iter 189**: Per-symbol OOD cutoffs. BTC's feature-space regime might
  need a tighter filter than altcoins.
- **Iter 190**: ETH-only Model A retrain (post-hoc simulation shows
  no gain from pruning, but a dedicated retrain might find different
  hyperparameters). 2.5h compute.
- **Iter 191**: Cross-asset features for LINK/LTC/DOT (BTC 30d-return,
  funding rate).
