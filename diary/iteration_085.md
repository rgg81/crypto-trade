# Iteration 085 Diary — 2026-03-30

## Merge Decision: NO-MERGE (EARLY STOP)

OOS Sharpe -2.01 vs baseline +1.84. Early-stopped: Year 2025 PnL=-81.3%, WR=25.0%, 64 trades. Regression labeling catastrophically worse than binary classification.

**OOS cutoff**: 2025-03-24

## Hypothesis

Regression labeling (LGBMRegressor predicting `long_pnl - short_pnl`) would provide more information than binary classification by capturing move magnitude, enabling the model to express conviction through prediction size.

## Configuration Summary

- OOS cutoff: 2025-03-24 (fixed)
- **Model: LGBMRegressor** (was LGBMClassifier)
- **Target: long_pnl - short_pnl** (was binary {-1, 1})
- **Filter: |prediction| > magnitude_threshold** (was P(class) > confidence_threshold)
- Features: 113 (global intersection — baseline)
- Symbols: BTCUSDT, ETHUSDT (pooled)
- Walk-forward: monthly, 24mo window, 5 CV folds, 50 Optuna trials
- Ensemble: 3 seeds [42, 123, 789]
- Execution: Dynamic ATR barriers TP=2.9, SL=1.45, cooldown=2

## Results: In-Sample

| Metric | Iter 085 | Baseline (068) |
|--------|----------|----------------|
| Sharpe | +0.82 | +1.22 |
| WR | 43.5% | 43.4% |
| PF | 1.27 | 1.35 |
| MaxDD | 46.8% | 45.9% |
| Trades | 232 | 373 |

## Results: Out-of-Sample

| Metric | Iter 085 | Baseline (068) |
|--------|----------|----------------|
| Sharpe | **-2.01** | +1.84 |
| WR | **27.1%** | 44.8% |
| PF | **0.54** | 1.62 |
| MaxDD | **63.0%** | 42.6% |
| Trades | 48 | 87 |

### Per-Symbol OOS

| Symbol | Trades | WR | PnL |
|--------|--------|-----|-----|
| BTCUSDT | 23 | 26.1% | -23.9% |
| ETHUSDT | 25 | 28.0% | -30.6% |

## What Happened

**Regression labeling was a catastrophic failure.** The model's IS metrics were decent (Sharpe +0.82, WR 43.5%) but OOS was the worst result in the project's history — WR 27.1%, PF 0.54, net PnL -54.5%.

**The magnitude threshold was the problem.** Optuna tuned thresholds in the 2-7 range across months. These high thresholds filtered aggressively — only 48 OOS trades vs 87 for the baseline — but the surviving trades were LESS accurate, not more. The model's high-magnitude predictions were precisely wrong in OOS.

**Why regression failed**: The regression target (long_pnl - short_pnl) has extreme values at the boundaries (±12 for TP vs SL outcomes). LightGBM's regression tries to minimize MSE, which heavily weights these extreme values. The model over-fits to predicting WHEN extreme outcomes happen, but these patterns don't generalize. Binary classification is inherently more robust because it only predicts direction, not magnitude — the magnitude signal is noisy.

**IS was also weaker**: Sharpe 0.82 vs baseline 1.22, 232 trades vs 373. The regression model is less confident overall (fewer trades) and less accurate even in-sample.

## Quantifying the Gap

WR: 27.1% OOS, break-even 33.3%, gap **-6.2pp below break-even**. The model is worse than random. PF 0.54 — losing $0.46 for every $1 in gross profits. This is the widest gap to break-even of any iteration.

## Exploration/Exploitation Tracker

Last 10 (iters 076-085): [E, X, E, E, X, X(abandoned), E, E, **E**]
Exploration rate: 6/10 = 60%
Type: **EXPLORATION** (model type change: classification → regression)

## Research Checklist

Completed 4 categories: C (labeling — primary change), A (feature analysis — used baseline features), E (trade pattern analysis via forward return distributions), F (statistical analysis of return distributions).

## lgbm.py Code Review

The regression implementation is correct — `use_regression` flag properly routes to `optimize_and_train_regression()`, the prediction path works correctly (model.predict vs model.predict_proba), and the magnitude threshold logic is sound. The problem is not a bug — regression genuinely performs worse than classification for this task.

## Lessons Learned

1. **Binary classification > regression for this task.** The direction value (long_pnl - short_pnl) is dominated by extreme outcomes (±12 for TP/SL). LightGBM regression overfits to these extremes. Classification's simpler objective (direction only) is more robust.

2. **More information in the label ≠ better predictions.** The regression target contains more information (magnitude + direction) but the extra information is noise, not signal. The model wastes capacity trying to predict magnitude when it should focus on direction.

3. **The magnitude threshold creates a dangerous selection bias.** High-magnitude predictions correlate with the model's most extreme feature patterns. In OOS, these patterns change — making the model's most confident predictions the MOST wrong.

4. **The baseline's binary classification + confidence threshold is hard to beat.** Both feature changes (iters 083-084) and model changes (iter 085) failed. The baseline's approach is a local optimum that may require a fundamentally different strategy architecture (not just model swaps) to improve.

5. **IS Sharpe +0.82 with IS MaxDD 46.8% should have been a warning.** Both metrics are worse than baseline IS. The regression model doesn't even capture IS signal as well as classification.

## Next Iteration Ideas

**After 9 consecutive NO-MERGE (077-085), the entire LightGBM approach may be at its ceiling.**

1. **EXPLOITATION: Exact baseline reproduction** — Run the exact baseline config (iter 068) to verify the infrastructure changes from iters 084-085 (feature_columns, trading_symbols, use_regression) haven't introduced regressions when disabled. This is a sanity check before any further exploration.

2. **EXPLORATION: Ensemble classification + regression** — Instead of replacing classification with regression, use regression predictions as an additional feature for the classifier. Train LGBMRegressor on direction_value, then add its prediction as feature 114 for the LGBMClassifier. The classifier decides direction; the regressor provides magnitude context.

3. **EXPLORATION: Prediction smoothing / momentum** — Add the previous candle's prediction direction as a feature. The model currently predicts each candle independently, but consecutive predictions often flip direction. Smoothing would reduce noisy flip-flops.

4. **EXPLORATION: Fundamentally different model** — Consider XGBoost, CatBoost, or a simple logistic regression as alternatives. If LightGBM is at its ceiling, another model family might find different signal.
