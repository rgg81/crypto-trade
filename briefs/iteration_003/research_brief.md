# Research Brief: 8H LightGBM Iteration 003

## 0. Data Split & Backtest Approach

- OOS cutoff date: 2025-03-24 (project-level constant, applies to all iterations)
- The researcher used ONLY IS data (before 2025-03-24) for all design decisions below
- The walk-forward backtest runs on the FULL dataset (IS + OOS) as one continuous process
- Monthly retraining with timeseries CV, 12-month minimum training window (unchanged)
- The report layer splits backtest results at OOS_CUTOFF_DATE into two report batches

## 1. Change from Iteration 002

**Single variable change: reduce features from 185 to top 40 by importance.**

### Problem Identified in Iteration 002

Win rate stuck at 30.7% despite confidence thresholding. The model uses 185 features — many of which are noise (31 features have zero importance, the bottom 80% contribute only 20% of signal). Noise features dilute the model's ability to learn and may cause overfitting to irrelevant patterns.

### Analysis (IS data only)

Trained a single LightGBM on last 12 months of IS data (50 symbols, ~49K rows) and ranked features by split importance:

- Top 11 features cover 50% of total importance
- Top 39 features cover 80% of total importance
- Top 63 features cover 90%
- 31 features have exactly zero importance

### Selected Features (top 40, covering ~80% of importance)

**Volume (12):** vol_ad, vol_vwap, vol_obv, vol_taker_buy_ratio_sma_50, vol_garman_klass_50, vol_atr_14, vol_hist_50, vol_atr_21, vol_parkinson_50, vol_parkinson_30, vol_cmf_20, vol_cmf_14

**Trend (12):** trend_sma_100, trend_ema_100, trend_sma_50, trend_adx_21, trend_sma_cross_20_100, trend_ema_21, trend_ema_50, trend_aroon_osc_50, trend_ema_9, trend_ema_cross_12_50, trend_ema_5, trend_ema_12

**Statistical (6):** stat_skew_50, stat_autocorr_lag10, stat_autocorr_lag5, stat_autocorr_lag1, stat_kurtosis_50, stat_skew_30

**Mean Reversion (4):** mr_dist_vwap, mr_pct_from_high_100, mr_pct_from_low_100, mr_zscore_100

**Volatility (5):** vol_range_spike_96, vol_atr_10, vol_parkinson_20, vol_garman_klass_20, vol_hist_30

**Momentum (1):** mom_macd_signal_12_26_9

### Rationale

- Dominated by **long-period features** (50, 100) → the model relies on multi-week context
- **Volume features** are most important (vol_ad, vol_vwap, vol_obv dominate top 3)
- **Autocorrelation and skew** features are valuable — capturing serial dependency
- Short-period momentum (RSI, Stochastic, Williams %R) contributes very little
- Reducing from 185→40 features cuts noise by 78%

## 2. Everything Else Unchanged

| Component | Value | Change? |
|-----------|-------|---------|
| Labeling | TP=4%, SL=2%, timeout=4320min, fee-aware | No |
| Symbols | 201 USDT | No |
| Walk-forward | Monthly, 12-month, 5 CV, 50 Optuna trials | No |
| Confidence threshold | Optuna 0.50–0.65 | No |
| LightGBM | Binary classifier, is_unbalance=True | No |
| Sharpe metric | Actual returns with threshold | No |
| Seed | 42 | No |

## 3. Implementation Spec

### Changes to `lgbm.py`

In `_discover_feature_columns()` or in `_train_for_month()`, after discovering all columns, filter to only the 40 selected features. The simplest approach: add a `SELECTED_FEATURES` constant list and intersect with discovered columns.

Alternatively, add a `feature_columns` parameter to `LightGbmStrategy.__init__()` that accepts an explicit feature list. If provided, use it instead of discovering all columns.

### No changes to optimization.py or labeling.py.
