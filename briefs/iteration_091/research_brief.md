# Research Brief: 8H LightGBM Iteration 091

**Type**: EXPLORATION (TimeSeriesSplit gap — eliminate CV label leakage)
**Date**: 2026-03-30

## 0. Data Split & Backtest Approach

- OOS cutoff date: 2025-03-24 (project-level constant)
- Walk-forward backtest runs on FULL dataset (IS + OOS), monthly retraining
- Report layer splits at OOS_CUTOFF_DATE

## Core Hypothesis

**Eliminate CV label leakage by adding a gap to TimeSeriesSplit that excludes training samples whose labels could see into the validation period.**

Triple barrier labels with 7-day timeout scan forward up to 21 candles (10080min / 480min per 8h candle). Training samples within 21 candles of the fold boundary have labels that depend on validation-period prices. By setting `gap=22` (21 + 1 safety margin), TimeSeriesSplit automatically excludes these contaminated samples.

This is simpler than:
- PurgedKFoldCV (iter 089-090): required custom CV class + embargo, lost too much data
- Bounded labeling (iter 091 first attempt): required re-labeling per fold, complex caching

`TimeSeriesSplit(n_splits=5, gap=22)` achieves the same goal in one parameter.

## Data Loss Analysis

- Per fold boundary: 22 samples excluded
- 4 boundaries × 22 = 88 samples out of ~4,400 = **2.0% data loss**
- Compare: PurgedKFoldCV (iter 089) lost ~4% (purge + embargo)
- training_days remains in Optuna search space (no empty fold risk — gap is small)

## Implementation

Single line change in `optimization.py`:
```python
tscv = TimeSeriesSplit(n_splits=cv_splits, gap=22)
```

No new files, no new parameters, no re-labeling.

## Configuration

All identical to baseline iter 068 except:
- **CV gap**: 22 candles (NEW) — prevents label leakage
- Features: 115 (symbol-scoped, same as recent iterations)
- training_days: enabled (Optuna 10-500, same as baseline)
