# Research Brief: 8H LightGBM Iteration 030 — EXPLORATION

## 0. Data Split: OOS cutoff 2025-03-24.

## 1. Change: TP=6%/SL=3% (2:1, middle ground)
Iter 016 baseline: 4%/2% → OOS WR 41.6%, Sharpe +1.33
Iter 027: 8%/4% → OOS WR 46%, IS Sharpe -0.04

6%/3% is the midpoint. Same 2:1 RR (break-even 33.3%). Tests whether larger-than-4% moves improve WR while keeping SL manageable.

## 2. Everything Else Unchanged
BTC+ETH, classification, threshold 0.50-0.85, 12mo, 50 trials, seed 42.
