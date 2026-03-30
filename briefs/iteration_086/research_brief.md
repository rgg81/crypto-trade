# Iteration 086 Research Brief — Slow Feature Augmentation + Noise Pruning

**Type**: EXPLORATION (new feature generation — features that don't exist in the pipeline)
**Date**: 2026-03-30

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

- IS period: all data before 2025-03-24 (~5,727 candles per symbol, ~5.3 years)
- OOS period: 2025-03-24 onward (~1 year)
- The walk-forward backtest runs on ALL data continuously. Reports split at the cutoff.
- The researcher (me) designed this brief using ONLY IS data and IS reports.

## Section 1: Research Analysis (4 categories — mandatory after EARLY STOP)

### Category A: Feature Stability & Contribution

**Feature autocorrelation analysis** (lag-1, pooled BTC+ETH IS data, 11,454 candles):

| Category    | Mean Autocorr | Mean Flip Rate | Count |
|-------------|---------------|----------------|-------|
| trend       | 0.955         | 0.169          | 39    |
| momentum    | 0.912         | 0.388          | 36    |
| mean_rev    | 0.889         | 0.453          | 26    |
| statistical | 0.806         | 0.514          | 24    |
| cross-asset | 0.785         | 0.448          | 7     |
| volume      | 0.779         | 0.479          | 60    |
| interaction | 0.637         | 0.490          | 6     |

**9 features with autocorr < 0.3 (essentially random candle-to-candle)**:
- `stat_return_1` (0.03), `stat_log_return_1` (0.04), `xbtc_return_1` (0.03)
- `interact_ret1_x_ret3` (0.06), `interact_ret1_x_natr` (-0.08)
- `vol_range_spike_12` (0.22), `vol_range_spike_24` (0.26)
- `vol_taker_buy_ratio` (0.24), `vol_volume_rel_5` (0.18)

**Correlation**: Only 3 highly correlated pairs (all volume metadata: quote_volume ↔ taker_buy_quote_volume r=0.999). The baseline's 113 features are already well-decorrelated.

**Feature count**: Global intersection gives 113 features. BTC+ETH scoped gives 198. The extra 85 include Stochastic, MACD, Aroon, ADX, Bollinger, MFI, CMF, interaction, and cross features. Iter 083 showed adding all 198 hurts (ratio drops to 22). But iter 084 showed pruning to 49 also hurts.

### Category D: Feature Frequency & Lookback Analysis

**This is the key finding.** Clear monotonic relationship between lookback period and feature stability:

| Lookback Bin  | Equiv. Days | Count | Mean Autocorr | Mean Autocorr (lag-3) |
|---------------|-------------|-------|---------------|-----------------------|
| 1-10 (≤3d)   | ≤3.3        | 73    | 0.803         | 0.557                 |
| 11-20 (≤7d)  | 3.7-6.7     | 49    | 0.886         | 0.756                 |
| 21-50 (≤17d) | 7-16.7      | 52    | 0.908         | 0.833                 |
| 51-100 (≤33d)| 17-33       | 8     | 0.834         | 0.790                 |
| 101+ (>33d)  | >33         | **0** | —             | —                     |

**No features with lookback > 100 exist.** The entire feature space lacks slow, trend-level signals. On 8h candles, the longest computed periods are ~33 days. Daily-equivalent indicators would use 3x the period.

RSI stability by period (monotonic improvement):
- RSI_5: autocorr 0.82 → RSI_30: autocorr 0.97

ROC stability by period:
- ROC_3: autocorr 0.66 → ROC_30: autocorr 0.97

**Economic rationale**: 8h candles with short lookbacks (RSI_5 = 40h ≈ 1.7 days) create features that flip every candle. The model must predict direction for a 7-day hold (TP=8%/SL=4%), but features capture only 1-3 day dynamics. There's a **temporal mismatch** between feature timescale and trade horizon. Slow features (RSI_42 = 14 days, RSI_63 = 21 days) align feature timescale with the trade holding period.

### Category E: Trade Pattern Analysis (IS baseline, 373 trades)

**Direction asymmetry**: Short WR=46.5% (mean PnL +1.37%) vs Long WR=40.9% (mean PnL +0.34%). The model is significantly better at short entries.

**Exit reasons**: 51% SL (mean -3.75%), 32% TP (mean +7.59%), 17% timeout (mean +1.74%, WR 67.7%). Timeout trades are highly profitable — the model identifies good entries but some positions need more than 7 days.

**Monthly variance**: Extreme — from +70% (Jun 2022) to -20% (Jun 2024). Strong in volatile bear markets (2022 H1), weak in ranging markets (2023 H2, 2024 Q4).

**Recent IS weakness**: 4 of 5 months negative from Sep 2024 to Jan 2025 (-48% cumulative). The model struggles in the recent IS period, suggesting feature signals have been degrading for short-period indicators in recent market conditions.

### Category F: Statistical Rigor

- **Bootstrap WR 95% CI**: [38.6%, 48.5%] — comfortably above 33.3% break-even
- **Bootstrap Sharpe 95% CI**: [0.17, 0.81] — P(Sharpe > 0) = 99.8%
- **Binomial test**: WR significantly > 33.3% break-even (p = 2.9e-5)
- **WR NOT > 50%** (p = 0.995) — strategy profits from asymmetric payoff (2:1 TP/SL), not directional accuracy
- **CI width**: 0.64 Sharpe units. Any proposed improvement must exceed this to be detectable.

## Section 2: Diagnosis & Gap Analysis

After 9 consecutive NO-MERGE (077-085):
- Feature expansion (198 features) hurt — too many, dilutes signal (iter 083)
- Feature pruning (49 features) hurt — removes BTC-specific signal (iter 084)
- Regression labeling catastrophically worse (iter 085)
- Per-symbol models dead for 2-symbol universe (iter 078, 079)
- Ternary: best exploration (iter 080), MaxDD improved but Sharpe fell

**Root cause hypothesis**: The baseline's features are heavily weighted toward short-period indicators (73 features with period ≤10, covering ≤3 days). These features are noisy (autocorr ~0.80) and capture intra-day dynamics, while the trade horizon is 7 days. Adding slow features that match the trade timescale could improve signal stability without changing the model architecture.

## Section 3: Proposed Change

### Hypothesis

Adding slow-period features (3x lookback multiplier, equivalent to daily indicators) will improve prediction stability by aligning feature timescale with the 7-day trade horizon. The model currently sees 1-3 day dynamics and must extrapolate to 7 days; slow features provide direct 14-21 day trend information.

### Specific Changes

**1. New slow feature group** (`features/slow.py`): ~15 new features

| Feature | Period | Days | Rationale |
|---------|--------|------|-----------|
| slow_rsi_42 | 42 | 14 | Daily RSI_14 — primary momentum |
| slow_rsi_63 | 63 | 21 | Daily RSI_21 — confirms longer trend |
| slow_stoch_k_42, slow_stoch_d_42 | 42 | 14 | Daily Stochastic — overbought/oversold |
| slow_roc_45 | 45 | 15 | Daily ROC_15 — 2-week momentum |
| slow_roc_90 | 90 | 30 | Daily ROC_30 — monthly momentum |
| slow_adx_42 | 42 | 14 | Daily ADX_14 — trend strength |
| slow_natr_42 | 42 | 14 | Daily NATR_14 — volatility regime |
| slow_natr_63 | 63 | 21 | Daily NATR_21 — vol regime confirm |
| slow_bb_bandwidth_60 | 60 | 20 | Daily BB_20 — squeeze detection |
| slow_bb_pctb_60 | 60 | 20 | Daily BB_%B_20 — mean reversion |
| slow_hist_vol_100 | 100 | 33 | Monthly historical volatility |
| slow_zscore_150 | 150 | 50 | 50-day z-score — strong mean reversion |
| slow_skew_100 | 100 | 33 | Monthly return skewness |
| slow_kurtosis_100 | 100 | 33 | Monthly return kurtosis |

**2. Add `feature_columns` parameter to `LightGbmStrategy`**: Explicit whitelist overrides discovery. This prevents the feature count from ballooning.

**3. Curated feature list (~115 features)**: Baseline 113 + 15 slow features - 13 noisiest features. Drop list:
- `stat_return_1`, `stat_return_2` (autocorr < 0.1, pure noise)
- `stat_log_return_1` (autocorr 0.04)
- `interact_ret1_x_natr` (autocorr -0.08, negatively autocorrelated)
- `interact_ret1_x_ret3` (autocorr 0.06)
- `vol_range_spike_12` (autocorr 0.22)
- `vol_taker_buy_ratio` (autocorr 0.24)
- `vol_volume_rel_5` (autocorr 0.18)
- `vol_volume_pctchg_3` (autocorr 0.34)
- `vol_volume_pctchg_5` (autocorr 0.31)
- `xbtc_return_1` (autocorr 0.03)
- `vol_obv` (raw cumulative, not scale-invariant)
- `vol_ad` (raw cumulative, not scale-invariant)

Net: 113 - 13 + 15 = **~115 features** (sample/feature ratio ≈ 38, healthy)

**4. Regenerate parquet files** for BTCUSDT and ETHUSDT only with slow features included.

### What stays the same

- Model: LGBMClassifier ensemble (seeds 42, 123, 789)
- Labeling: TP=8%, SL=4%, timeout 7 days, fee-aware
- Walk-forward: monthly, 24mo window, 5 CV folds, 50 Optuna trials
- Execution: Dynamic ATR barriers (TP=2.9×NATR, SL=1.45×NATR), cooldown=2
- Symbols: BTCUSDT + ETHUSDT (pooled)

### Risk assessment

- Feature count stays manageable (~115, ratio ~38)
- New features are scale-invariant (all ratios/percentages/oscillators)
- No architectural changes — same model, same labeling, same walk-forward
- Risk: slow features may have insufficient warm-up period in early training windows (need 150 candles = 50 days for slowest feature)
