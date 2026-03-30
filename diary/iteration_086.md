# Iteration 086 Diary — 2026-03-30

## Merge Decision: NO-MERGE

OOS Sharpe -0.17 vs baseline +1.84. IS Sharpe +0.53 vs baseline +1.22. Both IS and OOS degraded significantly. Slow features provided no benefit; dropping "noisy" features hurt.

**OOS cutoff**: 2025-03-24

## Hypothesis

Adding slow-period features (3x lookback multiplier, daily-equivalent indicators: RSI_42, ROC_90, ADX_42, NATR_63, etc.) would improve prediction stability by aligning feature timescale with the 7-day trade horizon. Simultaneously dropping 13 noisy features (autocorrelation < 0.35) would reduce noise in the feature space.

## Configuration Summary

- OOS cutoff: 2025-03-24 (fixed)
- **Features: 117** (baseline 113 - 13 noisy + 15 slow + 2 already present)
- **New**: `feature_columns` whitelist parameter in LightGbmStrategy
- **New**: `features/slow.py` module with 15 daily-equivalent features
- **Dropped**: stat_return_1/2, stat_log_return_1, vol_range_spike_12, vol_taker_buy_ratio, vol_volume_rel_5, vol_volume_pctchg_3/5, xbtc_return_1, vol_obv, vol_ad, interact_ret1_x_natr, interact_ret1_x_ret3
- Symbols: BTCUSDT, ETHUSDT (pooled)
- Walk-forward: monthly, 24mo window, 5 CV folds, 50 Optuna trials
- Ensemble: 3 LightGBM models (seeds 42, 123, 789)
- Execution: Dynamic ATR barriers TP=2.9, SL=1.45, cooldown=2

## Results: In-Sample

| Metric | Iter 086 | Baseline (068) |
|--------|----------|----------------|
| Sharpe | +0.53 | +1.22 |
| WR | 40.5% | 43.4% |
| PF | 1.14 | 1.35 |
| MaxDD | 69.2% | 45.9% |
| Trades | 328 | 373 |

## Results: Out-of-Sample

| Metric | Iter 086 | Baseline (068) |
|--------|----------|----------------|
| Sharpe | **-0.17** | +1.84 |
| WR | **34.6%** | 44.8% |
| PF | **0.96** | 1.62 |
| MaxDD | **59.0%** | 42.6% |
| Trades | 107 | 87 |

### Per-Symbol OOS

| Symbol | Trades | WR | PnL |
|--------|--------|-----|-----|
| BTCUSDT | 58 | 29.3% | -38.4% |
| ETHUSDT | 49 | 40.8% | +30.5% |

## What Happened

**Both the slow features and the noise pruning backfired.**

### Why slow features failed:

1. **Redundancy with existing features**: The baseline already has features up to period 100 (z-score_100, pct_from_high_100). Adding slow_rsi_42 when mom_rsi_30 already exists provides minimal new information — LightGBM can extrapolate from the existing feature range.

2. **Warm-up penalty**: Slow features with period 150 (slow_zscore_150) need 150 candles (~50 days) before producing valid values. This reduces effective training data in early walk-forward windows.

3. **Feature timescale mismatch in the wrong direction**: The research hypothesis assumed longer features = better predictions for 7-day holds. But the model doesn't predict "7-day direction" — it predicts "which direction hits TP/SL first within 7 days." This is a short-term prediction task where the first few candles after entry matter most. Short-period features (RSI_5, returns_1) capture the immediate momentum that determines whether TP or SL is hit first.

### Why dropping "noisy" features hurt:

4. **Autocorrelation ≠ predictive value**: Features with low autocorrelation (stat_return_1, range_spike_12) are "noisy" in the time-series sense, but they carry the strongest DIRECTIONAL signal for the next candle. The model doesn't need features to be stable — it needs features that differentiate between TP-first and SL-first outcomes.

5. **BTC collapsed without short-term features**: BTC OOS WR dropped to 29.3% (below break-even). The baseline's BTC WR was already lower than ETH's, and removing the short-term features that BTC-specific patterns rely on (1-candle returns, range spikes) destroyed BTC signal entirely.

## Quantifying the Gap

OOS WR: 34.6%, break-even 33.3%, gap **+1.3pp above break-even** (barely profitable). PF 0.96 — net loss after fees. Compared to baseline: WR gap is -10.2pp, PF gap is -0.66. This is worse than any iteration since iter 078 (per-symbol collapse).

## Exploration/Exploitation Tracker

Last 10 (iters 077-086): [X, E, E, X, X, X(abandoned), E, E, E, **E**]
Exploration rate: 6/10 = 60%
Type: **EXPLORATION** (new feature generation — slow features)

## Research Checklist

Completed 4 categories: A (feature stability analysis, correlation), D (lookback sensitivity — the key analysis), E (trade pattern analysis), F (statistical rigor — bootstrap CI).

**Key finding from Category D**: There IS a clear relationship between lookback period and feature stability (autocorr 0.80 at period 1-10 vs 0.91 at period 21-50). But stability ≠ predictive power. The noisy short-period features are the ones that carry the strongest directional signal for the TP/SL prediction task.

## lgbm.py Code Review

The `feature_columns` and `trading_symbols` parameters work correctly. When `feature_columns` is provided, it overrides the discovery function. When `trading_symbols` is provided, discovery is scoped to those symbols. Both are useful infrastructure for future iterations.

No bugs found. The slow features are computed correctly (verified via parquet inspection: 15 slow columns present in both BTC+ETH parquets).

## Lessons Learned

1. **Feature autocorrelation is NOT a proxy for feature importance.** The most "noisy" features (stat_return_1, range_spike_12, taker_buy_ratio) may be the most predictive for the TP/SL-first prediction task. "Stable" features (SMA, EMA) are stable because they change slowly — which means they carry less information about the immediate next candles.

2. **The prediction task is short-term, not long-term.** The 7-day timeout is a ceiling, not a target. Most TP/SL hits happen within 1-3 days (3-9 candles). Features that capture 1-3 day dynamics are exactly right. Slow features (14-50 day) are too coarse.

3. **Don't drop features based on a single metric.** Autocorrelation measures persistence, not predictive power. Feature importance from the model is a better guide for what to drop (iter 084 used this), though even that failed because importance varies by time period.

4. **The baseline's 113-feature global intersection may be accidentally optimal.** Every attempt to change the feature set has failed: expansion to 198 (iter 083), pruning to 49 (iter 084), slow replacement to 117 (iter 086). The model has had 50 Optuna trials per month to optimize feature usage via colsample_bytree. Manual feature curation is unlikely to beat automated selection.

5. **The `feature_columns` and `trading_symbols` parameters are reusable infrastructure.** These will be useful for future iterations that need to experiment with specific feature sets, regardless of this iteration's failure.

## Next Iteration Ideas

**After 10 consecutive NO-MERGE (077-086), the entire feature-centric approach is exhausted.**

Feature changes tried and failed: expansion (083), pruning (084), slow replacement (086). Model changes tried: regression (085). Architecture changes tried: per-symbol (078, 079). Label changes tried: ternary (080, 081). Only ternary showed partial promise (MaxDD improvement but Sharpe decline).

1. **EXPLOITATION: Ternary + slow features combined** — Iter 080 (ternary) was the closest to matching baseline risk-adjusted. Combine ternary labeling (neutral_threshold=2.0%) with the baseline 113 features. Unlike iter 082 (which was abandoned), this would keep cooldown=2 intact. The hypothesis is that ternary's noise reduction + baseline's proven features could match the Sharpe while maintaining the MaxDD improvement.

2. **EXPLORATION: Dynamic confidence threshold** — Instead of Optuna-optimizing a single confidence threshold per month, use a meta-model that sets the threshold based on recent model performance (rolling WR of last 20 trades). When the model is performing well, lower the threshold to take more trades; when struggling, raise it. This is a fundamentally different approach to trade selection.

3. **EXPLORATION: Multi-horizon labeling** — Instead of TP=8%/SL=4% with 7-day timeout, use multiple label horizons simultaneously: TP=4%/SL=2% (1-3 day) AND TP=8%/SL=4% (7 day). Train two models and trade based on agreement. When both horizons agree on direction, the signal is strongest.

4. **EXPLORATION: Feature importance-weighted ensemble** — Instead of averaging 3 seeds' probabilities equally, weight each model by its feature importance overlap with the current candle's feature pattern. Models whose top features are "active" (non-null, recently changing) get higher weight.
