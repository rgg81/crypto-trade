# Research Brief — Iteration 062

**Type**: EXPLOITATION (correlation-based feature dedup)
**Date**: 2026-03-28

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Hypothesis

Remove redundant features (|corr| > 0.95) to reduce dimensionality without IS-performance bias. Unlike iter 061's importance-based pruning, correlation dedup is agnostic to model performance — it removes mathematical redundancy only. This should reduce noise without introducing researcher overfitting.

## Research Analysis (2 Categories: A, F)

### A. Feature Contribution Analysis

Correlation analysis on IS data found 39 highly correlated pairs (|corr| > 0.95). Greedy removal produced 82 features (from 106). Key redundancies:
- `stat_return_X` ≡ `mom_roc_X` (mathematically identical: both are % change)
- `stat_log_return_X` ≈ `stat_return_X` (≈0.999 correlation for small returns)
- `vol_atr_5/7/10/14` all corr > 0.997 (kept `vol_atr_21` as the longest)
- `vol_range_spike_36/48/96` correlated with `vol_range_spike_24/72`
- `mom_rsi_7/9/14/21` correlated (kept `mom_rsi_5` and `mom_rsi_30` as extremes)

### F. Statistical Rigor

Feature/sample ratio: 82/4400 = 0.019 (vs baseline 0.024, vs iter 061's 0.011). Moderate reduction. The key advantage over iter 061: no IS-performance signal leaks into the selection criterion. All removed features have a kept near-duplicate that carries the same information.

## Design Specification

- 82 features (24 removed via corr > 0.95 dedup)
- Same classification, TP/SL, timeout, training, pooled BTC+ETH
- `feature_columns` whitelist with the 82 kept features
