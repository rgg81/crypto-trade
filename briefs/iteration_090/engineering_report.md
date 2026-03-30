# Engineering Report: Iteration 090

**Date**: 2026-03-30
**Status**: EARLY STOP — Year 2022 PnL=-58.7%, WR=35.6%, 90 trades

## Implementation

### Changes from iter 089
1. **PurgedKFoldCV** (carried from iter 089): same purge_window=21, embargo_pct=0.02
2. **Disabled training_days** (NEW): Removed `training_days` from Optuna search space. Full 24-month window used for all folds.

### Deviations from Research Brief
- None.

## Results

### EARLY STOP Trigger
Year 2022 checkpoint: cumulative PnL=-58.7%, WR=35.6% (threshold: PnL>0, WR>33%)

### Comparison: Iter 090 vs Iter 089 vs Baseline

| Metric | Iter 090 | Iter 089 | Baseline (068) |
|--------|----------|----------|----------------|
| Sharpe | **-1.00** | -1.32 | +1.22 |
| WR | **35.2%** | 32.6% | 43.4% |
| PF | **0.79** | 0.72 | 1.35 |
| MaxDD | **82.0%** | 116.1% | 45.9% |
| Trades | 91 | 92 | 373 |
| Net PnL | **-60.0** | -81.3 | +264.3 |

### Improvement from disabling training_days
- IS Sharpe: -1.32 -> -1.00 (+24% less negative)
- WR: 32.6% -> 35.2% (+2.6pp)
- MaxDD: 116.1% -> 82.0% (-34pp)
- Net PnL: -81.3 -> -60.0 (+21 units less loss)

The training_days fix partially helps — the model is less catastrophic. But PurgedKFoldCV still produces a deeply unprofitable strategy. The core issue persists: when CV leakage is removed, the model cannot find profitable hyperparameters.

### CV Fold Analysis
No -10.0 penalty folds in the first training window (all folds have sufficient data). This confirms the training_days fix resolved the empty fold problem. Best Optuna Sharpe was 0.12 in seed 42 — much lower than baseline's typical 0.5+, confirming the leakage thesis.
