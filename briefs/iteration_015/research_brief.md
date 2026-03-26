# Research Brief: 8H LightGBM Iteration 015

## 0. Data Split
- OOS cutoff: 2025-03-24. Walk-forward on full dataset.

## 1. Change: Widen confidence threshold range to 0.50-0.75
BTC+ETH, all else same as iter 010.

### Rationale
The confidence threshold controls trade selectivity. Current range 0.50-0.65 may be too narrow — Optuna might benefit from a higher ceiling. At 0.70-0.75, only the most confident predictions trade. With BTC+ETH, this could produce fewer but much higher-quality trades.

Iter 012 (BTC-only) showed 40.7% WR with 189 trades — high selectivity works. This iteration tries to achieve similar selectivity through the threshold rather than symbol restriction.

## 2. Everything Else Unchanged
BTC+ETH, classification, TP=4%/SL=2%, timeout=4320, training_months=12, 50 trials, seed 42.
