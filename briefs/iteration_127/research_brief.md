# Iteration 127 — Research Brief

**Type**: EXPLOITATION (LINK with pruned features — meme model architecture)
**Date**: 2026-04-03
**OOS cutoff**: 2025-03-24 (fixed, never changes)

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24
```

## Objective

Prune LINK from 185 auto-discovered features to ~45 curated features. Iter 126 showed LINK has genuine signal (IS +0.45, OOS +1.20) with 185 features at samples/feature ratio ~15. Feature pruning doubled the meme model's OOS Sharpe (iter 117: +0.29→+0.66). Same approach for LINK.

## Feature Selection (45 features)

Using the meme model's proven feature categories, selecting features available in LINK's parquet:

**Volume & Microstructure (8)**: vol_taker_buy_ratio, vol_taker_buy_ratio_sma_10, vol_volume_pctchg_5, vol_volume_pctchg_10, vol_volume_rel_10, vol_cmf_14, vol_mfi_7, vol_mfi_14

**Volatility (5)**: vol_natr_14, vol_bb_bandwidth_20, vol_garman_klass_10, vol_range_spike_12, vol_range_spike_24

**Mean Reversion (5)**: mr_zscore_20, mr_zscore_50, mr_bb_pctb_20, mr_pct_from_high_20, mr_pct_from_low_20

**Momentum (6)**: mom_rsi_5, mom_rsi_14, mom_roc_5, mom_roc_10, mom_stoch_k_5, stat_return_1

**Statistical (3)**: stat_return_5, stat_autocorr_lag1, stat_skew_10

**Trend (2)**: trend_adx_14, trend_psar_dir

**Additional (16 — to reach ~45, add proven indicators)**:
- mom_stoch_d_5, mom_macd_hist, mom_roc_20, mom_rsi_21
- vol_natr_21, vol_atr_pctchg_14, vol_bb_bandwidth_50
- mr_zscore_100, mr_pct_from_high_50, mr_pct_from_low_50
- trend_aroon_osc_14, trend_cci_14, trend_adx_21
- stat_return_10, stat_log_return_5, stat_kurtosis_20

**Total: 45 features. Samples/feature ratio: ~2,750/45 ≈ 61** (up from ~15 with 185 features).

## Architecture

- Same as iter 126 but with explicit 45 features
- ATR labeling 3.5x/1.75x
- 5-seed ensemble, 50 Optuna trials, 24-month training

## Research Checklist

- **A** (features): Feature pruning 185→45, following meme model proven approach
- **B** (symbols): LINK standalone exploitation after Gate 3 pass
