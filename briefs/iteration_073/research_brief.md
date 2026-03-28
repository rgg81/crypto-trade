# Research Brief: 8H LightGBM Iteration 073

**Type**: EXPLORATION (feature pruning — fundamentally changes feature space)

## 0. Data Split & Backtest Approach
- OOS cutoff date: 2025-03-24 (project-level constant, applies to all iterations)
- The researcher used ONLY IS data (before 2025-03-24) for all design decisions below
- The walk-forward backtest runs on the FULL dataset (IS + OOS) as one continuous process
- Monthly retraining with timeseries CV, 24-month training window (existing approach, unchanged)
- The report layer splits backtest results at OOS_CUTOFF_DATE into two report batches

## Research Analysis (Mandatory — 5 NO-MERGEs)

### Category A: Feature Contribution Analysis

Trained a single LightGBM on full IS data (11,454 samples × 185 features) to get split importance.

**Key findings:**
- **59 features (32%) have importance ≤ 5** — effectively zero contribution
- Top 24 features capture 50% of importance
- Top 60 features capture 77.5% of importance
- Top 80 features capture 85.5% of importance
- **Group importance**: vol (39.6%), trend (23.0%), stat (18.1%), mr (10.4%), mom (8.9%)
- Top features are long-period, scale-dependent: vol_vwap, vol_obv, stat_autocorr_lag5, vol_ad, trend_sma_100

**Pruning recommendation**: Keep top 60 features. This improves the samples/feature ratio from 24 (11454/185) to 73 (4400 training samples / 60 features), which should reduce overfitting in walk-forward monthly windows.

### Category C: Labeling Analysis

- Direction distribution: 54.4% long, 45.6% short — acceptable imbalance
- SHORT is significantly better than LONG: 46.5% WR vs 40.9% WR, 4.5x more total PnL
- TP rate 32.2%, SL rate 51.2%, Timeout 16.6%
- Actual RR ratio: 1.94:1 (close to target 2:1)
- Timeout neutrality: only 18/62 timeouts (29%) have |return| < 1% — NOT enough to justify ternary labeling
- **Conclusion**: Current labeling is adequate. Ternary labeling would only reclassify 18 trades, insufficient impact.

### Category E: Trade Pattern Analysis

- Quarterly PnL is highly variable: best +113% (2022-Q2), worst -9.5% (2023-Q4)
- Hour 07:00 UTC has best WR (45.6%) and most PnL (+133.6% of total)
- ETH generates 2.3x more PnL than BTC per trade (+0.91% vs +0.47%)
- Exit reasons: TP=32.2%, SL=51.2%, Timeout=16.6%. TP rate is the critical metric.
- Max loss streak: 11 trades — large but expected for 43% WR
- **No structural trade pattern issues** — the model trades both directions and both symbols

### Category F: Statistical Rigor

- WR 43.4%, 95% CI [38.6%, 48.5%] — significantly different from 50% (p=0.013)
- **WR significantly above break-even of 34.0%** (p=0.0002) — strong confirmation signal exists
- Mean PnL +0.71%, t-stat=2.41, p=0.017 — statistically significant profitability
- Bootstrap Sharpe 95% CI: [0.03, 0.22] — positive but barely above zero
- Sharpe degrading over IS quarters: Q1=0.25, Q2=0.01, Q3=0.10, Q4=0.06
- **Conclusion**: Signal is REAL (p<0.02) but NOISY. Reducing noise sources (low-importance features) is the right approach.

## Core Hypothesis

**Feature pruning to top 60 features by split importance.**

After 5 consecutive NO-MERGEs where feature additions (iters 070, 072) and symbol additions (071) all degraded performance, the problem is clear: the model has too many features for its sample size. Every feature addition increased the feature/sample ratio beyond what LightGBM can handle with monthly walk-forward windows (~4400 samples).

Instead of adding, we REMOVE. Keep only the 60 most important features (77.5% of total importance), eliminating 125 features that contribute only 22.5% of importance collectively.

## 1. Labeling
- Method: Triple barrier (UNCHANGED from baseline)
- Parameters: TP=8%, SL=4%, timeout=7 days
- Label function: existing `label_trades()` with fee_pct=0.1

## 2. Symbol Universe
- Approach: BTC+ETH only (UNCHANGED from baseline)
- Symbols: BTCUSDT, ETHUSDT

## 3. Data Filtering
- No changes from baseline
- No outlier handling changes
- No volume filters

## 4. Feature Candidates

**CHANGE: Static feature whitelist (top 60 by IS split importance)**

The following 60 features will be used (all others excluded):

```
vol_vwap, vol_obv, stat_autocorr_lag5, vol_ad, trend_sma_100,
trend_adx_21, mr_pct_from_low_100, stat_autocorr_lag1, stat_skew_50,
vol_taker_buy_ratio_sma_50, trend_sma_cross_20_100, mr_dist_vwap,
stat_kurtosis_50, vol_garman_klass_30, trend_sma_50, stat_skew_30,
stat_kurtosis_30, trend_ema_100, stat_autocorr_lag10, trend_adx_14,
mr_pct_from_low_50, vol_garman_klass_50, vol_hist_50, vol_atr_21,
vol_mfi_21, mom_macd_signal_12_26_9, mr_pct_from_high_100,
stat_skew_20, stat_kurtosis_20, vol_parkinson_30,
trend_sma_cross_20_50, trend_aroon_osc_50, trend_ema_50,
vol_bb_bandwidth_30, vol_parkinson_50, vol_atr_14, vol_hist_30,
mom_macd_signal_8_21_5, vol_atr_10, trend_sma_20,
vol_garman_klass_20, vol_parkinson_20, trend_adx_7, trend_ema_5,
vol_hist_10, mr_zscore_100, stat_kurtosis_10, trend_ema_cross_12_50,
trend_plus_di_21, trend_ema_21, vol_taker_buy_ratio_sma_20,
vol_hist_20, vol_hist_5, vol_cmf_10, mr_pct_from_high_50,
mom_roc_30, vol_natr_21, vol_taker_buy_ratio_sma_10,
mom_macd_hist_12_26_9, vol_cmf_20
```

**Feature selection method**: Pre-computed static whitelist from IS importance analysis. One-time LightGBM (n_estimators=300, max_depth=4) trained on full IS data with all 185 features, ranked by split importance, top 60 kept.

## 5. Model Spec
- Model: LightGBM (UNCHANGED)
- Task: Binary classification (long/short)
- Hyperparameters: Optuna-optimized (same ranges as baseline)
- Class weighting: is_unbalance=True
- Ensemble: 3 seeds [42, 123, 789] (UNCHANGED)

## 6. Walk-Forward Configuration
- Retraining frequency: monthly (UNCHANGED)
- Minimum training window: 24 months (UNCHANGED)
- Timeseries CV folds: 5 (UNCHANGED)
- Optuna trials: 50 per seed (UNCHANGED)

## 7. Backtest Requirements
- Position sizing: fixed $1000 per trade (UNCHANGED)
- Fees: 0.1% taker (UNCHANGED)
- Execution barriers: Dynamic ATR — TP=2.9×NATR_21, SL=1.45×NATR_21 (UNCHANGED)
- Signal cooldown: 2 candles (UNCHANGED)
- Timeout: 7 days (UNCHANGED)

## 8. Report Requirements
Two separate report directories split at OOS_CUTOFF_DATE: in_sample/ and out_of_sample/
Each containing standard suite plus comparison.csv.

## Implementation Notes for QE

1. Add `feature_whitelist: list[str] | None = None` parameter to `LightGbmStrategy.__init__`
2. In `compute_features()`, after `_discover_feature_columns()`, filter to whitelist if provided
3. Ensure `vol_natr_21` is always available for ATR barrier computation (even if not in whitelist)
4. Runner script provides the 60-feature whitelist
5. No other code changes needed — all other parameters match baseline iter 068
