# Iteration 086 Engineering Report — Slow Feature Augmentation + Noise Pruning

**Date**: 2026-03-30
**Runtime**: 3,922s (~65 min)

## Configuration

- **Features**: 117 (baseline 113 - 13 noisy + 15 slow + 2 calendar already in baseline)
- **New slow features**: slow_rsi_42, slow_rsi_63, slow_stoch_k_42, slow_stoch_d_42, slow_roc_45, slow_roc_90, slow_adx_42, slow_natr_42, slow_natr_63, slow_bb_bandwidth_60, slow_bb_pctb_60, slow_hist_vol_100, slow_zscore_150, slow_skew_100, slow_kurtosis_100
- **Dropped noisy features**: stat_return_1, stat_return_2, stat_log_return_1, vol_range_spike_12, vol_taker_buy_ratio, vol_volume_rel_5, vol_volume_pctchg_3, vol_volume_pctchg_5, xbtc_return_1, vol_obv, vol_ad, interact_ret1_x_natr, interact_ret1_x_ret3
- **Model**: LGBMClassifier ensemble (seeds 42, 123, 789)
- **Labeling**: TP=8%, SL=4%, timeout 7 days, fee-aware
- **Walk-forward**: monthly, 24mo window, 5 CV folds, 50 Optuna trials
- **Execution**: Dynamic ATR barriers (TP=2.9×NATR, SL=1.45×NATR), cooldown=2
- **Symbols**: BTCUSDT + ETHUSDT (pooled)
- **Feature whitelist**: Explicit `feature_columns` parameter (new)

## Code Changes

1. **`src/crypto_trade/features/slow.py`** (new): Slow feature generation module with 15 daily-equivalent features
2. **`src/crypto_trade/features/__init__.py`**: Registered "slow" feature group
3. **`src/crypto_trade/strategies/ml/lgbm.py`**: Added `feature_columns` and `trading_symbols` parameters to LightGbmStrategy
4. **`run_iteration_086.py`**: Runner with curated feature whitelist

## Results

### Comparison to Baseline

| Metric | IS (086) | IS (baseline) | OOS (086) | OOS (baseline) |
|--------|----------|---------------|-----------|----------------|
| Sharpe | +0.53 | +1.22 | **-0.17** | +1.84 |
| WR | 40.5% | 43.4% | **34.6%** | 44.8% |
| PF | 1.14 | 1.35 | **0.96** | 1.62 |
| MaxDD | 69.2% | 45.9% | **59.0%** | 42.6% |
| Trades | 328 | 373 | 107 | 87 |

### OOS/IS Ratio: -0.32 (catastrophic)

### Per-Symbol OOS

| Symbol | Trades | WR | Net PnL |
|--------|--------|-----|---------|
| BTCUSDT | 58 | 29.3% | -38.4% |
| ETHUSDT | 49 | 40.8% | +30.5% |

BTC collapsed below break-even (29.3% WR). ETH held up (40.8% WR) but overall OOS is negative.

### Exit Reasons (OOS)

| Reason | Count | % |
|--------|-------|---|
| stop_loss | 61 | 57% |
| take_profit | 29 | 27% |
| timeout | 15 | 14% |
| end_of_data | 2 | 2% |

SL rate increased from 51% (baseline IS) to 57% OOS. TP rate dropped from 32% to 27%.

## Trade Execution Verification

Verified 5 sample OOS trades — all PnL calculations correct:
- Entry/exit prices match signal candle closes
- SL/TP based on ATR multipliers
- Fee deduction consistent (0.1% per trade)
- PnL formula: (exit-entry)/entry for long, (entry-exit)/entry for short

## Analysis

The slow features + noise pruning degraded performance across all metrics. IS Sharpe dropped 57% (1.22 → 0.53) and OOS went negative. The feature changes hurt the model rather than helping it.

**Why**: The dropped "noisy" features (stat_return_1, range_spike_12, taker_buy_ratio) may have been carrying short-term signal that the model needs. The slow features (period 42-150) have long warm-up periods that reduce effective training data, and may not add discriminative power beyond what existing period 21-100 features already provide. The 3x lookback multiplier creates features that change too slowly to predict 8h-candle direction.
