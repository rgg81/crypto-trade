# Iteration 019 Diary - 2026-03-26

## Merge Decision: NO-MERGE
OOS Sharpe -0.29 (baseline +1.33). 3 CV folds gave worse optimization.

## Results: OOS Sharpe -0.29, WR 36.1%, PF 0.97, 296 trades.

## Lessons Learned
- 5 CV folds is better than 3 for this data. The extra folds give more stable Sharpe estimates for Optuna, leading to better hyperparameter selection.
- The iter 016 baseline configuration (BTC+ETH, threshold 0.85, 5 CV, 12mo, 50 trials) is well-optimized.
