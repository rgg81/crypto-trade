# Research Brief: 8H LightGBM Iteration 012

## 0. Data Split
- OOS cutoff: 2025-03-24. IS only for design. Walk-forward on full dataset.

## 1. Change: BTC-Only Model
From BTC+ETH (iter 010) to BTCUSDT only.

### Evidence
- BTC had 50.6% OOS WR (87 trades) in iter 004's 50-symbol backtest
- In iter 010 (BTC+ETH), overall WR was 38.6% — but ETH may be dragging BTC down
- BTC IS WR was 37.7% — highest of any symbol in IS
- A BTC-only model gets 100% of training focused on BTC dynamics

### Risk
- Very few trades (~87 OOS from iter 004 estimates). May not reach 50 minimum.
- Single-asset concentration risk.

## 2. Everything Else Unchanged
Classification, TP=4%/SL=2%, confidence 0.50-0.65, 50 Optuna trials, seed 42.
