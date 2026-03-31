# Iteration 095 — Engineering Report

**EARLY STOP**: Year 2022 PnL=-57.6%, WR=34.9%, 106 trades.

## Configuration

Same as iter 093 except:
- Features: 185 → 145 (removed 37 near-perfect duplicates |r|≥0.99 + 3 harmful MDA<-0.01)
- Bug fix: Sharpe overflow guard (|Sharpe|>100 → -10.0) in compute_sharpe_with_threshold

## Results (EARLY STOP)

| Metric | Iter 095 | Iter 094 | Baseline (093) |
|--------|----------|----------|----------------|
| IS Sharpe | **-0.83** | -1.46 | +0.73 |
| IS WR | 34.6% | 31.3% | 42.8% |
| IS PF | 0.82 | 0.71 | 1.19 |
| IS MaxDD | 123.5% | 150.5% | 92.9% |
| IS Trades | 107 (partial) | 115 (partial) | 346 |

Better than iter 094's 50 features but still far below baseline.

## Label Leakage Audit

- CV gap: 44 rows, verified on all folds (176-184h > 168h timeout)
- No leakage detected

## Sharpe Overflow Fix Verified

The fix works. In the last month's seed 1001 training, trial 11 hit the old overflow condition (Sharpe computed as -6.04 after guard → would have been huge positive). Trial 13 similarly capped. Optuna correctly selected trial 24 (Sharpe=0.087) instead of the degenerate trial.

## Root Cause

Even conservative pruning (removing only |r|≥0.99 duplicates) degrades performance. The issue is NOT the specific features removed — it's that **any change to the feature set changes Optuna's hyperparameter optimization landscape**, leading to different (worse) hyperparameters for each monthly model.

The baseline's 185 features were what Optuna was optimized against. Removing 40 features changes the effective search space for colsample_bytree, causing different tree structures and different confidence thresholds.
