# Research Brief: 8H LightGBM Iteration 024 (EXPLORATION)

## 0. Data Split: OOS cutoff 2025-03-24.

## 1. Change: Regression mode on BTC+ETH (exploration)
Iter 009 tested regression on 50 symbols — failed (Sharpe -3.73). But BTC+ETH wasn't tested with regression. BTC has the strongest directional signal (50.6% OOS WR in classification). Regression on BTC+ETH may find even stronger patterns by predicting return magnitude.

### Key difference from iter 009
- Only 2 symbols (was 50) → model focuses on BTC/ETH dynamics
- min_return_threshold optimized 0.5-3.0% → selectivity similar to classification's 0.85 confidence

## 2. Everything Else Unchanged
TP=4%/SL=2%, timeout=4320, 12mo training, 50 trials, 5 CV, seed 42.
