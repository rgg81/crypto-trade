# Research Brief: 8H LightGBM Iteration 014

## 0. Data Split
- OOS cutoff: 2025-03-24. Walk-forward on full dataset.

## 1. Change: training_months=24 (from 12)
BTC+ETH, timeout=4320 (same as baseline iter 010).

### Rationale
With only 2 symbols, each month has ~190 training candles at 12-month window. Doubling to 24 months gives ~380 candles — more data for LightGBM to find patterns. The walk-forward still prevents lookahead.

## 2. Everything Else Unchanged
BTC+ETH, classification, TP=4%/SL=2%, timeout=4320, confidence 0.50-0.65, 50 trials, seed 42.
