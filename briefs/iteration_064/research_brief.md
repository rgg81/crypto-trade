# Iteration 064 — Research Brief

**Type**: EXPLOITATION
**Date**: 2026-03-28

## Section 0: Data Split (Verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24 (fixed, never changes)
```

- IS: all data before 2025-03-24
- OOS: all data from 2025-03-24 onward
- Walk-forward runs on full dataset; reporting layer splits at cutoff

## Hypothesis

**Remove `training_days` from the Optuna search space** to reduce seed variance.

Currently, Optuna optimizes `training_days` in the range [10, 500]. This allows different seeds to discover fundamentally different training window sizes — some using 10 days (~30 candles), others using 500 days (16 months). This creates high seed variance because models trained on different amounts of data produce different decision boundaries.

By disabling this parameter, all seeds will use the full 24-month training window consistently, which should:
1. Reduce OOS seed variance (current std 0.96 → target <0.5)
2. Maintain mean performance (all IS results from baseline are positive with full window)
3. Simplify the search space (10 → 9 Optuna dimensions)

## Evidence

### Seed variance is the #1 weakness

| Seed | IS Sharpe | OOS Sharpe |
|------|-----------|------------|
| 42   | +1.48     | +1.95      |
| 123  | +1.00     | +0.70      |
| 456  | +0.81     | +0.13      |
| 789  | +0.83     | +1.20      |
| 1001 | +1.46     | -0.78      |

OOS: mean +0.64, std 0.96. The spread from +1.95 to -0.78 is too large.
IS: mean +1.12, std 0.30. Much tighter — suggests variance comes from the optimization, not the data.

### training_days is a high-variance parameter

- Range [10, 500] spans 50x in data size
- 10 days = ~30 candles (8h) — insufficient for LightGBM
- 500 days = 16 months out of 24 — reasonable but arbitrary trim
- Different seeds → different TPE paths → different training_days → different models
- This is the only Optuna parameter that changes the TRAINING DATA itself (all others change the model)

### Trade pattern analysis supports the approach

IS and OOS trade patterns are consistent (a sign the model generalizes):
- SL rate: 50% IS vs 48% OOS
- TP rate: 33% IS vs 34% OOS
- Timeout rate: 17% IS vs 16% OOS
- Mean TP: 7.25% IS vs 7.98% OOS
- Mean SL: 4.00% IS vs 3.80% OOS

This consistency means the model's core signal is sound — the variance comes from optimization instability, not model inadequacy.

## Configuration

No changes from iter 063 baseline EXCEPT:
- **Remove**: `training_days` Optuna parameter (was range [10, 500])
- Training window: always full 24 months (set by `training_months=24`)
- All other parameters identical: TP=8%/SL=4% labeling, ATR execution (2.9/1.45), 50 trials, 5 CV folds, 106 features, BTC+ETH pooled

## Implementation Notes for QE

1. Add `optimize_training_window: bool = True` parameter to `LightGbmStrategy.__init__`
2. When `optimize_training_window=False`, pass `open_times=None` to `optimize_and_train()`
3. Also pass `train_end_ms=None` when disabled (no trimming)
4. Create `run_iteration_064.py` with `optimize_training_window=False`
5. Run seed 42 first; if profitable, run 4 more seeds

## Research Checklist

Categories completed: A (partial — no feature importance file, but feature set unchanged), E (trade patterns)

Not required after MERGE: B (symbols unchanged), C (labeling unchanged), D (features unchanged), F (not 3+ NO-MERGE)
