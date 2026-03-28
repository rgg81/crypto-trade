# Iteration 059 Diary — 2026-03-28

## Merge Decision: NO-MERGE (EARLY STOP)

Year 2022 PnL = -39.4% (WR 34.1%). IS Sharpe -0.44 vs baseline +1.60. Per-symbol models catastrophically worse than pooled model.

**OOS cutoff**: 2025-03-24

## Hypothesis

Train separate LightGBM models for BTC and ETH instead of a single pooled model. The pooled model forces the algorithm to learn patterns common to both symbols simultaneously, even though they exhibit different trading dynamics (ETH Sharpe 3.57 vs BTC 1.22 in baseline IS). Per-symbol models could specialize in each asset's patterns.

## Configuration Summary
- OOS cutoff: 2025-03-24 (fixed)
- Labeling: triple barrier TP=8%, SL=4%, timeout=7 days
- Symbols: BTCUSDT + ETHUSDT (separate models)
- Features: **106** (same global intersection as baseline)
- Walk-forward: monthly, 24mo training, 5 CV folds, 50 Optuna trials
- Random seed: 42
- **per_symbol=True**: each symbol gets its own model

## Results: In-Sample (trades with entry_time < 2025-03-24)

| Metric | Value | Baseline IS |
|--------|-------|-------------|
| Sharpe | -0.44 | +1.60 |
| Win Rate | 34.0% | 43.4% |
| Profit Factor | 0.94 | 1.31 |
| Max Drawdown | 107.5% | 64.3% |
| Total Trades | 259 | 574 |
| PnL | -40.9% | +387.9% |

## Results: Out-of-Sample

No OOS data — early stopped in Year 1 (2022).

## What Happened

### 1. Both symbols collapsed

| Metric | BTC (per-symbol) | ETH (per-symbol) | BTC (baseline) | ETH (baseline) |
|--------|-----------------|-----------------|----------------|----------------|
| Trades | 114 | 145 | 257 | 317 |
| WR | 35.1% | 33.1% | 40.5% | 45.7% |
| TP Rate | 27.2% | 31.7% | 27.2% | 36.3% |
| SL Rate | 59.6% | 65.5% | 51.0% | 52.4% |
| PnL | -20.1% | -20.7% | +81.8% | +306.1% |

ETH was supposed to be the strong symbol. Instead it suffered the worst degradation: WR dropped 12.6pp (45.7% → 33.1%), falling below break-even (34.2%). BTC dropped 5.4pp. Both symbols had massive SL rate increases — the models predicted direction worse than random.

### 2. Why pooling works (the key insight)

The hypothesis that "BTC and ETH have different dynamics, so separate models should do better" was **wrong**. The pooled model benefits from:

1. **2x training data**: ~4400 samples vs ~2200 per symbol. With 106 features, the sample-to-feature ratio drops from ~41:1 to ~21:1. While still adequate for LightGBM on paper, the effective dimensionality matters — Optuna needs sufficient data to identify meaningful hyperparameter configurations.

2. **Cross-symbol regularization**: BTC and ETH share many market dynamics (crypto correlation ~0.85 at macro level). The pooled model learns patterns that generalize across both — momentum regimes, volatility spikes, market-wide trends. Splitting removes this implicit regularization.

3. **Optuna needs volume**: With half the data, Optuna's cross-validation folds become too small (~440 samples each). The optimization landscape becomes noisy — the best trial Sharpe across 50 trials was barely positive (0.02-0.04) for most months, compared to consistently positive best trials in the pooled model.

### 3. Data contamination note

The initial run accidentally used 137 features (stale slow features from iter 057-058 in parquet files). After regenerating BTC+ETH parquets, the clean 106-feature run was actually WORSE (Sharpe -0.44 vs 0.14). This confirms: per-symbol models are the problem, not features.

## Quantifying the Gap

- IS Sharpe: -0.44 vs baseline +1.60 — the model is UNPROFITABLE
- IS WR: 34.0%, break-even ~34.2% — literally at random (0.2pp below break-even!)
- IS PF: 0.94 — losing money on average
- ETH WR: 33.1% — the "strong" symbol fell furthest
- Trade count: 259 vs 574 — model generates 55% fewer trades

## Decision: NO-MERGE (EARLY STOP)

IS Sharpe negative. Strategy is unprofitable. Year 1 fail-fast triggered.

## lgbm.py Code Review

The per-symbol implementation is clean. Added `per_symbol` flag, `_train_for_month_per_symbol()`, `_get_signal_per_symbol()` methods alongside the existing pooled code. No bugs — the implementation correctly isolates per-symbol training and prediction. The poor results are not a code issue; they reflect the fundamental unsuitability of per-symbol models with this dataset size.

One observation: the `_discover_feature_columns()` function still reads ALL 760 parquet files for the global intersection. This is correct for per-symbol mode (ensures consistent features across symbols) but could be made configurable. Not a priority.

**Stale parquet issue**: The feature parquets for ALL symbols except BTC/ETH still contain slow features from iter 057-058. Future iterations should be aware that the global intersection might change if those symbols' parquets are ever used for feature discovery with different column sets. For the current BTC+ETH-only strategy, this is not an issue since BTC/ETH were regenerated.

## Research Checklist

Completed 4 categories (A, B, E, F) in the research brief:
- **A (Feature Contribution)**: Per-symbol feature distributions show 29/243 features with large Cohen's d (>0.5) between BTC/ETH. Kept 106 global intersection to isolate the variable.
- **B (Symbol Universe)**: Confirmed ETH dominates (78.9% of PnL, Sharpe 3.57 vs 1.22). Monthly correlation only 0.417.
- **E (Trade Patterns)**: Exit reason analysis showed ETH has 9.1pp higher TP rate and shorter timeout. Shorts outperform longs for both.
- **F (Statistical Rigor)**: BTC 95% CI touches break-even [34.2%, 46.3%]. ETH solidly above [40.7%, 51.4%].

Finding F was prophetic: BTC's marginal signal couldn't sustain a standalone model, and the per-symbol result (35.1% WR) fell within the noisy lower CI range.

## Exploration/Exploitation Tracker

Last 10 (iters 050-059): [X, E, E, E, X, X, X, E, E, E]
Exploration rate: 6/10 = 60%
Type: EXPLORATION (model architecture change)

## What We've Eliminated (iters 047-059)

| Iter | Change | Result | Learning |
|------|--------|--------|----------|
| 048 | Add _balance_weights() | NO-MERGE | More class balancing hurts |
| 049 | Parallel BTC+ETH + SOL+DOGE | NO-MERGE | Symbol pairs don't combine |
| 050 | Balanced weights (no code change) | NO-MERGE | Baseline re-run fluke |
| 051 | 14-day timeout | EARLY STOP | Longer timeout hurts |
| 052 | Add XRP to pool | EARLY STOP | More symbols hurt |
| 053 | BNB+LINK independent pair | EARLY STOP | BTC+ETH best pair |
| 054 | AVAX+DOT independent pair | EARLY STOP | BTC+ETH best pair |
| 055 | Balanced weights (real code) | NO-MERGE | Over-correction |
| 056 | Remove is_unbalance | NO-MERGE | is_unbalance is load-bearing |
| 057 | Slow features + scoped discovery | EARLY STOP | 242 features overwhelm model |
| 058 | Slow features (global intersection) | EARLY STOP | Slow features are noise |
| **059** | **Per-symbol models** | **EARLY STOP** | **Pooling is essential, not dilutive** |

**Dead ends confirmed**: symbol expansion, class weights, timeout changes, feature expansion (slow), AND now per-symbol models. The baseline 047's pooled architecture is locally optimal.

## What Worked

Nothing. But the result is informative: cross-symbol signal sharing is essential for this strategy.

## What Failed

- Per-symbol LightGBM models with ~2200 training samples per symbol
- Both BTC and ETH degraded; ETH (the "strong" symbol) fell the most
- Optuna optimization was noisy with small per-symbol CV folds

## Next Iteration Ideas

12 consecutive NO-MERGE iterations. The baseline architecture (pooled model, 106 features, 8%/4% barriers, 24mo training, BTC+ETH) appears to be locally optimal for this approach. Future iterations must consider changes OUTSIDE the current architecture.

1. **Regression target instead of classification** (EXPLORATION): Predict forward return magnitude instead of direction. The model might capture more nuanced signal from continuous targets. Classification with 34.2% break-even is hard; regression doesn't have a binary threshold.

2. **Dynamic TP/SL via ATR** (EXPLORATION): Scale barriers by recent volatility. Fixed 8%/4% works in volatile markets but may be too wide in calm periods. ATR-based barriers adapt to market conditions, potentially improving resolution.

3. **Ternary classification with neutral class** (EXPLORATION): Add "neutral" label for candles where neither TP nor SL is hit AND |timeout return| < 1%. Reduces noisy label flips and gives the model a "don't trade" option during training.

4. **Feature pruning** (EXPLOITATION): Remove the ~55 lowest-importance features. Go from 106 → ~50 features. The baseline's Optuna already has colsample_bytree for implicit feature selection, but explicit pruning reduces search space complexity.

5. **Prediction smoothing** (EXPLOITATION): Majority vote of last 3 predictions before opening a trade. Reduces direction flips and may improve trade quality. Low implementation cost.

## Lessons Learned

- **Cross-symbol pooling provides essential regularization.** The hypothesis that "separate models can specialize" was wrong for this dataset. BTC and ETH share enough dynamics that pooling doubles the effective training signal. Per-symbol models underfit.
- **Sample size matters more than specialization at N~2000.** With 2200 samples and 106 features, LightGBM can still fit, but Optuna's 50-trial search over a noisy loss landscape fails to find good hyperparameters. The pooled model's 4400 samples create a much smoother optimization surface.
- **Check parquet freshness.** Stale slow features from iter 057-058 persisted in parquets. Regenerating BTC/ETH resolved it, but this could silently confound future iterations.
- **The strongest symbol suffered the most.** ETH dropped 12.6pp WR when isolated — counterintuitive. This suggests ETH's baseline performance partly depends on BTC's patterns providing contrast/context during training.
