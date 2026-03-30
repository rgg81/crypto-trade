# Engineering Report: Iteration 091

**Date**: 2026-03-31
**Status**: Full walk-forward completed (no early stop)

## Implementation

Single line change in `optimization.py`: `TimeSeriesSplit(n_splits=cv_splits, gap=cv_gap)` where `cv_gap = (timeout_candles + 1) * n_symbols` computed dynamically in `lgbm.py._train_for_month()`.

For 8h candles, 7-day timeout, 2 symbols: gap = (10080/480 + 1) * 2 = **44 rows**.

## Results

| Metric | Iter 091 | Baseline (068) |
|--------|----------|----------------|
| IS Sharpe | +0.54 | +1.22 |
| IS WR | 42.6% | 43.4% |
| IS PF | 1.14 | 1.35 |
| IS MaxDD | 78.8% | 45.9% |
| IS Trades | 352 | 373 |
| OOS Sharpe | **+0.89** | +1.84 |
| OOS WR | 40.6% | 44.8% |
| OOS PF | 1.25 | 1.62 |
| OOS MaxDD | **30.5%** | 42.6% |
| OOS Trades | 96 | 87 |
| OOS/IS Ratio | 1.63 | 1.50 |

## Confounding Variable

Feature count: 115 (current symbol-scoped discovery) vs baseline's 106. This iteration does NOT perfectly replicate baseline — the 9 extra features may contribute to the differences. Iter 092 should fix this.

## Label Leakage Audit

- TimeSeriesSplit gap = 44 rows (22 candles × 2 symbols): VERIFIED
- No -10.0 fold penalties from empty folds: CONFIRMED
- training_days parameter still active in Optuna: CONFIRMED
- Walk-forward trains only on past klines: VERIFIED
