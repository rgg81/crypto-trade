# Research Brief: 8H LightGBM Iteration 021

## 0. Data Split
- OOS cutoff: 2025-03-24. Walk-forward on full dataset.

## 1. Change: training_months=18 (from 12)
Combining longer training (which improved IS in iter 014) with the proven 0.85 threshold ceiling. Iter 014 tested 24mo at 0.65 threshold on 50 symbols — IS Sharpe improved from -1.20 to -0.02. Now testing 18mo at 0.85 threshold on BTC+ETH.

### Rationale
- 12mo training: first test month (Jan 2021) has only 12 months of BTC+ETH data (~730 candles). Sparse.
- 18mo training: first test month shifts to Jul 2021, with 18 months (~1095 candles). More data for early months.
- 18mo is a compromise between 12mo (current) and 24mo (iter 014, which hurt OOS).

## 2. Everything Else Unchanged
BTC+ETH, TP=4%/SL=2%, timeout=4320, threshold 0.50-0.85, 50 trials, seed 42.
