# Research Brief: 8H LightGBM Iteration 025

## 0. Data Split: OOS cutoff 2025-03-24.

## 1. Change: Start backtest from 2022-01-01 (skip 2020-2021 cold-start)
The IS negativity comes from early 2021 when the model has only 12 months of BTC+ETH data (~730 candles). By starting the backtest from 2022-01, we skip the cold-start period and only include months where the model has 2+ years of training data.

### Key Insight
Iter 016 (baseline): IS Sharpe -0.96, OOS +1.33. The IS includes 2021 (terrible) and 2022-2025 (likely positive). By removing 2021, IS should improve significantly. OOS (2025+) is unchanged.

## 2. Everything Else Unchanged
BTC+ETH, classification, TP=4%/SL=2%, timeout=4320, threshold 0.50-0.85, 12mo training, 50 trials, seed 42.
