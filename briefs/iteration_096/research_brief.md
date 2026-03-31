# Iteration 096 — Research Brief

**Type**: EXPLOITATION
**Date**: 2026-03-31
**Previous**: Iter 095 (NO-MERGE, EARLY STOP — conservative pruning also failed)

## Section 0: Data Split (verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

## Hypothesis

The Sharpe overflow bug (discovered in iter 094) causes Optuna to occasionally select degenerate trials with training_days=30 and Sharpe=1e15. The fix (|Sharpe|>100 → -10.0) was cherry-picked to main in iter 095 but was confounded with feature pruning. This iteration tests the fix in isolation — identical to baseline except for the bug fix.

**Single variable changed**: Sharpe overflow guard in compute_sharpe_with_threshold.

## Configuration

Identical to iter 093 (baseline):
- Symbols: BTCUSDT + ETHUSDT
- Training: 24 months, walk-forward monthly
- Features: **185** (full symbol-scoped discovery, NO pruning)
- Labeling: TP=8%, SL=4%, timeout=7 days, dynamic ATR barriers
- CV: 5 folds, gap=44, 50 Optuna trials
- Ensemble: 5 seeds [42, 123, 456, 789, 1001]
- Cooldown: 2 candles

**Only change**: Sharpe overflow guard

## Expected Outcome

Results should be very close to baseline (OOS Sharpe ~1.01). The bug only triggered in edge cases (1 month, 1 seed). Improvement would be marginal but demonstrates correctness.
