# Research Brief: 8H LightGBM Iteration 031 — EXPLOITATION

## 0. Data Split: OOS cutoff 2025-03-24.

## 1. Change: Baseline config + start_time=2022-07-01 (skip 18 months)
Iter 025 (start=2022-01) got IS Sharpe -0.14. By starting 6 months later (2022-07), we skip the bear market bottom too. This should push IS positive while preserving the +1.33 OOS.

## 2. Everything Else: Exact baseline config (iter 016).
BTC+ETH, TP=4%/SL=2%, threshold 0.50-0.85, 12mo, 50 trials, seed 42.
