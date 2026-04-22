# Iteration 183 — Engineering Report

**Date**: 2026-04-22
**Runner**: `run_iteration_183_xlm.py`
**Symbol**: XLMUSDT, standalone
**Feature columns**: `BASELINE_FEATURE_COLUMNS` (193 features)
**Ensemble seeds**: [42, 123, 456, 789, 1001]
**Risk mitigations**: R1 (K=3, C=27), R2 (t=7%, a=15%, f=0.33)
**Early stop**: year-1 / year-2 cumulative PnL check active

## Result

`*** EARLY STOP (1099s) *** Year 1 (2022): PnL=-4.5% (WR=38.2%, 55 trades)`

| Metric | IS (year 1 only) |
|---|---:|
| Sharpe | +0.045 |
| WR | 37.5% |
| PF | 1.019 |
| MaxDD | 18.81% |
| Trades | 56 |
| DSR | −65.98 |

Per the skill, year-1 fail-fast triggered (year-1 PnL < 0 with ≥ 10 trades).

## What R1+R2 bought us

XLM underlying in 2022 returned **−73.3%** with a peak-to-trough drawdown of **−75.7%**.
The strategy with R1+R2 contained the portfolio drawdown to **−18.81%** and limited
trading PnL to **−4.5%** over 55 trades. That is risk mitigation working as designed;
the model avoided the blow-ups ATOM/AAVE suffered in the same window.

## What R1+R2 could NOT fix

The signal itself is not strong enough:
- WR 37.5% is barely above the 33.3% break-even for a 2:1 RR (8% TP, 4% SL)
- IS Sharpe **+0.045** — indistinguishable from noise
- DSR −65.98 — deeply negative deflated Sharpe, i.e., overwhelmingly likely to be
  overfit to the ≤100-trial Optuna search given 55 trades

R1+R2 are damage-control, not alpha-generation. A model with no edge still has no edge.

## Test Suite

No code changes in this iteration — runner only. Existing tests untouched.
