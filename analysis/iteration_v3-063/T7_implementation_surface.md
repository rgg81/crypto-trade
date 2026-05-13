# T7 — Implementation Surface Estimate

## NEW features required (22 total)

Compute status breakdown:
- easy (≤15 LOC each): 20
- medium (>15 LOC): 2
- hard: 0

## Estimated LOC

- ~10 LOC × 20 easy = ~200
- ~30 LOC × 2 medium = ~60
- Total new code: ~260 LOC

## New files

- 1 new module: `features_v3/technical_v3.py` (RSI, stochastic, MACD, CCI, Williams, ADX, BB %B)
- 1 new module: `features_v3/calendar_v3.py` (hour/dow cyclic encodings)
- 1 module to extend: `features_v3/engineered_v3.py` (vol_regime_x_momentum, trend_efficiency_signed)
- 1 module to extend: `features_v3/cross_btc_v3.py` (sym_vs_btc_ret_3d, sym_vs_btc_vol_14d)
- 1 module to extend: `features_v3/microstructure_v3.py` (taker_buy_imbalance_20, taker_buy_zscore_50)
- 1 module to extend: `features_v3/momentum_accel_v3.py` (ret_1d/3d/5d/20d)
- 1 file to extend: `features_v3/__init__.py` (V3_FEATURE_COLUMNS_TOP_N rewrite)

## Tests

- ~3-5 NEW tests per new module (RSI bounds, stochastic [0,100], cyclic shape)
- 1 NEW test: V3_FEATURE_COLUMNS_TOP_N count assertion
- Expected test suite growth: 34 → ~45

## Dependencies

- NO new external deps required (all features computable with pandas + numpy)
- ta-lib NOT required (canonical TA computed inline with EWM/rolling)

## Feature regeneration wall-clock estimate

- features_v3 parquet regen for BCH+LDO+TRX+BTC: ~3-5min (existing infrastructure)
- This time IS included in the 1.2h wall-clock estimate

## Risk to wall-clock

- /060 + /061 ran at 0.69h
- New features add ~10-15% Optuna search time
- Estimate: 0.8-1.0h for backtest; total iter 1.2h within 2h cap

