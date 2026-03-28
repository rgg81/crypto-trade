# Iteration 073 Diary — 2026-03-28

## Merge Decision: NO-MERGE (EARLY STOP)

Year 2022 PnL -21.1% (WR 35.1%, 74 trades). IS Sharpe -0.41. Static feature pruning to top 60 destroys signal.

**OOS cutoff**: 2025-03-24

## Hypothesis

Prune features from 185 → 60 (top by split importance). The model has too many features for ~4400 training samples (samples/feature ratio = 24). Removing the bottom 68% of features (22.5% of importance) should reduce overfitting.

## Configuration Summary

- OOS cutoff: 2025-03-24 (fixed)
- Labeling: Triple barrier TP=8%, SL=4%, timeout=7d (unchanged)
- Symbols: BTCUSDT, ETHUSDT (unchanged)
- Features: **60** (pruned from 185 by global IS split importance)
- Walk-forward: monthly retraining, 24mo window, 5 CV folds, 50 Optuna trials
- Ensemble: 3 seeds [42, 123, 789]
- Execution: Dynamic ATR barriers, cooldown=2

## Results: In-Sample (early stop at Year 2022)

| Metric | Iter 073 | Baseline (068) |
|--------|----------|----------------|
| IS Sharpe | **-0.41** | +1.22 |
| IS MaxDD | 69.0% | 45.9% |
| IS WR | 34.7% | 43.4% |
| IS PF | 0.89 | 1.35 |
| IS Trades | 75 | 373 |
| IS Net PnL | -23.2% | +264.3% |

OOS: not reached (early stop in Year 2022)

## What Happened

### 1. Static importance ranking doesn't transfer to walk-forward

The importance ranking was computed from a single LightGBM trained on ALL IS data (11,454 samples). But the walk-forward trains on rolling 24-month windows (~4,400 samples per month). Features that appear unimportant globally may be crucial in specific time windows.

For example, `stat_return_5` (5-candle return) had zero importance in the global model, but during trending markets it may be the strongest predictor. By pruning it, the model loses signal during those months.

### 2. The removed features provided redundancy that helped generalization

LightGBM's tree splits benefit from having multiple correlated features (e.g., RSI_5, RSI_7, RSI_9). When one feature has a noisy split point, a correlated feature provides an alternative path. Removing the "less important" correlated features eliminates this redundancy.

### 3. Optuna found fundamentally different (worse) hyperparameters

With 60 features, the best Optuna Sharpe per month was 0.05-0.14 (vs 0.4-0.5 with full features). The optimizer chose:
- Very short training_days (60 vs 450-500) — can't learn from longer history
- Low confidence thresholds (0.52 vs 0.72-0.85) — predictions barely above coin flip
- This means the model fundamentally cannot find signal with these features

### 4. Discovery bug masked worse performance in first run

The first run only used 38 features (global intersection across 760 symbols). The second run with 60 features was actually WORSE (Sharpe -0.41 vs +0.41). More features from the whitelist didn't help because the removed features were more important than any in the whitelist.

## Research Checklist Completed

| Category | Finding | Impact |
|----------|---------|--------|
| A. Feature Contribution | 59/185 features have importance ≤ 5; top 24 capture 50% | Motivated pruning hypothesis |
| C. Labeling | 54% long/46% short; SHORT 6pp better WR; only 18 timeouts with |ret|<1% | Ternary labeling not worth it |
| E. Trade Patterns | TP=32.2%, SL=51.2%; SHORT better; ETH 2.3x more PnL than BTC | Model is balanced, no structural issues |
| F. Statistical Rigor | WR above break-even p=0.0002; mean PnL p=0.017; Sharpe CI [0.03, 0.22] | **Signal is real but very noisy** |

## Quantitative Gap

- IS WR: 34.7%, break-even ~34.0%, gap: **0.7pp** (essentially random)
- IS Sharpe: -0.41 (negative = losing money)
- To close: would need WR ~43% (9pp improvement), which requires the full feature set

## lgbm.py Code Review

1. **Bug found and fixed**: `_discover_feature_columns()` was called without `symbols` parameter, causing it to scan all 760 parquet files. The intersection across all symbols yielded fewer features than BTC/ETH alone. Fixed by passing `symbols` from master DataFrame.
2. **Feature whitelist parameter works correctly** — filters after discovery as designed.
3. **No other issues found** in the pipeline.

## Exploration/Exploitation Tracker

Last 10 (iters 064-073): [X, E, X, E, E, X, E, E, E, E]
Exploration rate: 7/10 = 70%
Type: EXPLORATION (feature pruning)

## Lessons Learned

1. **Static feature importance ≠ walk-forward importance.** A single model trained on all IS data has completely different feature importance than rolling monthly models. Global importance reflects average utility across all time; monthly models need features that are useful in SPECIFIC time windows.

2. **Feature redundancy helps LightGBM.** Having multiple correlated features (RSI_5/7/9, SMA_20/50/100) provides alternative split paths. Pruning "redundant" features hurts because they serve as backup signals when the primary is noisy.

3. **The 185-feature set is NOT oversized.** With 11,454 IS samples and 185 features (62 samples/feature globally, ~24 per monthly window), the model operates at the edge of dimensionality constraints. But LightGBM's regularization (colsample_bytree, min_child_samples) handles this better than static pruning.

4. **Discovery bug**: the `_discover_feature_columns` should always pass trading symbols to avoid scanning 760+ parquet files. This fix should be kept for future iterations.

## Next Iteration Ideas

1. **EXPLORATION: Regression target** — Instead of binary classification (long/short), predict forward 8h return magnitude. Uses `objective="regression"` in LightGBM, trades based on sign and magnitude. This changes the loss function and the information content of labels (continuous returns vs binary direction). This is the most structural change remaining that hasn't been tried.

2. **EXPLORATION: Per-symbol models** — Train separate LightGBM for BTC and ETH, each with its own Optuna optimization. The models have different dynamics (ETH 2.3x more profitable per trade). Separate models can exploit symbol-specific patterns without interference.

3. **EXPLOITATION: Run baseline with all 185 features** — The current parquet has 185 features (vs the 106 the baseline used). Simply running the baseline configuration with 185 features (no pruning, no changes) may already be different from the baseline. This establishes a clean comparison point for future iterations.
