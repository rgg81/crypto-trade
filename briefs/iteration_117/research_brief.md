# Iteration 117 Research Brief — Meme Model: Feature Pruning (67 → 45)

**Type**: EXPLOITATION (feature pruning)
**Date**: 2026-04-01

## Section 0: Data Split (verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
IS: all data before 2025-03-24
OOS: all data from 2025-03-24 onward
```

## Objective

Prune the meme model's feature set from 67 to ~45 features by removing redundant lookback
variants and low-signal features. Fewer features = more stable model, higher samples-per-feature
ratio (4400/45 = 97.8 vs 4400/67 = 65.7).

## Feature Pruning Rationale

### Dropped features (22 features removed):

**Redundant lookback variants** (keep the most useful period, drop duplicates):
- `vol_taker_buy_ratio_sma_5` — keep sma_10 only (smoother, less noise)
- `vol_volume_pctchg_3` — keep pctchg_5 and pctchg_10
- `vol_volume_rel_5` — keep rel_10 only
- `vol_cmf_10` — keep cmf_14 only (standard period)
- `vol_natr_7`, `vol_natr_21` — keep natr_14 only (standard period)
- `vol_bb_bandwidth_10` — keep bb_bandwidth_20 only
- `mr_zscore_10` — keep zscore_20 and zscore_50
- `mr_bb_pctb_10` — keep bb_pctb_20 only
- `mr_pct_from_high_5` — keep pct_from_high_20 only
- `mom_roc_3` — keep roc_5 and roc_10
- `mom_stoch_d_5` — keep stoch_k_5 (k and d are highly correlated)
- `stat_return_3` — keep return_1 and return_5

**Low-signal meme features** (microstructure noise):
- `meme_vol_body` — body × volume product, noisy
- `meme_body_expansion` — captures same info as vol_range_spike
- `meme_taker_accel` — derivative of noisy signal
- `meme_vol_trend` — OBV-like, unstable for meme coins

**Redundant trend features**:
- `meme_new_low_20` — keep new_high_20 only (asymmetric signal)
- `meme_hh_ll_5` — captures same info as range_pos_50 + rsi_slope_5

**Redundant cross-asset**:
- `xbtc_return_10` — keep return_1 and return_5 (fast-moving meme beta)
- `xbtc_rsi_14` — keep natr_14 (volatility more predictive than momentum for meme)

### Kept features (45 total):

**Volume & Microstructure (8)**: vol_taker_buy_ratio, vol_taker_buy_ratio_sma_10,
vol_volume_pctchg_5, vol_volume_pctchg_10, vol_volume_rel_10, vol_cmf_14, vol_mfi_7, vol_mfi_14

**Volatility (5)**: vol_natr_14, vol_bb_bandwidth_20, vol_garman_klass_10,
vol_range_spike_12, vol_range_spike_24

**Mean Reversion (5)**: mr_zscore_20, mr_zscore_50, mr_bb_pctb_20,
mr_pct_from_high_20, mr_pct_from_low_20

**Momentum (6)**: mom_rsi_5, mom_rsi_14, mom_roc_5, mom_roc_10,
mom_stoch_k_5, stat_return_1

**Statistical (3)**: stat_return_5, stat_autocorr_lag1, stat_skew_10

**Trend (2)**: trend_adx_14, trend_psar_dir

**Microstructure (8)**: meme_body_ratio, meme_upper_shadow, meme_lower_shadow,
meme_vol_spike_3, meme_vol_spike_10, meme_taker_imbalance, meme_range_position, meme_consec_dir, meme_indecision

**Meme Trend (5)**: meme_cum_ret_10, meme_cum_ret_30, meme_new_high_20,
meme_range_pos_50, meme_rsi_slope_5

**Cross-Asset (3)**: xbtc_return_1, xbtc_return_5, xbtc_natr_14

## Configuration (iter 114 base)

Everything identical to iter 114 except the feature set:
- Symbols: DOGEUSDT + 1000SHIBUSDT
- Features: **45** (was 67)
- Labeling: Dynamic ATR (2.9x/1.45x)
- Training: 24 months, 5 CV folds, 50 Optuna trials
- Ensemble: 5-seed [42, 123, 456, 789, 1001]
- Timeout: 7 days (10080 min) — NOT changed (learned in iter 116)
- Cooldown: 2 candles
