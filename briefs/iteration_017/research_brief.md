# Research Brief: 8H LightGBM Iteration 017

## 0. Data Split
- OOS cutoff: 2025-03-24. Walk-forward on full dataset.

## 1. Change: Widen confidence threshold to 0.50-0.95
Continue the selectivity trend: 0.65→0.75→0.85→0.95.

### Risk
At 0.95, very few candles may pass. Could drop below 50 OOS trades. But each widening so far has improved metrics without trade count issues.

## 2. Everything Else Unchanged
BTC+ETH, TP=4%/SL=2%, timeout=4320, 12mo, 50 trials, seed 42.
