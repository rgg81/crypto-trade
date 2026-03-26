# Research Brief: 8H LightGBM Iteration 008

## 0. Data Split & Backtest Approach

- OOS cutoff date: 2025-03-24 (project-level constant)
- IS data only for design decisions; walk-forward on full dataset
- Monthly retraining, 12-month window, reports split at cutoff

## 1. Research Analysis (Checklist Categories A, C, E, F)

### A. Feature Contribution (IS, top 15 symbols, 2yr)

Per-group importance: Volume (27.3%) > Trend (25.2%) > Statistical (16.4%) > Volatility (14.1%) > Mean Reversion (10.6%) > Momentum (6.3%)

Top 5: vol_vwap (180), vol_obv (151), vol_ad (147), trend_sma_100 (105), mr_dist_vwap (101)

**Key findings**: Volume-price relationship is the dominant signal. Momentum indicators (RSI, Stochastic, etc.) barely contribute (6.3%). Autocorrelation features (lag 1,5,10) are in top 15 — serial dependency matters. 31/185 features have zero importance.

**CRITICAL BUG**: `_discover_feature_columns()` uses intersection across all parquet files. With 50 symbols, only 106/185 features survive. Top features vol_vwap, vol_obv, vol_ad may be missing from some symbols' parquet files, reducing available signal. Fix: union + NaN (LightGBM handles NaN natively).

### C. Labeling Analysis (IS)

- Distribution: 48.9% long, 51.1% short — well balanced
- **Label stability is HIGH**: BTC flip rate 16.6%, ETH 19.0% — labels are stable, not noisy
- **Barrier analysis**: TP_rate in labeled direction at 4%/2% is 68% — the labels have strong signal, the model just can't learn them well enough

### E. Trade Patterns (IS)

- **SHORT outperforms LONG by 4.1pp**: Short WR=32.7%, Long WR=28.6%. Huge directional asymmetry.
- **Per-hour**: 07:00 UTC best (31.8%), 23:00 UTC worst (29.2%)
- **Loss streaks average 4.0** vs win streaks 1.7 — model fails in bursts
- **TP rate is 29.5%**, SL rate 68.9%, timeout 1.6%

### F. Statistical Rigor

- **Bootstrap IS WR: 30.57% [30.18%, 30.98%]** — the 95% CI does NOT include break-even (33.3%)
- **Binomial test (WR < 33.3%): p=4.8e-37** — the model is SIGNIFICANTLY below break-even
- **Short-only CI: [32.09%, 33.28%]** — still does not include break-even
- **CONCLUSION: Parameter tuning CANNOT close the gap.** The current classification approach is structurally unable to reach break-even with the pooled model on these features.

## 2. Gap Quantification

WR is 30.6% (IS), break-even is 33.3%, gap is **2.7pp**. TP rate is 29.5%, SL rate is 68.9%. Bootstrap CI proves this gap is statistically significant (p < 1e-36). To close this gap, the strategy needs a **fundamentally different feature set or model formulation** — not parameter adjustments.

## 3. Structural Change: Fix Feature Pipeline + Add Cross-Asset Features

### Change A: Fix feature intersection → union

`_discover_feature_columns()` in lgbm.py uses set intersection. If one symbol is missing a feature, it's dropped for ALL symbols. Fix: use **union** of all features, let LightGBM handle NaN natively. This restores access to all 185 features.

### Change B: Add BTC cross-asset features

**Economic hypothesis**: Crypto is highly correlated (mean pairwise corr = 0.60 from EDA). BTC is the market leader — when BTC moves, alts follow with a lag. BTC's recent return and volatility should predict alt direction on the next candle.

**New features** (injected during training, not pre-computed in parquet):
- `btc_return_1`: BTC 1-candle return at the same open_time
- `btc_return_3`: BTC 3-candle return
- `btc_natr_14`: BTC NATR(14) at the same open_time
- `btc_rsi_14`: BTC RSI(14) at the same open_time

For BTC itself, these are the same as its own features (no leakage). For alts, these add cross-market context that no current feature provides.

**Implementation**: In `_train_for_month()`, after loading features via `lookup_features()`, join BTC features by open_time. Add 4 new columns. Same for test month batch loading.

### Why These Two Changes Together

1. The union fix is a bug fix that should have been done in iteration 001 — it's not a design choice
2. Cross-asset features are a genuinely NEW feature category (supported by checklist A finding that no cross-asset features exist)
3. Together they address the fundamental problem: the model lacks sufficient signal. More features (union) + better features (cross-asset) may push WR past break-even

### Everything Else Unchanged

Top 50 symbols, TP=4%/SL=2%, confidence threshold 0.50–0.65, 50 Optuna trials, seed 42.
