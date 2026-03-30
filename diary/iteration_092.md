# Iteration 092 Diary — 2026-03-31

## Merge Decision: NO-MERGE (EARLY STOP)

OOS Sharpe -0.28 (unprofitable). 106 features + gap=44 cannot sustain profitability. The 9 extra features present in iter 091 (115 features) are load-bearing.

**OOS cutoff**: 2025-03-24

## Hypothesis

Replicate baseline iter 068 exactly (106 features from original 6 groups) + gap=44. Isolate the feature count confound from iter 091.

## Configuration Summary

- OOS cutoff: 2025-03-24 (fixed)
- CV gap: 44 rows (22 candles × 2 symbols)
- **Features: 106** (regenerated with original 6 groups, global intersection)
- Model: LGBMClassifier binary, ensemble [42, 123, 789]
- Walk-forward: monthly, 24mo window, 5 CV folds, 50 Optuna trials
- Execution: Dynamic ATR barriers TP=2.9, SL=1.45, cooldown=2

## Results

| Metric | Iter 092 (106 feat) | Iter 091 (115 feat) | Baseline (106 feat, no gap) |
|--------|---------------------|---------------------|-----------------------------|
| OOS Sharpe | **-0.28** | +0.89 | +1.84 |
| OOS WR | 42.1% | 40.6% | 44.8% |
| OOS PF | 0.93 | 1.25 | 1.62 |
| OOS MaxDD | 33.4% | 30.5% | 42.6% |
| OOS Trades | 76 | 96 | 87 |

## What Happened

With honest CV (gap=44), the original 106-feature set is insufficient. The model cannot find profitable hyperparameters. The 9 extra features in iter 091 (from expanded trend/volatility/interaction/calendar groups) provide enough additional signal to sustain profitability.

## Exploration/Exploitation Tracker

Last 10 (iters 083-092): [E, E, E, E, E, X, E, E, E, **X**]
Exploration rate: 8/10 = 80%
Type: **EXPLOITATION** (baseline replication with feature control)

## Next Iteration Ideas

1. **EXPLOITATION: 115 features + gap=44 + 5-seed ensemble** — Validate iter 091's OOS +0.89 is not seed-dependent. Increase ensemble from 3 to 5 seeds.

## Lessons Learned

1. **Features matter more than expected with honest CV.** 106→115 features flips OOS from -0.28 to +0.89. The expanded feature modules (interaction, calendar, trend additions) carry genuine signal.
2. **The baseline's OOS +1.84 relied on leaked CV + lucky feature set.** With honest CV and original features, the strategy is unprofitable.
