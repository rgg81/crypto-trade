# Research Brief: 8H LightGBM Iteration 022

## 0. Data Split
- OOS cutoff: 2025-03-24. Walk-forward on full dataset.

## 1. Change: training_months=24 with 0.85 threshold
Iter 014 (24mo, 0.65 thresh, 50 syms) got IS Sharpe -0.02 (best IS ever).
Iter 016 (12mo, 0.85 thresh, BTC+ETH) got OOS Sharpe +1.33 (best OOS ever).
Combining: 24mo training + 0.85 threshold + BTC+ETH.

## 2. Everything Else Unchanged
BTC+ETH, TP=4%/SL=2%, timeout=4320, 50 trials, 5 CV, seed 42.
