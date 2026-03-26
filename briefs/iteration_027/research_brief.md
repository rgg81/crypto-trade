# Research Brief: 8H LightGBM Iteration 027 — EXPLORATION

## 0. Data Split: OOS cutoff 2025-03-24.

## 1. Change: TP=8%/SL=4% (2x larger barriers, same 2:1 RR)
Bold parameter change (>2x = EXPLORATION per protocol).

### Rationale
The model works well on BTC+ETH at 4%/2%. Larger moves (8%/4%) may be even more structured — driven by major market events, institutional flows, macro catalysts. These are rarer but potentially more predictable.

Break-even WR is still 33.3% (same 2:1 RR). The question: does WR hold or improve at 8%/4%?

Iter 007 tested TP=5%/SL=2% (asymmetric) and WR dropped to 28% on 50 symbols. But that was pre-BTC+ETH. On BTC+ETH only, the model has much stronger signal.

## 2. Everything Else Unchanged
BTC+ETH, classification, timeout=4320, threshold 0.50-0.85, 12mo, 50 trials, seed 42.

## Exploration/Exploitation Tracker
Last 10: [X, X, E, X, X, X, X, X, **E**, **E**] → 3/10 = 30% ✓
