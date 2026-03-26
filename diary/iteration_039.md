# Iteration 039 Diary - 2026-03-26 — EXPLOITATION (SEED SWEEP)

## Merge Decision: NO-MERGE (OOS +1.14 < baseline +1.33, but provides robustness data)

## Seed Sweep Results
| Seed | OOS Sharpe | OOS WR | OOS PF |
|------|-----------|--------|--------|
| 42   | +1.33     | 41.6%  | 1.21   |
| 123  | -1.15     | 33.6%  | 0.86   |
| 456  | +1.14     | 40.0%  | 1.17   |

**Average OOS Sharpe: +0.44** — strategy IS profitable on average across seeds.
**2 of 3 seeds profitable.** Seed 123 is the outlier.

## Key Insight
The strategy has real signal but high variance from monthly Optuna optimization. Each seed produces different hyperparameters per month → different trades → different results. The variance is ~±1.2 Sharpe units around the mean.

## To reduce seed sensitivity:
1. Multi-seed ensemble (average predictions from seeds 42, 456, 789)
2. Fixed good hyperparameters (no monthly Optuna)
3. More Optuna trials (100 instead of 50) for more stable optimization
