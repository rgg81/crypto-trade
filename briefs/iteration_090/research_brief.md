# Research Brief: 8H LightGBM Iteration 090

**Type**: EXPLOITATION (fix PurgedKFoldCV integration from iter 089)
**Date**: 2026-03-30

## 0. Data Split & Backtest Approach

- OOS cutoff date: 2025-03-24 (project-level constant, applies to all iterations)
- The researcher used ONLY IS data (before 2025-03-24) for all design decisions below
- The walk-forward backtest runs on the FULL dataset (IS + OOS) as one continuous process
- Monthly retraining with PurgedKFoldCV, 24-month training window
- The report layer splits backtest results at OOS_CUTOFF_DATE into two report batches

## Core Hypothesis

**Iter 089 failed because training_days optimization + PurgedKFoldCV creates empty folds. Fix by disabling training_days (use full 24-month window) while keeping PurgedKFoldCV.**

In iter 089, the combination of:
1. PurgedKFoldCV removing ~109 samples at boundaries (purge + embargo)
2. `training_days` parameter trimming training data from the beginning (Optuna range 10-500 days)
3. High confidence thresholds filtering most predictions

...caused many CV folds to have insufficient data, producing -10.0 penalty scores. This destabilized Optuna optimization entirely.

The fix: remove `training_days` from the Optuna search space. The full 24-month training window provides ~4,400 samples per fold. After purging (21 samples) and embargo (88 samples), each fold still has ~4,200 training samples — more than enough.

## Two Changes from Baseline

1. **PurgedKFoldCV** (from iter 089): purge_window=21, embargo_pct=0.02
2. **Disable training_days** (NEW): Use full 24-month window, no Optuna trimming

This violates the "one variable at a time" rule, but the second change is a bugfix for the first — training_days was always an optimization convenience, not a core strategy parameter.

## 1-8. Configuration

All configuration identical to iter 089 research brief, with one change:
- **training_days**: REMOVED from Optuna search space (was 10-500). Fixed at full window.
- Everything else: same as baseline iter 068 + PurgedKFoldCV from iter 089.
