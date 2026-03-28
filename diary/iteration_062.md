# Iteration 062 Diary — 2026-03-28

## Merge Decision: NO-MERGE

OOS Sharpe -0.41 (negative). OOS PnL -28.4%. Extreme researcher overfitting (OOS/IS ratio -0.21).

**OOS cutoff**: 2025-03-24

## Hypothesis

Remove redundant features with |corr| > 0.95 to reduce dimensionality without IS-performance bias. Unlike iter 061's importance-based pruning, correlation dedup is agnostic to model performance.

## Configuration Summary
- OOS cutoff: 2025-03-24 (fixed)
- Labeling: triple barrier TP=8%, SL=4%, timeout=7 days
- Symbols: BTCUSDT + ETHUSDT (pooled)
- Features: **82** (24 removed via |corr| > 0.95 dedup)
- Walk-forward: monthly, 24mo training, 5 CV folds, 50 Optuna trials
- Random seed: 42

## Results: In-Sample

| Metric | Value | Baseline IS |
|--------|-------|-------------|
| Sharpe | **+1.99** | +1.60 |
| Win Rate | 45.7% | 43.4% |
| Profit Factor | 1.42 | 1.31 |
| Max Drawdown | 50.7% | 64.3% |
| Total Trades | 514 | 574 |

## Results: Out-of-Sample

| Metric | Value | Baseline OOS |
|--------|-------|-------------|
| Sharpe | **-0.41** | +1.16 |
| Win Rate | 35.7% | 44.9% |
| Profit Factor | 0.93 | 1.27 |
| Max Drawdown | 58.0% | 75.9% |
| Total Trades | 157 | 136 |
| OOS/IS Sharpe | -0.21 | 0.72 |

## What Happened

### Best IS ever, worst OOS ever

IS Sharpe 1.99 is the highest of any iteration. IS WR 45.7%, PF 1.42, MaxDD 50.7% — all better than baseline. But OOS completely collapsed: Sharpe -0.41, WR 35.7% (barely above break-even), PF 0.93 (losing money).

### Why correlation dedup increased overfitting

The hypothesis was that removing mathematically redundant features should be "safe" — the model can't learn anything new from `stat_return_5` that it can't learn from `mom_roc_5` (r=1.000). But:

1. **Correlated features serve as implicit regularization** for tree-based models. LightGBM's `colsample_bytree` (0.3-1.0) randomly subsets features per tree. With correlated features, even when one is excluded, its duplicate provides similar information. This prevents the model from becoming dependent on any specific feature.

2. **Removing duplicates concentrates learning**. With 82 unique features instead of 106 (including redundant copies), each feature gets more tree splits. The model fits IS patterns more precisely — hence IS Sharpe 1.99. But this precision is overfit to IS-specific patterns.

3. **The "redundancy" was protective**. Features like `stat_return_5` ≡ `mom_roc_5` appear identical, but having both helps LightGBM generalize because the random feature selection in each tree benefits from having multiple access points to the same information.

### Comparison to iter 061

| Metric | Iter 061 (50 feat) | Iter 062 (82 feat) | Baseline (106 feat) |
|--------|-------------------|-------------------|---------------------|
| IS Sharpe | 1.40 | 1.99 | 1.60 |
| OOS Sharpe | +0.51 | -0.41 | +1.16 |
| OOS/IS ratio | 0.36 | -0.21 | 0.72 |

Iter 061 (50 features) had OOS +0.51. Iter 062 (82 features) has OOS -0.41. The importance-based selection in 061 was LESS overfit than the correlation dedup in 062, despite being explicitly biased toward IS. This suggests the specific features removed matter more than the selection method.

## Quantifying the Gap

- OOS Sharpe: -0.41, strategy is UNPROFITABLE out-of-sample
- OOS WR: 35.7%, break-even ~34.2%, gap = +1.5pp only
- OOS PF: 0.93 — losing money
- Both BTC (-20.5%) and ETH (-7.9%) negative OOS

## Decision: NO-MERGE

OOS negative. Extreme overfitting.

## lgbm.py Code Review

No issues. Same feature_columns whitelist implementation as iter 061.

## Research Checklist

Completed 2 categories (A, F) — minimum for exploitation.

## Exploration/Exploitation Tracker

Last 10 (iters 053-062): [E, X, X, X, E, E, E, E, X, X]
Exploration rate: 4/10 = 40%
Type: EXPLOITATION (feature dedup)

## What Worked

- IS Sharpe 1.99 — best ever. IS MaxDD 50.7% — best ever. Shows the model CAN learn stronger patterns with fewer features.

## What Failed

- OOS completely collapsed. Correlation dedup removed protective redundancy.
- The "agnostic to IS performance" claim was wrong — removing features changes the optimization landscape, which indirectly biases toward IS.

## Next Iteration Ideas

Feature pruning is a dead end in its current form. Both importance-based (iter 061) and correlation-based (iter 062) introduced overfitting. The baseline's 106 features with natural redundancy provide the right level of regularization.

1. **Dynamic TP/SL via ATR** (EXPLORATION): Change the execution layer, not the features. Scale barriers by recent ATR to adapt to volatility. This is the most untested structural change.

2. **Prediction smoothing** (EXPLOITATION): Keep all 106 features but add majority vote of last 3 predictions. Reduces flip-flopping without changing the model.

3. **Confidence threshold range narrowing** (EXPLOITATION): Narrow from [0.50, 0.85] to [0.70, 0.85] based on baseline's typical optimal thresholds. Less Optuna noise.

## Lessons Learned

- **Feature redundancy = implicit regularization** for tree-based models. Correlated features provide multiple access points to the same information, preventing over-reliance on any single feature. This is a FEATURE, not a bug.
- **IS improvement ≠ OOS improvement** when modifying the feature space. The IS-OOS gap is the REAL signal; IS Sharpe alone is meaningless.
- **The baseline's 106 features are near-optimal** including their redundancy. The redundancy ratio (24 correlated pairs out of 106) is apparently the right amount for LightGBM's random feature sampling.
- **Pruning that improves IS always risks overfitting**. The only safe pruning would remove features that hurt BOTH IS and OOS — but identifying those requires OOS data, which we can't use.
