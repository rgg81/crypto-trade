# Research Brief: 8H LightGBM Iteration 013

## 0. Data Split
- OOS cutoff: 2025-03-24. IS only for design. Walk-forward on full dataset.

## 1. Change: Reduce timeout from 3 days to 2 days (4320→2880 min)
BTC+ETH only (same as iter 010 baseline).

### Rationale
- Iter 010 had 487 OOS trades. More trades = better Sharpe (if WR holds).
- Shorter timeout means trades close faster, freeing the slot for new trades sooner.
- At 4320 min timeout, 1.6% of trades timed out in IS. Reducing to 2880 min may increase this to ~3%, but each timeout resolves faster.

### Research Checklist: E (Trade Patterns)
Timeout trades average +0.71% PnL in IS. Faster resolution means these small wins/losses contribute less, focusing the strategy on TP/SL outcomes.

## 2. Everything Else Unchanged
BTC+ETH, classification, TP=4%/SL=2%, confidence 0.50-0.65, 50 Optuna trials, seed 42.
