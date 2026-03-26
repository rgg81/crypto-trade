# Engineering Report: Iteration 008

## Changes

1. **Fixed `_discover_feature_columns()`**: intersection → union. Now 189 features (from 106).
2. **Added BTC cross-asset features**: `_load_btc_cross_features()`, `_inject_btc_features()`. Adds btc_return_1, btc_return_3, btc_natr_14, btc_rsi_14.
3. **Updated test month loading**: Handles mixed parquet + injected features.

## Trade Execution Verification

Sampled 10 OOS trades: entry prices match, SL/TP calculations correct, PnL math verified. No anomalies.

## Results

- 189 features (from 106), 57,527 trades, 8,367 OOS
- OOS Sharpe: -3.96 (worse than -1.91)
- WR: 31.2% (worse than 32.9%)
- Runtime: ~10,000s
