# Iteration 066 — Engineering Report

## Change

Increased Optuna trials from 50 to 100 (`n_trials=100`). No code changes to lgbm.py — only the run script parameter.

## Results

### Seed 42

| Metric | Iter 066 | Baseline (063) |
|--------|----------|---------------|
| IS Sharpe | **+1.55** | +1.48 |
| IS MaxDD | **51.4%** | 74.9% |
| OOS Sharpe | +1.72 | **+1.95** |
| OOS MaxDD | 30.6% | **18.4%** |
| OOS Trades | 114 | 100 |

### Seed 123

| Metric | Iter 066 | Baseline (063) |
|--------|----------|---------------|
| IS Sharpe | **+1.23** | +1.00 |
| IS MaxDD | **51.9%** | N/A |
| OOS Sharpe | -0.22 | **+0.70** |
| OOS PF | 0.95 | 1.18 |

### Analysis

100 trials improves IS metrics (higher Sharpe, lower MaxDD) but degrades OOS. This is classic optimization overfitting — with more trials, Optuna finds hyperparameters that fit the training CV folds better, but this doesn't generalize to OOS.

Runtime: 2391s (~40min) with 100 trials vs ~20min with 50. Double as expected.

## Trade Verification

Spot-checked 10 trades from seed 42. Execution correct. Dynamic ATR barriers applied properly.
