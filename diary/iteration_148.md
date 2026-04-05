# Iteration 148 Diary

**Date**: 2026-04-05
**Type**: EXPLORATION (DOGE + per-symbol VT — final attempt)
**Decision**: **NO-MERGE** — 3rd DOGE addition attempt fails

## Results

| Metric | Baseline (iter 147) | Iter 148 | Change |
|--------|---------------------|----------|--------|
| OOS Sharpe | +2.65 | +2.42 | -9% |
| OOS MaxDD | 39.2% | 69.0% | +76% |
| OOS PF | 1.62 | 1.56 | -4% |
| OOS Trades | 164 | 214 | +30% |

## Analysis

### DOGE is definitively rejected after 3 attempts

| Attempt | Sharpe | MaxDD | Result |
|---------|--------|-------|--------|
| iter 143 (no sizing) | +2.30 | 92.5% | FAIL |
| iter 146 (portfolio VT) | +2.10 | 48.5% | FAIL |
| iter 148 (per-symbol VT) | +2.42 | 69.0% | FAIL |

DOGE's trades are temporally correlated with A+C+D drawdowns. Position sizing,
whether portfolio-wide or per-symbol, cannot overcome this fundamental correlation.

### Why per-symbol VT fails the portfolio test

Per-symbol VT scales DOGE trades only by DOGE's own realized vol. When DOGE
appears calm in isolation but ALL portfolio models lose together (July 2025
cross-asset crash), per-symbol scaling preserves too much DOGE exposure.

This makes per-symbol VT WORSE than portfolio-wide VT for multi-model portfolios
with correlated drawdowns. Paradoxically:
- Per-symbol VT is better for A+C+D (iter 147 beats iter 145)
- Portfolio VT is better for A+C+D+DOGE (iter 146 beats iter 148)

### DOGE is a standalone asset, not a portfolio addition

DOGE's strong standalone Sharpe (+1.24 in iter 142) means it would be profitable
as an INDEPENDENT strategy. But within a portfolio of A+C+D, its drawdowns
amplify the aggregate without proportional return benefit.

## Hard Constraints

| Constraint | Threshold | Iter 148 | Pass? |
|------------|-----------|----------|-------|
| OOS Sharpe > baseline | > +2.65 | +2.42 | **FAIL** |
| OOS MaxDD ≤ 47% | ≤ 47% | 69.0% | **FAIL** |

## Research Checklist

- **B (Symbol Universe)**: Confirms DOGE's structural incompatibility with A+C+D.
- **E (Trade Pattern)**: Per-symbol vs portfolio VT reveals sizing-rule tradeoffs.

## Exploration/Exploitation Tracker

Last 10 iterations: [X, E, X, E, E, E, E, X, E, **E**] (iters 139-148)
Exploration rate: 7/10 = 70% ✓

## Next Iteration Ideas

1. **Accept v0.147 as FINAL baseline** — 148 iterations, OOS Sharpe +2.65, Calmar
   4.02. The A+C+D portfolio with per-symbol VT is very strong. Further gains
   require structural changes (new feature categories, regime models, etc.).

2. **Implement per-symbol VT in backtest.py** (EXPLOITATION, code change) — To
   make iter 147 production-ready, the vol targeting rule must be in the backtest
   engine, not applied post-hoc.

3. **Hybrid VT: portfolio × per-symbol** (EXPLORATION) — Scale by geometric mean
   of both signals. Might catch both per-symbol noise AND cross-asset co-movement.

4. **Test different IS-tuned configs for robustness** (EXPLOITATION) — Run A+C+D
   with 2nd and 3rd best IS configs to verify iter 147 isn't IS-overfit.
