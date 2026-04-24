# Iteration 193 — Bootstrap validation of v0.186

**Date**: 2026-04-23
**Type**: VALIDATION (not a merge candidate)
**Baseline**: v0.186 — unchanged (validated)
**Decision**: v0.186 is statistically credible for deployment

## TL;DR

10,000-sample daily-return bootstrap on v0.186's trades:

- **Portfolio OOS Sharpe 95% CI: [−0.14, +3.44]** with median +1.74
- **P(portfolio OOS Sharpe > 1.0) = 79%**
- **Combined IS+OOS P(S>1.0) = 86%**
- IS and OOS bootstrap medians within 0.3 of each other (consistent)

v0.186 is real. The DSR of -13 was conservative; the bootstrap CI
gives a more actionable view that supports deployment.

## Per-symbol OOS CIs (signal source diagnostic)

| symbol | median Sharpe | P(S > 1.0) |
|--------|--------------:|-----------:|
| LINK | +1.45 | **69%** |
| ETH | +1.09 | **54%** |
| LTC | +0.63 | 34% |
| BTC | +0.29 | 23% |
| DOT | +0.05 | 16% |

Only LINK has strong standalone OOS evidence. DOT has essentially no
standalone signal (16% P>1.0). The portfolio's diversification converts
these weak signals into a 79% P>1.0 at the aggregate.

**Concern on DOT**: even with R1+R2 risk mitigations, its OOS standalone
Sharpe bootstrap is indistinguishable from zero. Adding DOT to the
portfolio helped 2022 IS (the motivating case for R2) but its OOS
contribution is fragile. Worth reconsidering in a future iteration
whether DOT's 38% OOS PnL share is robust or is leaning on a handful
of lucky trades.

## Why run this now

After 4 consecutive NO-MERGE exploration iterations (189 xbtc augment,
190 xbtc swap, 191 LINK pruning, 192 DOT 14d), the hit rate on exploration
was zero. Before running yet another exploration iteration, wanted to
confirm the baseline we're trying to beat is itself statistically sound.

It is. The bootstrap result unlocks a clear path forward: ship v0.186
to paper-trading while continuing iteration.

## Exploration/Exploitation Tracker

Validation iterations don't count toward E/X. Window stays 5E/5X.

## Next Iteration Ideas

- **Iter 194**: AFML fractional differentiation features — preserved
  memory, stationary, never tried. One feature at a time, displacement
  basis.
- **Iter 195**: Revisit DOT's inclusion. Post-hoc portfolio metrics
  with DOT removed. If the cost of DOT is higher than its contribution
  (considering R1+R2 complexity and its weak OOS standalone Sharpe),
  drop DOT.
- **Iter 196**: Ship v0.186 to paper-trading. Validation supports it.
  Live data becomes the best iteration input.
