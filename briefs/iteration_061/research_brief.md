# Research Brief — Iteration 061

**Type**: EXPLOITATION (feature pruning)
**Date**: 2026-03-28

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Hypothesis

Pruning 56 low-importance features (106 → 50) reduces noise in the feature space, allowing LightGBM and Optuna to find better hyperparameters. The bottom 56 features collectively account for only 20.8% of gain importance. Removing them reduces the effective dimensionality without losing meaningful signal.

## Research Analysis (2 Categories: A, F)

### A. Feature Contribution Analysis

Trained a single LightGBM on full IS period (BTC+ETH, 3-candle forward return as proxy label). Gain-based importance analysis:

- **Top 50 features**: 79.2% cumulative importance
- **Bottom 56 features**: 20.8% cumulative importance
- **39 features** have < 0.5% individual importance

Top feature groups by cumulative importance:
1. **Statistical** (autocorr, kurtosis, skew, returns): ~35% of total
2. **Mean Reversion** (zscore, pct_from_high/low, vwap_dist): ~18%
3. **Volatility** (hist_vol, taker_buy_ratio, natr, obv): ~16%
4. **Momentum** (roc, rsi, willr, mom): ~10%

Notable: trend features (ADX, Aroon, EMA/SMA crosses, Supertrend) are largely in the bottom 56. Bollinger Bands, MFI, CMF, and most RSI periods also pruned.

### F. Statistical Rigor

The feature-to-sample ratio improves from 106/4400 = 0.024 to 50/4400 = 0.011 — roughly halving effective dimensionality. This should:
- Reduce Optuna search space (fewer features → fewer tree split options)
- Improve cross-validation stability (less noise in each fold)
- Potentially improve generalization (less overfitting to noise features)

Risk: some pruned features may carry signal that's captured through interactions. LightGBM's `colsample_bytree` already provides implicit feature selection, so explicit pruning may be redundant.

## Design Specification

### What Changes
- `feature_columns` parameter whitelist with 50 features
- Reduced from 106 → 50 features

### What Stays the Same
- Classification (LGBMClassifier, binary, is_unbalance=True)
- TP=8%, SL=4%, timeout=7 days
- 24-month training, 50 Optuna trials, 5 CV folds
- Seed=42, BTC+ETH pooled
- Walk-forward monthly, yearly fail-fast
