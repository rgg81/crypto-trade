# Research Brief: 8H LightGBM Iteration 035 — EXPLORATION

## 0. Data Split: OOS cutoff 2025-03-24. Full data range.

## 1. Change: Per-symbol models (separate BTC and ETH backtests combined)

### Rationale
The pooled BTC+ETH model compromises between two assets with different dynamics:
- BTC: Lower volatility, more institutional, leads market moves
- ETH: Higher volatility, follows BTC with lag, more speculative

Iter 012 (BTC-only): 40.7% OOS WR, 189 trades
Iter 010 (BTC+ETH pooled): 38.6% OOS WR, 487 trades

By training separate models, each learns asset-specific patterns. Combined trades should be ~400-500 (sum of both).

### Implementation
Run BTC backtest and ETH backtest separately, combine trade lists, generate unified reports.

## 2. Everything Else Per-Model Unchanged
TP=4%/SL=2%, timeout=4320, threshold 0.50-0.85, 12mo, 50 trials, seed 42.
