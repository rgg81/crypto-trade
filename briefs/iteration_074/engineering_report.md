# Engineering Report: Iteration 074

## Implementation

1. Applied symbol-filtered discovery fix from iter 073 — `_discover_feature_columns()` now passes trading symbols from master DataFrame
2. Exact iter 068 config, no whitelist — model discovers all 187 features from BTC/ETH parquets
3. Runner matches baseline parameters exactly

## Backtest Results

- **EARLY STOP**: Year 2022 PnL -63.9% (WR 34.3%, 99 trades)
- IS Sharpe: **-0.86** (baseline: +1.22)
- IS MaxDD: **122.1%** (baseline: 45.9%)
- IS WR: 35.0% (baseline: 43.4%)
- IS PF: 0.80 (baseline: 1.35)
- IS Trades: 100 (baseline: 373)
- OOS: not reached

## Critical Finding: Parquet Contamination

**The feature parquet was corrupted by code from failed iterations committed to main.**

The baseline (iter 068) ran with 106 features and produced IS Sharpe +1.22. The current parquet has 187 features because:
1. Iter 070 (NO-MERGE) added interaction features + `feat(iter-070)` was committed to main
2. Iter 072 (NO-MERGE) added calendar features + `feat(iter-072)` was committed to main
3. The feature generation ran with these extra groups, regenerating parquets with 187 features

With 187 features:
- Optuna best Sharpe per month dropped from 0.4-0.5 (with 106) to 0.02-0.09 (with 187)
- The 81 extra features (interaction, calendar, etc.) are noise — proven to hurt by iters 070 and 072
- LightGBM wastes optimization budget exploring noisy features

**To restore baseline performance**, the parquet must be regenerated with only the original 6 feature groups (momentum, volatility, trend, volume, mean_reversion, statistical), excluding interaction and calendar groups.

## Runtime

~1431s (24 min) — longer than usual due to 187 features per training round
