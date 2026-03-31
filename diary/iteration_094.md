# Iteration 094 Diary — 2026-03-31

## Merge Decision: NO-MERGE (EARLY STOP)

**Trigger**: Year 2022 PnL=-102.0%, WR=31.6%, 114 trades. Below break-even in first year of predictions.

**OOS cutoff**: 2025-03-24

## Hypothesis

Pruning features from 185 to 50 using MDA permutation importance would improve model stability and OOS generalization by raising the samples-per-feature ratio from 24 to 88.

## Configuration Summary

- OOS cutoff: 2025-03-24 (fixed)
- CV gap: 44 rows (no label leakage)
- **Features: 50** (MDA-pruned from 185, correlation-deduped)
- Model: LGBMClassifier binary, ensemble 5 seeds
- Walk-forward: monthly, 24mo window, 5 CV folds, 50 Optuna trials
- Execution: Dynamic ATR barriers TP=2.9×NATR_21, SL=1.45×NATR_21, cooldown=2

## Results: In-Sample (EARLY STOP — partial)

| Metric | Iter 094 | Baseline (093) |
|--------|----------|----------------|
| Sharpe | **-1.46** | +0.73 |
| Win Rate | 31.3% | 42.8% |
| Profit Factor | 0.71 | 1.19 |
| Max Drawdown | 150.5% | 92.9% |
| Total Trades | 115 (partial) | 346 |
| Net PnL | -104.5% | +150.2% |

No OOS results — early stopped before OOS period.

## Per-Symbol IS Performance

| Symbol | Trades | WR | Net PnL |
|--------|--------|----|---------|
| BTCUSDT | 55 | 30.9% | -41.7% |
| ETHUSDT | 60 | 31.7% | -62.8% |

Both below 33.3% break-even. The model has no directional signal with 50 features.

## Gap Quantification

WR is 31.3%, break-even is 33.3%, gap is **-2.0 pp**. TP rate is 20.0% (baseline 32.1%), SL rate is 63.5% (baseline 52.9%). The pruned model takes more SL hits (+10.6 pp) and fewer TP exits (-12.1 pp). To close this gap, the model needs features that were removed — the pruning was too aggressive.

## What Failed

1. **Aggressive pruning killed the signal.** 185→50 is a 73% feature reduction. The model lost features that carry genuine (if subtle) signal. The MDA methodology assumed features with low average importance are noise — but in a walk-forward context with monthly retraining, different features are important in different months.

2. **MDA computed on static reference model.** The reference model trained on full IS with fixed hyperparams differs fundamentally from the walk-forward monthly models with Optuna-optimized hyperparams. Features ranked low by the reference model may be critical for specific months.

3. **Correlated features provide complementary tree splits.** Even when two features have |r|>0.9 (e.g., RSI_14 and RSI_21), the tree model uses them differently — one for coarse splits, another for fine-tuning within leaves. Removing "redundant" features removes split opportunities.

4. **Optuna Sharpe overflow bug.** Seed 1001 in month 2023-01 selected a degenerate trial (Sharpe=8.9e14) with training_days=30, producing a model trained on only 180 samples. Not the primary cause of failure but compounded it.

## What We Learned

1. **Feature pruning from 185→50 is too aggressive.** The model needs more than 50 features to capture the signal. The "30-50 target" from the iteration plan may be too restrictive for this model architecture.

2. **MDA on a single reference model is unreliable.** Need walk-forward MDA (compute importance per monthly model, then aggregate) for reliable feature ranking.

3. **Correlation dedup is destructive for tree models.** Unlike linear models, tree ensembles benefit from having correlated features available for different split points. A |r|>0.9 threshold is too aggressive.

4. **The 185-feature baseline is not obviously over-parameterized.** Despite the low samples/feature ratio (24), the walk-forward retraining with Optuna's colsample_bytree (0.3-1.0) provides implicit feature selection. Removing features explicitly removed this flexibility.

## Exploration/Exploitation Tracker

Last 10 (iters 085-094): [E, E, E, X, E, E, E, X, E, **X**]
Exploration rate: 7/10 = 70%
Type: **EXPLOITATION** (feature count change only)

## MLP Diagnostics (AFML)

| Metric | Value |
|--------|-------|
| Deflated Sharpe Ratio (DSR) | N/A (early stop, no valid Sharpe to evaluate) |
| CV method | TimeSeriesSplit(n_splits=5, gap=44) |
| Label leakage | NONE (verified) |
| Feature discovery | Manual 50-feature list via MDA |

## Next Iteration Ideas

After an EARLY STOP, parameter-only changes are banned. Must propose structural changes.

1. **EXPLORATION: Conservative pruning — remove only harmful features.** Instead of pruning to 50, only remove the 3 features with MDA < -0.01 (trend_aroon_osc_50, trend_sma_cross_20_100, vol_bb_bandwidth_30) and the ~74 trivially redundant features (|r|>0.95). Target: ~100-110 features. This is a gentler approach that respects the tree model's need for split options.

2. **EXPLORATION: Walk-forward MDA.** Compute MDA per monthly model during the walk-forward backtest, aggregate across months. Features that are consistently important across time periods are reliable. This requires embedding MDA computation into `_train_for_month()`.

3. **EXPLORATION: Per-symbol models.** BTC and ETH showed different dynamics in iter 093 (BTC 33.3% WR vs ETH 50.0% OOS). Separate models could specialize and avoid the pooling problem.

4. **EXPLORATION: Fix the Optuna Sharpe overflow.** Add `if abs(sharpe) > 100: return -10.0` guard in `compute_sharpe_with_threshold()`. This is a bug fix, not a strategy change — should be done regardless.

## Lessons Learned

1. **Feature pruning must be conservative for tree models.** The 30-50 feature target is a guideline, not a dogma. LightGBM with `colsample_bytree` already does implicit feature selection per tree. Explicit pruning removes options the model may need.

2. **Static MDA is not walk-forward MDA.** A feature's importance on the full IS data does not reflect its importance in monthly windows. Use per-month MDA and aggregate.

3. **Correlation ≠ redundancy for trees.** Two features with r=0.95 provide different split point distributions. The tree uses both.
