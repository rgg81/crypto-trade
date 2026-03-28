# Research Brief: 8H LightGBM Iteration 075

**Type**: EXPLOITATION (baseline reproduction — corrective)

## 0. Data Split & Backtest Approach
- OOS cutoff date: 2025-03-24
- Walk-forward on full dataset, monthly retraining, 24mo window

## Motivation

Iter 074 revealed the root cause of all failures since iter 068: the "symbol-filtered discovery fix" from iter 073 increased features from 106→185, destroying the signal.

The baseline's 106 features came from the GLOBAL intersection across all 760 parquet files. This implicit feature selection kept only features present in ALL symbols — an effective pruning mechanism. The "fix" that restricted discovery to only BTC/ETH parquets removed this pruning, exposing the model to 79 additional features that it can't handle.

## What Changed

**REVERT the symbol-filtered discovery.** Restore the original `_discover_feature_columns()` behavior that scans all 760 parquet files and returns the 106-feature global intersection.

## Configuration

IDENTICAL to iter 068. No changes except restoring original discovery behavior.
