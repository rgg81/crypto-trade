# Iteration 006 Diary - 2026-03-25

## Merge Decision: NO-MERGE

OOS Sharpe worsened -1.91→-2.34. Win rate dropped 32.9%→32.6%. More Optuna trials didn't help.

## Hypothesis

Doubling Optuna trials from 50 to 100 would improve hyperparameter optimization, particularly the confidence threshold, pushing WR past break-even.

## Configuration Summary

- OOS cutoff: 2025-03-24 (fixed)
- **Change**: n_trials=100 (from 50)
- Symbols: Top 50 (unchanged), TP=4%/SL=2%, seed 42

## Results: Out-of-Sample

| Metric | Value | Baseline OOS |
|--------|-------|--------------|
| Sharpe | -2.34 | -1.91 |
| MaxDD | 999% | 997% |
| Win Rate | 32.6% | 32.9% |
| PF | 0.91 | 0.92 |
| Trades | 6,638 | 6,831 |

## Overfitting Diagnostics

| Metric | IS | OOS | Ratio |
|--------|-----|-----|-------|
| Sharpe | -4.28 | -2.34 | 0.55 |
| WR | 30.7% | 32.6% | 1.06 |

IS/OOS ratio of 0.55 passes the 0.5 gate for the first time — but absolute metrics are worse.

## What Failed

- More trials = marginal overfitting to CV objective, slightly worse OOS
- WR dropped 0.3pp — within noise but in the wrong direction
- The hyperparameter space at 50 trials was already adequately explored

## Next Iteration Ideas

1. **BTC regime filter**: Only trade when BTC ADX > threshold. Requires code changes but addresses the fundamental issue of trading in unpredictable market conditions.
2. **Asymmetric barriers**: TP=5%/SL=2% (2.5:1 RR). Break-even drops to ~29%. At 32.9% WR, this would be PROFITABLE.
3. **Per-symbol models for top 5**: BTC, ETH, SOL, XRP, DOGE have the most data. Individual models might capture asset-specific patterns the pooled model misses.

## Lessons Learned

- 50 Optuna trials is sufficient for this search space. More trials don't help and may slightly overfit.
- The TPE sampler converges quickly with 12 dimensions. Additional trials explore noise.
- The 1.1pp gap to break-even won't close with optimization improvements — it requires structural changes.
