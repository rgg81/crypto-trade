# Iteration 174 Research Brief

**Date**: 2026-04-22
**Role**: QR
**Type**: **EXPLORATION** (re-attempt DOT addition against new v0.173 baseline)
**Previous iteration**: 173 (MERGE — R1 on LINK+LTC)
**Baseline**: v0.173 (A+C(R1)+LTC(R1), OOS +1.39, IS +1.30, MaxDD 27.74%)

## Section 0 — Data Split (verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

## Motivation

With v0.173's R1 reducing pooled MaxDD from 30.56% to 27.74%, iter 174 tests whether DOT (with R1) can now clear the diversification-exception MaxDD requirement. Iter 172's DOT(R1) with the old baseline gave OOS +1.29 (marginal) but failed MaxDD.

## Research Analysis (IS evidence)

`analysis/iteration_174/add_dot_to_v173.py`:

| Variant                     | IS Sharpe | IS MaxDD | OOS Sharpe | OOS MaxDD | OOS PnL   | LINK%  |
|-----------------------------|----------:|---------:|-----------:|----------:|----------:|-------:|
| v0.173 baseline (no DOT)    | +1.297    | 45.57%   | +1.387     | **27.74%**| +78.65%   | 83.1%  |
| + DOT no R1                 | +1.102    | 79.09%   | +1.429     | 32.93%    | +98.05%   | 66.6%  |
| + DOT R1 K=2 C=18           | +1.233    | 62.23%   | +1.410     | 30.33%    | +94.13%   | 69.4%  |
| + **DOT R1 K=3 C=18**       | +1.176    | 71.47%   | **+1.432** | 28.19%    | +97.85%   | 66.8%  |
| + DOT R1 K=3 C=27           | +1.284    | 60.92%   | +1.379     | 31.95%    | +94.10%   | 69.4%  |
| + DOT R1 K=3 C=36           | +1.282    | 60.92%   | +1.331     | 31.95%    | +90.77%   | 72.0%  |

### Findings

1. **DOT K=3 C=18 gives the best OOS Sharpe** (+1.43) — +0.045 over the v0.173 baseline. OOS PnL jumps from +78.65% to +97.85% (+24% relative).
2. **LINK concentration drops from 83.1% to 66.8%** — the highest single reduction we've seen, entirely from DOT's 17-20% OOS contribution.
3. **Pooled OOS MaxDD** regresses from 27.74% to 28.19% (+0.45 pp) — a near-wash in absolute terms but still technically WORSE, not improved. Fails the diversification-exception "MaxDD improves by > 10%" clause.
4. **IS MaxDD REGRESSES materially** (45.57% → 71.47%). This is because DOT's IS draws down heavily in 2022 and that drawdown amplifies Model A's 2022 DD, compounding.
5. All floors (IS > 1.0, OOS > 1.0) hold.

## Merge decision: NO-MERGE (strict rules)

| Check | Threshold | iter-174 best (DOT R1 K=3 C=18) | Pass |
|-------|-----------|---------------------------------|:----:|
| IS Sharpe floor | > 1.0 | +1.18 | ✓ |
| OOS Sharpe floor | > 1.0 | +1.43 | ✓ |
| OOS > baseline | > +1.39 | +1.43 | ✓ |
| OOS MaxDD ≤ 1.2× baseline | ≤ 33.29% | 28.19% | ✓ |
| Min 50 OOS trades | ≥ 50 | ~256 | ✓ |
| OOS PF > 1.0 | > 1.0 | ~1.3 | ✓ |
| Single symbol ≤ 30% OOS PnL | ≤ 30% | LINK 66.8% | ✗ |
| IS/OOS Sharpe ratio > 0.5 | > 0.5 | 0.82 | ✓ |

Concentration still fails. Diversification exception requires MaxDD to *improve* by > 10%; here it regresses by 0.45 pp. So the exception doesn't apply.

NO-MERGE under strict rules.

## What would unlock this merge

DOT adds value (OOS Sharpe and PnL) and meaningfully reduces LINK concentration, but brings correlated-drawdown risk that our current risk mitigations don't address. **R2 (drawdown-triggered position scaling)** is designed for exactly this: when pooled drawdown exceeds X%, scale new trades by F < 1 across all symbols. This would reduce the compounding when multiple models hit simultaneous losses.

Iter 175 = design + implement R2. Then iter 176 = retry DOT addition with both R1 and R2 active.

## Exploration/Exploitation Tracker

Window (165-174): [X, E, E, E, E, X, E, E, X, E] → 7E/3X. Iter 174 as E. Balanced.

## Commit discipline

Since this is NO-MERGE:
- Research brief → `docs(iter-174): research brief`
- Engineering report → `docs(iter-174): engineering report`
- Diary → `docs(iter-174): diary entry`
