# Research Brief: 8H LightGBM Iteration 020

## 0. Data Split
- OOS cutoff: 2025-03-24. Walk-forward on full dataset.

## 1. Change: 7 CV folds (from 5)
Iter 019 showed 3 folds was worse. Try 7 folds for more stable Sharpe estimates in Optuna. More folds = less variance in hyperparameter evaluation = potentially better model selection.

## 2. Everything Else Unchanged
BTC+ETH, TP=4%/SL=2%, timeout=4320, threshold 0.50-0.85, 12mo, 50 trials, seed 42.
