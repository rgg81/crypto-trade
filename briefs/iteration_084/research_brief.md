# Iteration 084 Research Brief — Aggressive Feature Pruning

**Type**: EXPLORATION
**Date**: 2026-03-30
**QR**: Claude (autopilot)

## Section 0: Data Split (verbatim, never changes)

- OOS cutoff date: **2025-03-24** (fixed for all iterations)
- IS period: all data before 2025-03-24
- OOS period: all data from 2025-03-24 onward
- The walk-forward backtest runs on ALL data (IS + OOS) as one continuous process
- Reports split at cutoff: `in_sample/` and `out_of_sample/`
- QR sees OOS for the first time in Phase 7

## Section 1: Motivation

Iteration 083 proved that adding features without pruning is catastrophic: 198 features dropped IS Sharpe 43% and IS MaxDD ballooned to 72%. The baseline's 106 features are already too many — the signal is likely concentrated in 30-50 features.

This iteration tests the hypothesis: **aggressive pruning to ~50 features will improve model stability and OOS generalization by increasing the samples-per-feature ratio from 106 to 229.**

7 consecutive NO-MERGE iterations (077-083) demand a structural change. Feature pruning is the most evidence-backed intervention available.

## Section 2: Research Analysis

Completed **4 categories** from the Research Checklist (required: 4+ after 3+ NO-MERGE):

### A1: Feature Pruning Protocol (MANDATORY)

**Starting point**: 198 features (BTC+ETH symbol-scoped discovery, iter 083)

**Step 1 — Reference model**: Trained LightGBM on full IS period (11,214 samples, BTC+ETH pooled). Used gain-based importance to rank all 198 features.

**Step 2 — Correlation dedup** (|Spearman| > 0.90):
- **82 features dropped** due to high correlation with more important features
- Major redundancy clusters:
  - `stat_return_*` / `stat_log_return_*` perfectly correlated with `mom_roc_*` (correlation = 1.0)
  - `vol_hist_*` variants (10/20/30/50) all highly correlated (kept vol_hist_30)
  - `vol_parkinson_*` / `vol_garman_klass_*` correlated with each other (kept garman_klass)
  - `mom_stoch_k_*` / `mom_stoch_d_*` correlated with `mom_rsi_*` (kept RSI via macd_signal)
  - `trend_ema_*` / `trend_sma_*` raw values correlated (kept crossover ratios)
  - `mr_bb_pctb_*` correlated with `vol_bb_pctb_*` (dropped all—low importance)
  - `mom_williams_r_*` correlated with `mom_rsi_*` (dropped all)
- 116 features survived

**Step 3 — Importance threshold**:
- Ranked surviving 116 features by gain importance
- 95% cumulative importance reached at feature #78
- Selected top 50 features (capturing 82.9% of total importance)
- Bottom 66 features share only 17.1% of importance — noise

**Step 4 — Stability check** (3 non-overlapping IS sub-periods):
- Period 1 (2020-2021): 4,386 rows
- Period 2 (2022-2023): 4,380 rows
- Period 3 (2024-2025.03): 2,688 rows

**11 stable features** (top-20 in ALL 3 periods):

| Feature | Period 1 rank | Period 2 rank | Period 3 rank |
|---------|---------------|---------------|---------------|
| mr_pct_from_low_100 | 1 | 16 | 3 |
| vol_vwap | 8 | 6 | 1 |
| trend_adx_21 | 4 | 11 | 2 |
| xbtc_adx_14 | 6 | 8 | 4 |
| stat_autocorr_lag1 | 20 | 9 | 5 |
| vol_obv | 14 | 2 | 6 |
| vol_ad | 2 | 5 | 7 |
| mr_pct_from_low_50 | 17 | 12 | 9 |
| stat_autocorr_lag10 | 7 | 10 | 11 |
| stat_skew_50 | 10 | 7 | 12 |
| vol_hist_30 | 15 | 18 | 17 |

**1 unstable feature removed**: `vol_taker_buy_ratio_sma_20` (ranks: 5, 58, 45 — wildly inconsistent)

**Final count: 49 features** (samples/feature ratio = 229)

### A3: Feature Importance by Category

| Category | % of importance | Key features |
|----------|----------------|--------------|
| Volume/Volatility | 34.4% | vol_ad, vol_vwap, vol_obv, garman_klass, hist, mfi, cmf, atr |
| Trend | 20.1% | trend_adx_21, sma_cross_20_100, aroon_osc_50, plus_di_21 |
| Statistical | 17.8% | autocorr_lag1/5/10, skew_10/20/30/50, kurtosis_20/30/50 |
| Mean Reversion | 13.2% | mr_dist_vwap, pct_from_low_100, pct_from_high_100, zscore_100 |
| Momentum | 7.6% | mom_macd_signal_12_26_9, mom_roc_30 |
| Cross-Asset | 5.6% | xbtc_adx_14, xbtc_natr_21 |
| Interaction | 1.2% | interact_natr_x_adx |

**Economic hypotheses for top-10:**
1. **vol_taker_buy_ratio_sma_50**: Persistent order flow imbalance — directional conviction over 50 candles
2. **vol_vwap**: Price position relative to volume-weighted average — institutional anchor point
3. **vol_ad**: Accumulation/Distribution — divergences between price and volume pressure
4. **mr_dist_vwap**: Distance from VWAP — measures how extended price is from fair value
5. **vol_obv**: On-Balance Volume — confirms/denies price trends with volume
6. **trend_adx_21**: Trend strength — strong trends are more predictable directionally
7. **stat_autocorr_lag10**: Serial correlation at ~3.3 day lag — momentum persistence
8. **stat_autocorr_lag1**: Short-term autocorrelation — immediate trend continuation
9. **stat_autocorr_lag5**: Medium-term autocorrelation — multi-day trend persistence
10. **mr_pct_from_low_100**: Position relative to 100-period range — mean reversion anchor

**49 noise features** (importance < 0.1%) were removed. These include all RSI extremes, range spikes (at these feature counts they contribute nothing), log returns, individual returns, and Bollinger %B variants.

### E: Trade Pattern Analysis (IS labels)

- **Label distribution**: 40% long / 60% short overall. BTC 41.7% long, ETH 39.2% long — short bias in IS period
- **Label flip rate**: BTC 12.3%, ETH 14.7% — very low, labels are temporally stable (good for ML)
- **Hour-of-day**: No significant difference (40.0-41.2% long rate across all 3 sessions)
- **Monthly variance**: Long rate ranges from 11.7% (June 2024) to 72.6% (July 2020) — labels capture market regime shifts

### F: Statistical Rigor

- **Bootstrap WR**: Mean 40.0%, 95% CI [39.1%, 41.0%]
- **Break-even is 33.3%** (for 8%/4% TP/SL) — CI is entirely above break-even
- **Binomial p-value vs 33.3%**: < 1e-50 (highly significant)
- **Binomial p-value vs 50%**: < 1e-99 (significantly below 50% — short bias is real)
- **Interpretation**: The labeling process produces robust directional signal well above break-even. The model does not need to be clever — it needs to filter confidently.

## Section 3: Configuration

### What Changes (vs baseline iter 068)
| Parameter | Baseline (068) | This iteration |
|-----------|---------------|----------------|
| Feature discovery | Global intersection (113) | **Symbol-scoped + pruned (49)** |
| Feature count | 106 (global) | **49** |
| Samples/feature ratio | ~106 | **~229** |

### What Stays the Same
- Symbols: BTCUSDT + ETHUSDT (pooled)
- Labeling: Binary, TP=8%, SL=4%, timeout=7 days
- Training: 24 months, 5 CV folds, 50 Optuna trials
- Ensemble: 3 seeds [42, 123, 789]
- Execution: Dynamic ATR barriers TP=2.9×NATR_21, SL=1.45×NATR_21
- Signal cooldown: 2 candles

### Feature List (49 features)

The QE must implement a feature filter in the runner script that restricts `_discover_feature_columns` to exactly these 49 features:

```
vol_taker_buy_ratio_sma_50, vol_vwap, vol_ad, mr_dist_vwap, vol_obv,
trend_adx_21, stat_autocorr_lag10, stat_autocorr_lag1, stat_autocorr_lag5,
mr_pct_from_low_100, xbtc_natr_21, xbtc_adx_14, trend_sma_cross_20_100,
stat_kurtosis_20, stat_skew_50, stat_skew_30, vol_garman_klass_50,
trend_sma_cross_20_50, stat_skew_20, stat_kurtosis_30, vol_hist_30,
mr_pct_from_high_100, stat_kurtosis_50, mr_zscore_100, trend_aroon_up_50,
trend_aroon_osc_50, stat_skew_10, mom_macd_signal_12_26_9, vol_mfi_10,
trend_plus_di_21, trend_aroon_osc_25, mr_pct_from_high_50, vol_garman_klass_10,
vol_cmf_10, vol_cmf_20, mom_roc_30, mr_pct_from_low_50, vol_mfi_7,
trend_adx_14, interact_natr_x_adx, vol_mfi_14, vol_cmf_14, trend_aroon_down_50,
vol_atr_21, vol_bb_bandwidth_20, vol_bb_bandwidth_30, stat_kurtosis_10,
mr_pct_from_low_20, trend_aroon_osc_14
```

### Implementation Notes for QE

1. Use `symbols=["BTCUSDT", "ETHUSDT"]` in `_discover_feature_columns()` (symbol-scoped, not global)
2. After discovery, filter the column list to only the 49 features above
3. If any of the 49 features are missing from parquet, log a warning and proceed with available subset
4. The `columns` parameter in `lookup_features()` and `load_features_range()` should pass only these 49 features for efficiency

## Section 4: Success Criteria

**Primary**: OOS Sharpe > baseline +1.84 (stretch goal: unlikely with just pruning, but any improvement validates the approach)

**Realistic target**: IS Sharpe >= baseline +1.22 with IS MaxDD <= 50%. If IS metrics are at least as good as baseline, the pruning worked — the 57 removed features were noise.

**Hard constraints**:
- IS MaxDD < 55% (iter 083 lesson: IS MaxDD > 55% = OOS failure)
- Samples/feature ratio > 50 (49 features → ratio 229 ✓)
- At least 300 IS trades and 50 OOS trades
