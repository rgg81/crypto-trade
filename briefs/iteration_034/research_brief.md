# Research Brief: 8H LightGBM Iteration 034 — EXPLORATION

## 0. Data Split: OOS cutoff 2025-03-24. Full data range.

## 1. Change: Simplified macro features (just 2, from 13 in iter 033)

### Lesson from iter 033
13 macro features caused overfitting (IS worsened -0.96 → -1.77). Too many features diluted signal.

### This iteration: only 2 targeted features
- `macro_dd_from_ath`: Drawdown from all-time high. Directly captures bear market depth.
- `macro_return_90d`: 90-day rolling return. Captures bull/bear trend regime.

These 2 features directly address the root cause: in 2022, the model went long 156 times (27.6% WR) in a -65% BTC year because it had NO market-cycle context.

## 2. Everything Else Unchanged
BTC+ETH, TP=4%/SL=2%, timeout=4320, threshold 0.50-0.85, 12mo, 50 trials, seed 42.
