# Research Brief: 8H LightGBM Iteration 006

## 0. Data Split & Backtest Approach

- OOS cutoff date: 2025-03-24 (project-level constant)
- IS data only for design decisions; walk-forward on full dataset
- Monthly retraining, 12-month window, reports split at cutoff

## 1. Change from Iteration 004 (current baseline)

**Single variable change: increase Optuna trials from 50 to 100 per month.**

### Rationale

With 50 trials, Optuna searches a space of 12 dimensions (confidence_threshold + training_days + 9 LightGBM hyperparams). At 50 trials, the search is sparse — TPE sampler may not converge. Doubling to 100 gives more exploration of promising regions, particularly for the confidence threshold (0.50–0.65) which is the primary trade quality filter.

The win rate is 1.1pp from break-even. Better optimization could close this gap without any structural changes.

### Trade-off

Compute time will roughly double (~12,000s vs ~6,000s). Acceptable for a one-time experiment.

## 2. Everything Else Unchanged

Top 50 symbols, TP=4%/SL=2%, all 106 features, confidence threshold 0.50–0.65, monthly walk-forward, seed 42.
