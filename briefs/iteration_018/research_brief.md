# Research Brief: 8H LightGBM Iteration 018

## 0. Data Split
- OOS cutoff: 2025-03-24. Walk-forward on full dataset.

## 1. Change: Add BNB (3 symbols: BTC+ETH+BNB)
With the 0.85 threshold ceiling, Optuna can be very selective per month. BNB adds a third liquid large-cap. IS WR 33.7% — above break-even. The high threshold should filter BNB to only confident trades.

## 2. Everything Else Unchanged
Classification, TP=4%/SL=2%, timeout=4320, threshold 0.50-0.85, 12mo, 50 trials, seed 42.
