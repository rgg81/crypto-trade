# Research Brief — Iteration 106

**Type**: EXPLORATION
**Hypothesis**: A heterogeneous ensemble (5 LightGBM + 1 XGBoost + 1 CatBoost) provides genuine directional diversity, unlike the 5 identical-seed LGBMs which agree >99% of the time (iter 104).

## Section 0: Data Split (Verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Section 1: Problem Statement

The 5-seed LightGBM ensemble provides NO directional diversity (iter 104: >99% direction agreement). Different gradient boosting frameworks (XGBoost, CatBoost) use fundamentally different algorithms:
- **LightGBM**: Leaf-wise growth, GOSS sampling, exclusive feature bundling
- **XGBoost**: Level-wise growth, histogram-based, different regularization
- **CatBoost**: Ordered boosting, symmetric trees, target statistics for categoricals

These algorithmic differences produce genuinely different split decisions, especially on borderline predictions where the direction is uncertain.

## Section 2: Research Analysis

### A. Feature Contribution (Category A)
No feature changes. Same 185 features. All three frameworks support the same numeric input.

### E. Trade Pattern Analysis (Category E)
The baseline has 42.8% IS WR / 42.1% OOS WR. With 2:1 RR, any improvement in WR translates directly to PnL. A heterogeneous ensemble that better identifies direction should improve WR.

### F. Statistical Rigor (Category F)
Ensembling different model types is a well-established technique for reducing variance without increasing bias. Each model has its own inductive bias — averaging reduces the impact of any single framework's systematic errors.

### H. Overfitting Audit (Category H)
XGBoost and CatBoost are NOT optimized by Optuna — they use translated LightGBM params. This means they add diversity without adding optimization degrees of freedom.

## Section 3: Proposed Change

Add `heterogeneous_ensemble: bool = False` parameter. When True, after training the 5 LGBMs, also train 1 XGBoost + 1 CatBoost with translated hyperparams. Total: 7 models, averaged equally.

**Param translation**: n_estimators, max_depth, learning_rate, subsample, colsample_bytree, reg_alpha/lambda are common across all three. Framework-specific params use each library's defaults.

**All other params identical to baseline.**
