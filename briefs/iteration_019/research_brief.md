# Research Brief: 8H LightGBM Iteration 019

## 0. Data Split
- OOS cutoff: 2025-03-24. Walk-forward on full dataset.

## 1. Change: 3 CV folds (from 5)
With only ~190 candles per month for 2 symbols, 5-fold CV creates very small validation sets. 3 folds give ~63 validation candles each (vs ~38 with 5 folds), reducing variance in the Sharpe estimate.

## 2. Everything Else Unchanged
BTC+ETH, TP=4%/SL=2%, timeout=4320, threshold 0.50-0.85, 12mo, 50 trials, seed 42.
