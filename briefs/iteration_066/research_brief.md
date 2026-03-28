# Iteration 066 — Research Brief

**Type**: EXPLOITATION
**Date**: 2026-03-28

## Section 0: Data Split (Verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24 (fixed, never changes)
```

## Hypothesis

**Double Optuna trials from 50 to 100** to improve optimization convergence and reduce seed variance.

The baseline (iter 063) has OOS seed variance of std=0.96 (seeds range from -0.78 to +1.95). This variance likely comes from the 50-trial Optuna search not fully converging — different seeds explore different regions of the 10-dimensional hyperparameter space, finding different local optima.

With 100 trials, the TPE sampler has twice as many iterations to converge on the global optimum, which should produce more consistent parameter sets across seeds.

## Evidence

### Seed variance is the primary weakness

Baseline (iter 063) seed sweep:

| Seed | IS Sharpe | OOS Sharpe |
|------|-----------|------------|
| 42   | +1.48     | +1.95      |
| 123  | +1.00     | +0.70      |
| 456  | +0.81     | +0.13      |
| 789  | +0.83     | +1.20      |
| 1001 | +1.46     | -0.78      |

IS std=0.30, OOS std=0.96 — the optimization is less stable OOS.

### Recent iterations confirm model architecture is robust

- Iter 064: removing training_days broke the model → training_days is essential
- Iter 065: ATR labeling degraded signal quality → fixed labeling is optimal
- The 106-feature, pooled, fixed-label, ATR-execution architecture is proven

### 100 trials is standard for TPE

In 10-dimensional space (9 LightGBM params + training_days + confidence_threshold), TPE typically needs 50-100 trials for good convergence. Going from 50 to 100 doubles compute but should significantly improve the quality of found parameters.

## Configuration

All parameters identical to iter 063 baseline EXCEPT:
- **`n_trials`: 50 → 100** (doubled)
- Everything else: 24mo training, 5 CV, 106 features, BTC+ETH pooled, ATR execution (2.9/1.45)

## Expected Impact

- More consistent Sharpe across seeds (lower std)
- Similar or slightly better mean OOS Sharpe
- Runtime approximately doubles (~20min → ~40min per seed)

## Research Checklist

After 2 consecutive NO-MERGE (not yet 3+), minimum 2 categories:
- **A (Features)**: Unchanged from baseline — 106 features proven optimal (iters 061-062)
- **E (Trade Patterns)**: Analyzed in iter 064 — patterns consistent IS/OOS, no actionable changes

No feature, labeling, or architecture changes needed. This is a pure optimization quality improvement.
