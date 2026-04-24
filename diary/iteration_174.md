# Iteration 174 Diary

**Date**: 2026-04-22
**Type**: EXPLORATION (DOT against v0.173 baseline)
**Decision**: **NO-MERGE** (concentration + MaxDD regression blocks it, but DOT is close)

## Headline

A+C(R1)+LTC(R1)+DOT(R1 K=3 C=18) gives OOS Sharpe **+1.432** vs v0.173's +1.387. LINK concentration drops from 83.1% to 66.8%. OOS PnL jumps from +78.65% to +97.85%. But OOS MaxDD regresses from 27.74% to 28.19% and concentration still exceeds 30%, so the diversification exception doesn't apply.

## Why this is the right call even though Sharpe improves

Under the strict merge rules, OOS Sharpe improvement alone is not sufficient. The concentration constraint is a hard rule, and the diversification exception specifically requires MaxDD to improve — otherwise we'd be paying drawdown risk for a modest return uplift. The 0.45 pp MaxDD regression is tiny, but the rule is explicit, and we don't dilute it.

The meta-finding: DOT's OOS is strong but its IS has catastrophic drawdowns in 2022 that amplify Model A's concurrent drawdowns. The problem is correlated drawdown, and R1 doesn't address correlation — R1 is per-symbol. We need a portfolio-level mitigation.

## What needs to change for DOT to merge

Either (a) DOT's IS 2022 losses need to be further mitigated (R3 OOD detection might help if 2022 candles have out-of-distribution feature values), or (b) portfolio-level R2 scales positions down during collective drawdowns, or (c) another candidate is added simultaneously to reduce concentration below 30% and bank the diversification benefit regardless of MaxDD.

Option (b) is the cheapest and most directly relevant. Iter 175 implements R2.

## Research Checklist

- **E (trade pattern)**: executed via the pooled portfolio analysis with various R1 variants on DOT.
- **R1 (consecutive-SL cool-down)**: applied comprehensively with 5 variants tested.

## Exploration/Exploitation Tracker

Window (165-174): [X, E, E, E, E, X, E, E, X, E] → 7E/3X. Iter 174 tagged E. Iter 175 will be X (implementation iteration).

## Next Iteration Ideas

### 1. Iter 175 (EXPLOITATION, PRIORITY) — Implement R2 in the backtest engine

Drawdown-triggered position scaling. `BacktestConfig`:

```python
risk_drawdown_scale_enabled: bool = False
risk_drawdown_lookback_days: int = 30
risk_drawdown_trigger_pct: float = 10.0
risk_drawdown_scale_floor: float = 0.33
```

Logic: track rolling 30-day weighted-PnL drawdown from peak. When drawdown exceeds the trigger (e.g., 10%), scale new trades' `weight_factor` by `max(floor, 1 - drawdown_pct / 60%)`. This uniformly de-risks during bad periods.

Calibration: run the IS analysis on v0.173 baseline drawdowns and identify trigger/floor values that (a) fire during the 2022 correlated drawdown, (b) don't fire spuriously in healthy periods.

### 2. Iter 176 — Retry DOT addition with R1+R2

If R2 tames the pooled MaxDD, A+C(R1)+LTC(R1)+DOT(R1,R2) may pass all constraints including the diversification exception.

### 3. Iter 177 — R3 (OOD detector) and/or portfolio concentration soft-cap R5

These are further mitigations. Skipping in favour of R2 first because R2 directly targets the MaxDD regression that's blocking iter 174.

## lgbm.py Code Review

No changes needed. The R1 infrastructure from iter 173 is clean.
