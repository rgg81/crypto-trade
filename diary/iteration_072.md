# Iteration 072 Diary — 2026-03-28

## Merge Decision: NO-MERGE (EARLY STOP)

Year 2025 PnL -3.3% (WR 39.1%). OOS Sharpe +0.13 vs baseline +1.84. Calendar features hurt.

**OOS cutoff**: 2025-03-24

## Hypothesis

Add 2 calendar features (hour_of_day, day_of_week) — minimal dimensionality (106→108).

## Results

| Metric | Iter 072 | Baseline (068) |
|--------|----------|----------------|
| IS Sharpe | +0.99 | +1.22 |
| IS MaxDD | 50.9% | 45.9% |
| OOS Sharpe | +0.13 | +1.84 |
| OOS MaxDD | 48.4% | 42.6% |
| OOS/IS ratio | 0.14 | 1.50 |

## What Happened

Calendar features (hour, day of week) degraded OOS by 93%. The OOS/IS ratio of 0.14 indicates severe researcher overfitting — the model learned to exploit time-of-day patterns in IS that don't generalize.

With only 3 possible hour values (0/8/16) on 8h candles, the model can trivially overfit to "trade at hour X" patterns. These are spurious correlations.

## Exploration/Exploitation Tracker

Last 10 (iters 063-072): [E, X, E, X, E, E, X, E, E, E]
Exploration rate: 6/10 = 60%
Type: EXPLORATION (calendar features)

## Lessons Learned

1. **Calendar features with low cardinality overfit.** 3 hours × 7 days = 21 unique combinations. The model memorizes these.
2. **5 consecutive NO-MERGEs since iter 068.** The baseline is resistant to incremental changes. Need structural shifts.
3. **Feature changes consistently fail** (iters 070, 072). The 106-feature baseline is well-tuned.

## Next Iteration Ideas

1. **EXPLORATION: Ternary labeling** — Add "neutral" class for timeout trades with |return| < 1%. Reduces noise in labels.
2. **EXPLORATION: Regression target** — Predict forward return magnitude instead of direction. Fundamentally different model.
3. **EXPLOITATION: Increase Optuna trials** (75 or 100) — More budget for hyperparameter search.
