# Research Brief: 8H LightGBM Iteration 036 — EXPLOITATION

## 0. Data Split: OOS cutoff 2025-03-24. Full data range.

## 1. Change: Symbol-scoped feature discovery (bug fix) with baseline config

### The Fix
_discover_feature_columns() was scanning ALL 760 parquet files (intersection), dropping features missing from ANY symbol. With BTC+ETH only, the intersection should be BTC∩ETH = 185 features. But the old code intersected across all 760 → only 106 survived.

The fix (from iter 033): scan only the symbols in the backtest config. Now BTC+ETH gets 185 features instead of 106.

### Why This Matters
The baseline (iter 016) ran with 106 features. This iteration tests the SAME config (BTC+ETH, 4%/2%, 0.85 threshold) but with 185 features. The model has access to 79 additional features it never saw before.

Parquets regenerated WITHOUT macro features — just the original 7 groups.

## 2. Everything Else: Exact iter 016 config.
