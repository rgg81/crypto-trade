# Iteration 140 Diary

**Date**: 2026-04-06
**Type**: EXPLOITATION (Model A colsample_bytree restriction)
**Model Track**: Model A — implicit feature selection via colsample_bytree
**Decision**: **NO-MERGE** — OOS Sharpe -0.35 (complete collapse from +1.67). Restriction destroys Optuna co-optimization.

## Results

| Metric | IS | OOS |
|--------|-----|-----|
| Sharpe | +0.74 | -0.35 |
| WR | 41.9% | 37.1% |
| PF | 1.20 | 0.91 |
| Trades | 322 | 89 |

## Analysis

### colsample_bytree restriction backfires

Restricting colsample_bytree to 0.3-0.5 (from 0.3-1.0) was intended to provide implicit feature selection. Instead, it caused Model A to collapse. The mechanism:

1. **Optuna needs freedom**: When colsample_bytree can vary 0.3-1.0, Optuna co-optimizes it with other hyperparameters (num_leaves, max_depth, n_estimators). Different feature fractions pair with different tree structures.

2. **Restriction kills co-optimization**: Forcing colsample_bytree ≤ 0.5 removes the ability for Optuna to choose "use all features with simpler trees" or "use fewer features with deeper trees." The interaction is broken.

3. **Result**: Each tree sees fewer features but without the compensating hyperparameter adjustments. Trees become weaker individually, and the ensemble becomes less diverse (all trees limited similarly).

### ETH collapses, BTC holds steady

OOS per-symbol:
- BTC: WR 42.2% (was 42.1%) — unchanged
- ETH: WR 31.8% (was 55.9%) — **-24.1pp catastrophic drop**

ETH is the high-signal symbol. With restricted colsample_bytree, ETH's trees can't access the key features in combination. BTC's weaker signal is unaffected (it was already at its ceiling).

### This confirms the iter 094 lesson

Iter 094 proved that explicit feature pruning (185→50 features) destroys Optuna co-optimization for BTC/ETH. This iteration shows that **implicit pruning via colsample_bytree does the same thing**. The model is mature — any constraint on feature usage breaks the Optuna-tuned balance.

**Updated dead ideas**: Aggressive feature reduction on Model A (explicit OR implicit) doesn't work. The 196-feature count with 22.4 samples/feature ratio is acceptable because Optuna has tuned around it.

### Gap quantification

Model A current: WR 48.6% OOS (baseline iter 138). Break-even 33.3%. Gap **+15.3pp**. 
Iter 140: WR 37.1% OOS. Gap collapsed to **+3.8pp**. 

## Label Leakage Audit

- CV gap = 44 (22 × 2). Verified.

## Research Checklist

- **A (Feature Contribution)**: Tested colsample_bytree restriction as implicit pruning. Result: fails, same as explicit pruning in iter 094. Model A's feature set is locked in.
- **E (Trade Pattern)**: ETH OOS WR collapsed from 55.9% to 31.8%. The restriction specifically harms the high-signal symbol.

## lgbm.py Code Review

Added `colsample_bytree_max` parameter to `LightGbmStrategy` constructor, passed through `optimize_and_train` to `_objective`. Code is clean. The parameter exists for future use but defaults to 1.0 (no restriction) — which is what Model A needs.

## Exploration/Exploitation Tracker

Last 10 iterations: [E, E, E, E, X, E, X, X, E, **X**] (iters 131-140)
Exploration rate: 5/10 = 50%

## Next Iteration Ideas

1. **Increase n_estimators max** (EXPLOITATION) — Optuna's n_estimators range is 50-500. With 196 features and low ratio, more trees could help. Test raising the range to 500-1000. Each additional tree sees a random feature subset, providing natural ensemble regularization.

2. **Cross-asset features for Model A** (EXPLORATION) — Add LINK/BNB returns as features. Pipeline work required: modify parquet generation to include xlink_* and xbnb_* features.

3. **ATR multiplier variations for Model A** (EXPLOITATION) — Current is 2.9x/1.45x. Test 3.2x/1.6x or 2.5x/1.25x. Wider barriers might further improve ETH's signal.

4. **Wider confidence threshold range** (EXPLOITATION) — Optuna's confidence_threshold range is 0.50-0.85. Extending to 0.50-0.90 or 0.55-0.90 might let the model select even higher-quality trades.
