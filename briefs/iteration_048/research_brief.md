# Research Brief: 8H LightGBM Iteration 048 — EXPLORATION

## 0. Data Split: OOS cutoff 2025-03-24. Full data range.

## 1. Change: Balance class weights before LightGBM fit

### User Suggestion
Before calling model.fit(), scale sample_weights so sum(weights for shorts) ≈ sum(weights for longs). Currently `is_unbalance=True` handles count imbalance but NOT weight imbalance. If long-labeled candles tend to have higher weights (bigger moves → bigger weights), the model over-optimizes for longs.

### Implementation
Added `_balance_weights(y, w)` in optimization.py. Applied before every `model.fit()` call.

### Expected Impact
More balanced predictions between long/short. Currently SHORTS outperform LONGS (IS: SHORT 44.6% WR vs LONG 42.2%). Weight balancing may improve LONG accuracy.

## 2. Everything Else: iter 047 baseline config.
BTC+ETH, 24mo training, TP=8%/SL=4%, timeout=7d, threshold 0.50-0.85, seed 42.
