# Iteration 028 Diary - 2026-03-26 — EXPLORATION

## Merge Decision: NO-MERGE
OOS Sharpe -0.16 < baseline +1.33. Asymmetric 8%/2% failed — SL too tight for TP target.

## Type: EXPLORATION (asymmetric 4:1 barriers)

## Results
| Metric | Value | Baseline |
|--------|-------|----------|
| OOS Sharpe | -0.16 | +1.33 |
| OOS WR | 30.9% | 41.6% |
| OOS PF | 0.98 | 1.21 |
| Trades | 314 | 286 |

## Key Finding
WR crashed from 46% (symmetric 8%/4%) to 30.9% (asymmetric 8%/2%). The 2% SL is too tight for 8% targets — normal BTC/ETH volatility triggers stop-loss before TP can be reached.

## Exploration/Exploitation Tracker  
Last 10: [X, X, X, X, X, E, E, E, E, **X-next**] → 4/10 = 40% ✓

## Next Iteration Ideas
1. **TP=6%/SL=3% (2:1 symmetric)**: Middle ground — bigger moves than 4%/2%, tighter SL than 8%/4%
2. **Back to exploitation at baseline**: The baseline (TP=4%/SL=2%, 0.85 threshold, BTC+ETH) is well-proven. Try start_time=2022 to fix IS.
3. **TP=8%/SL=3% (2.67:1)**: More room for SL while keeping large TP.

## Lessons Learned
- Asymmetric barriers don't work when SL is too tight relative to TP. The ratio matters but so does the absolute SL level relative to the asset's normal volatility.
- BTC/ETH 8h candles have ~2% std. A 2% SL = 1 standard deviation = 50% chance of being hit just from noise.
- For 8% TP targets, SL needs to be at least 3-4% to give the trade room to develop.
