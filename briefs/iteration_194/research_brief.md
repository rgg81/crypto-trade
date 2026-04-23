# Iteration 194 — Drop DOT from portfolio (rejected on concentration rule)

**Date**: 2026-04-23
**Type**: EXPLOITATION (configuration simplification driven by iter 193 finding)
**Baseline**: v0.186
**Decision**: NO-MERGE (but documented as a viable alternative)

## Motivation

Iter 193's bootstrap CI on v0.186 OOS showed:
- DOT standalone Sharpe: median +0.05, 95% CI [−1.91, +1.94], **P(Sharpe > 1.0) = 16%**
- DOT's signal is indistinguishable from zero in OOS.

Yet DOT contributes a visible 38% of reported per-symbol OOS PnL share.
Question: net of its contribution, is DOT a portfolio positive or a
diversification noise?

## Method

Post-hoc simulation on `reports/iteration_186/*.csv`. Remove all DOT
trades, recompute portfolio daily Sharpe + MaxDD + bootstrap CI.
Post-hoc is exact here because each model allocates its own capital
(no shared sizing pool); removing DOT doesn't change the other models'
trades.

## Result — OOS

| slice | trades | Sharpe | MaxDD | PnL | 95% CI |
|-------|-------:|-------:|------:|----:|:-------|
| Full v0.186 | 210 | **+1.737** | 29.31% | +104.11% | [−0.15, +3.44] |
| **Drop DOT** | 170 | **+1.869** | **27.89%** | +103.02% | [+0.06, +3.52] |
| Drop DOT+BTC | 127 | +1.908 | 25.64% | +97.26% | [+0.10, +3.52] |
| ALTs only | 118 | +1.387 | 23.10% | +67.05% | [−0.52, +3.02] |

## Result — IS

| slice | trades | Sharpe | MaxDD | PnL |
|-------|-------:|-------:|------:|----:|
| Full v0.186 | 594 | +1.440 | 56.70% | +297.99% |
| Drop DOT | 502 | +1.349 | 46.55% | +255.92% |

Drop-DOT IS Sharpe: −0.091 vs. baseline (small regression).

## Drop-DOT per-symbol concentration (OOS)

| symbol | weighted_pnl | % of total |
|--------|-------------:|-----------:|
| LINK | +49.19% | **47.7%** |
| ETH | +31.30% | 30.4% |
| LTC | +16.77% | 16.3% |
| BTC | +5.76% | 5.6% |

**LINK concentration jumps from 37.3% (v0.186) to 47.7%.** ETH rises to
30.4%. Both symbols now violate the 30% single-symbol rule.

## Merge criteria check

| rule | threshold | drop-DOT | pass? |
|------|-----------|---------:|:-----:|
| IS Sharpe > 1.0 | 1.0 | +1.349 | ✓ |
| OOS Sharpe > 1.0 | 1.0 | +1.869 | ✓ |
| OOS Sharpe > baseline | +1.737 | +1.869 | ✓ |
| OOS MaxDD ≤ baseline × 1.2 | ≤ 35.17% | 27.89% | ✓ |
| OOS trades/month ≥ 10 | ≥ 130 | 170 | ✓ |
| OOS PF > 1.0 | 1.0 | 2.98 (est.) | ✓ |
| OOS/IS Sharpe > 0.5 | 0.5 | 1.39 | ✓ |
| **No single symbol > 30% OOS PnL** | 30% | **LINK 47.7%, ETH 30.4%** | **FAIL** |

The concentration rule is a hard constraint, and drop-DOT is strictly
**worse** on concentration than v0.186 (which had max-symbol at 38.25%).
The diversification-exception clause does not apply (that's for
additions, and only when concentration *improves*).

## Why this is genuinely ambiguous

1. **Sharpe and MaxDD both improve** meaningfully (+0.13 OOS Sharpe,
   −1.4 pp OOS MaxDD). Normally a clear MERGE signal.
2. **The weaker model (DOT) is genuinely noise**. Bootstrap showed its
   signal is indistinguishable from zero. Keeping it adds operational
   complexity (R1+R2 tuning) for no OOS benefit.
3. **But** portfolio concentration goes up because removing the weak
   contributor means the strong ones represent a larger share.
4. The rule "no symbol > 30%" assumes the kept symbols are
   genuinely independent. LINK is already concentrated; making it more
   so is a live-deployment risk (a LINK-specific regime shift hurts
   the whole portfolio).

## Decision

NO-MERGE under the strict concentration rule. The finding is documented
as a viable alternative baseline (call it "v0.186-lean") that the user
may choose to deploy if they judge LINK concentration acceptable.

**Recommendation**: before shipping either, consider whether v0.186 vs
v0.186-lean is a better live bet. Trade-off:

| aspect | v0.186 (keep DOT) | v0.186-lean (drop DOT) |
|--------|------------------:|-----------------------:|
| OOS Sharpe | +1.74 | +1.87 |
| OOS MaxDD | 29.3% | 27.9% |
| Max single-symbol | DOT 38% | LINK 48% |
| Num models | 5 (A, C, D, E) | 4 (A, C, D) |
| Operational complexity | R1+R2 on E | R1 on C, D only |

## Exploration/Exploitation Tracker

Window (184-194): [X, X, X, X, X, E, E, E, E, V, **X**] — 4E/6X,
plus one validation iteration.

## Next Iteration Ideas

- **Iter 195**: AFML fractional differentiation features — try BTC at
  d=0.4, d=0.6. True new direction.
- **Iter 196**: Direct live deployment of v0.186 (as is, with DOT) to
  paper-trading for 2 weeks. Collect live data as input for future
  decisions about DOT inclusion.
- **Iter 197**: If paper-trading shows DOT actively hurting the
  portfolio, revisit drop-DOT as a concrete MERGE candidate under
  a "live data justifies exception" argument.
