# Iteration 194 — Drop DOT? (rejected on concentration rule, documented alternative)

**Date**: 2026-04-23
**Type**: EXPLOITATION
**Baseline**: v0.186 — unchanged
**Decision**: NO-MERGE (strict concentration rule), but drop-DOT is a
viable alternative deployment.

## TL;DR

Dropping DOT improves OOS Sharpe (+1.74 → +1.87) and MaxDD (29.31% →
27.89%), at cost of LINK concentration rising to **47.7%** (from 37.3%).
Strict 30% concentration rule fails, so NO-MERGE. But the Sharpe/MaxDD
case for drop-DOT is strong enough to document as an alternative baseline.

## The numbers

OOS:

| slice | Sharpe | MaxDD | Trades | Top symbol |
|-------|-------:|------:|-------:|-----------:|
| v0.186 (keep DOT) | +1.737 | 29.31% | 210 | DOT 38% |
| **v0.186-lean (drop DOT)** | **+1.869** | **27.89%** | 170 | **LINK 48%** |

IS:

| slice | Sharpe |
|-------|-------:|
| v0.186 | +1.440 |
| v0.186-lean | +1.349 (−0.09) |

## Why ambiguous

DOT's **standalone OOS Sharpe CI is [−1.9, +1.9] with median +0.05**.
Its signal is indistinguishable from zero. Keeping it requires R1+R2
risk mitigations that have no upside except preventing a 2022-style
IS blow-up that OOS doesn't reward.

But removing it concentrates the portfolio on LINK to 48%. If LINK
enters a regime-shift drawdown in live, the whole portfolio bleeds.

## Decision logic

The skill's 30% concentration rule is a hard constraint, and
"diversification exception" doesn't apply to removals (it's specifically
for symbol additions that reduce concentration). Drop-DOT makes
concentration strictly worse in absolute terms.

**NO-MERGE** as v0.194. v0.186 stays.

## What's documented for future decisions

v0.186-lean exists as a viable alternative deployment. The tradeoff is
explicit:
- v0.186: Better diversification (no symbol > 38%), more operational
  complexity (5 models with R1+R2), marginally worse Sharpe/MaxDD.
- v0.186-lean: Better Sharpe/MaxDD, simpler (4 models, only R1), but
  LINK concentration at 48% is a live-deployment risk.

The right call depends on live-deployment conviction — data we don't
yet have.

## Exploration/Exploitation Tracker

Window (184-194): [X, X, X, X, X, E, E, E, E, V, **X**] → **4E/6X** +
1 validation. Slightly exploitation-heavy.

## Next Iteration Ideas

- **Iter 195**: AFML fractional differentiation — real new-direction
  exploration. Frac-diff features on BTC close at d=0.4, 0.6.
- **Iter 196**: Ship v0.186 (NOT v0.186-lean) to paper-trading. The
  more-diversified portfolio is safer for first live deployment.
  Collect 2-4 weeks of live data.
- **Iter 197**: Live data-driven decisions. Revisit drop-DOT *if*
  paper-trading confirms DOT's signal is genuinely absent. Live data
  beats backtest-derived inference.
