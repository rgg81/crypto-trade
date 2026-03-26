# Iteration 009 Diary - 2026-03-26

## Merge Decision: NO-MERGE

OOS Sharpe -3.73 (worse than -1.91). WR 31.6% (worse than 32.9%). Regression approach didn't improve over classification.

## Hypothesis

Switch from LGBMClassifier to LGBMRegressor, predicting forward 3-candle (24h) return. Trade only when |predicted_return| > threshold. This fundamentally changes the model formulation.

## Configuration Summary

- OOS cutoff: 2025-03-24 (fixed)
- **Change**: mode="regression", regression_horizon=3, min_return_threshold Optuna [0.5, 3.0]
- Symbols: Top 50, TP=4%/SL=2%, 50 Optuna trials, seed 42

## Results: Out-of-Sample

| Metric | Value | Baseline |
|--------|-------|----------|
| Sharpe | -3.73 | -1.91 |
| WR | 31.6% | 32.9% |
| PF | 0.86 | 0.92 |
| Trades | 4,638 | 6,831 |
| MaxDD | 935% | 997% |

IS/OOS ratio: 1.06 — perfect consistency, uniformly bad.

## Research Checklist: A, C, E, F (from iter 008)

## Gap Quantification

WR 31.6%, break-even 33.3%, gap 1.7pp. Regression did not close the gap.

## What Failed

- Regression predicts return magnitude but still can't reliably predict direction
- The forward 3-candle return target doesn't align with TP/SL barrier exits
- The positive CV Sharpe values in early trials didn't generalize

## lgbm.py Code Review

- Added dual-mode support (classification/regression) — clean implementation
- Regression target computation uses per-symbol forward scanning (correct, no cross-symbol leakage)
- get_signal() uses model.predict() for regression, predict_proba() for classification
- Weight proportional to |predicted_return| (capped at 100)
- Compute of regression targets in _train_for_month is slow (O(n*h) per symbol) — could be vectorized

## Next Iteration Ideas

1. **Per-symbol BTC/ETH models**: BTC had 50.6% OOS WR in iter 004. A dedicated model for BTC alone with all features focused on BTC dynamics. This isolates the strongest signal.
2. **Regression with barrier-aligned target**: Instead of raw forward return, use the ACTUAL triple-barrier outcome as regression target (TP→+4, SL→-2, timeout→actual return). This aligns model training with execution.
3. **Short-only + top 15**: Combine the two strongest findings (short advantage + liquid symbols)
4. **Add calendar features**: Hour-of-day was 2.6pp spread (07:00 vs 23:00 UTC). A simple calendar feature could help.

## Lessons Learned

- Switching from classification to regression is not sufficient when the underlying features can't predict direction. The model type changes the problem formulation but doesn't create signal that isn't there.
- The model needs features that contain directional information, not just magnitude. Current features (volume, trend, statistics) may describe market STATE but not reliably predict DIRECTION.
