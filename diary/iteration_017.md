# Iteration 017 Diary - 2026-03-26

## Merge Decision: NO-MERGE
OOS Sharpe dropped +1.33→-0.09. Threshold 0.95 ceiling too aggressive.

## Results: Out-of-Sample
| Metric | Value | Baseline |
|--------|-------|----------|
| Sharpe | -0.09 | +1.33 |
| WR | 36.6% | 41.6% |
| PF | 0.99 | 1.21 |
| Trades | 213 | 286 |

## What Failed
- At 0.95 ceiling, Optuna sometimes picked very high thresholds that filtered too aggressively, removing profitable trades alongside unprofitable ones.
- The 0.85 ceiling (iter 016) is the sweet spot.

## Next Iteration Ideas
1. **Keep 0.85 ceiling, try 100 Optuna trials**: More optimization at the proven sweet spot.
2. **Add BNB as 3rd symbol at 0.85 threshold**: More trades from a liquid large-cap.
3. **Add calendar hour-of-day feature**: Simple but potentially impactful.

## Lessons Learned
- Selectivity has diminishing returns. 0.65→0.75→0.85 each helped. 0.85→0.95 hurt.
- The 0.85 confidence threshold ceiling is optimal for BTC+ETH 8h candles.
