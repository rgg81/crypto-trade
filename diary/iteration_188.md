# Iteration 188 — R1 on Model A (rejected, IS Sharpe always falls)

**Date**: 2026-04-22
**Type**: EXPLOITATION
**Baseline**: v0.186 — unchanged
**Decision**: NO-MERGE

## TL;DR

Post-hoc per-symbol R1 (consecutive-SL cooldown) on Model A trades: every
K/C combo trades IS Sharpe for OOS Sharpe. Best IS-calibrated choice
(K=2/C=9) gives +0.029 IS and +0.045 OOS — within noise. Best OOS result
(K=2/C=36) costs −0.092 IS Sharpe, which is the classic sign of
OOS-overfit. Model A keeps R1 disabled.

## Data

With R3 already active on all models, the Mahalanobis filter is doing the
regime-break defence. R1 on Model A adds a second filter that also blocks
trades during SL streaks. Problem: Model A shows *mean-reverting* WR at
long streaks (from iter 173 EDA); the next trade after 3+ BTC/ETH SLs is
disproportionately a TP, which R1 would block.

Result of per-symbol sweep (BTC and ETH streaks tracked separately, matching
`backtest.py`):

| K | C | IS Sharpe | OOS Sharpe | OOS MaxDD |
|--:|--:|----------:|-----------:|----------:|
| baseline | — | +1.440 | +1.737 | 29.31% |
| 2 | 9  | **+1.469** | +1.782 | 29.31% |
| 2 | 27 | +1.402 | +1.812 | 22.84% |
| 2 | 36 | +1.348 | **+1.898** | 22.84% |
| 3 | 27 | +1.372 | +1.768 | 29.09% |
| 4 | 27 | +1.377 | +1.743 | 28.40% |

IS Sharpe falls monotonically with cooldown length. The only IS-improving
choice (K=2/C=9) gives a tiny OOS gain. The biggest OOS gain (K=2/C=36)
costs 6% of IS Sharpe — overfit.

## Why R1 helps altcoins but not the BTC/ETH pool

LINK/LTC/DOT standalone models develop clustered SL streaks during regime
shifts (DOT's 2022 bleed was the motivating case). R1 truncates the
cluster.

Model A is pooled BTC+ETH. Pooled-model WR at streak-length ≥ 3 is actually
*higher* than at streak 0 — mean reversion. Blocking trades during the
streak forfeits mean-reversion profit. This was the original reason we
kept R1 off Model A in v0.173; the finding survives the v0.186 R3 filter.

## Decision

NO-MERGE. The risk-mitigation stack is at its sweet spot for v0.186: R1
on altcoins, R2 on DOT, R3 everywhere. Model A's alpha is mean-reverting
in streak space; any blanket streak filter costs more than it saves.

## Exploration/Exploitation Tracker

Window (178-188): [E, E, X, E, X, E, X, X, X, X, **X**] → **4E/7X**.

## Next Iteration Ideas

- **Iter 189**: Per-symbol OOD cutoffs. BTC OOS WR is 32.6%, LINK is 50.0%.
  Tighter cutoff for BTC, looser for LINK may recover lost alpha. Post-hoc.
- **Iter 190**: Cross-asset features for altcoins (BTC 30d return, realized
  vol, funding rate). Full backtest (~5h).
- **Iter 191**: ETH-only Model A retrain.
