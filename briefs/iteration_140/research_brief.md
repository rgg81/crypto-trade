# Iteration 140 Research Brief

**Type**: EXPLOITATION (Model A colsample_bytree restriction)
**Model Track**: Model A (BTC+ETH) — implicit feature selection via colsample_bytree
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Motivation

Model A has 196 features with ~4,400 training samples (ratio 22.4). This is dangerously low — the skill recommends ratio > 50. Explicit feature pruning was catastrophic in iter 094 (destroyed Optuna co-optimization, IS Sharpe -1.46).

**Alternative**: restrict `colsample_bytree` to 0.3-0.5 (from 0.3-1.0). Each tree only sees 30-50% of features, forcing implicit feature selection. The model learns to rely on the most informative ~60-100 features per tree split, without removing any features from the pool. This preserves Optuna co-optimization while achieving regularization.

**Hypothesis**: With colsample_bytree capped at 0.5, each tree sees at most 98 of 196 features. This effectively doubles the samples/feature ratio per tree from 22.4 to 44.9 — closer to the 50 threshold. The ensemble of trees (n_estimators typically 200-400) still explores all 196 features collectively, but each individual tree is more regularized.

## Research Checklist Categories

### A. Feature Contribution Analysis
The colsample_bytree restriction is a form of implicit feature selection (A1 variant). Instead of pruning features, we restrict how many each tree can see. This achieves similar regularization without the risks of explicit pruning.

### E. Trade Pattern Analysis
After the backtest, compare exit reason breakdown and WR patterns vs iter 138 baseline to assess if the restriction helps or hurts trade quality.

## Configuration

| Parameter | Baseline (iter 138 Model A) | Iter 140 |
|-----------|----------------------------|----------|
| colsample_bytree range | 0.3-1.0 (Optuna) | **0.3-0.5** |
| All other params | Same | Same |

**Single variable changed**: colsample_bytree upper bound from 1.0 to 0.5.

This is a Model A standalone test. If it improves, run full A+C+D portfolio as follow-up.
