# Research Brief: 8H LightGBM Iteration 016

## 0. Data Split
- OOS cutoff: 2025-03-24. Walk-forward on full dataset.

## 1. Change: Widen confidence threshold to 0.50-0.85
Iter 015 widened from 0.50-0.65 to 0.50-0.75 and improved all metrics. Continue the trend.

### Research Checklist (E: Trade Patterns)
Iter 015: 314 OOS trades (~29/month). At 0.85 threshold ceiling, trades could drop to ~150-200. Still above 50 minimum if model is confident enough.

### Checklist (F: Statistical Rigor)
With 314 trades at 39.2% WR, 95% CI ≈ [34%, 44%]. Break-even at 33.3% — CI excludes break-even on the low end. Signal is real but moderate sample size.

## 2. Everything Else Unchanged
BTC+ETH, classification, TP=4%/SL=2%, timeout=4320, 12mo training, 50 trials, seed 42.
