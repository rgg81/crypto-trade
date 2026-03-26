# Iteration 013 Diary - 2026-03-26

## Merge Decision: NO-MERGE
OOS Sharpe -0.63 (baseline +0.43). Shorter timeout didn't help.

## Results: Out-of-Sample
| Metric | Value | Baseline |
|--------|-------|----------|
| Sharpe | -0.63 | +0.43 |
| WR | 38.1% | 38.6% |
| PF | 0.94 | 1.05 |
| Trades | 504 | 487 |
| MaxDD | 82.2% | 49.6% |

## What Failed
- Shorter timeout (2 days vs 3 days) cut some TP hits short. Trades that would have reached +4% in 3 days now timed out at smaller returns.
- PF dropped from 1.05 to 0.94 — the TP/SL balance shifted unfavorably.
- WR barely changed (38.1% vs 38.6%) — timeout trades are a small fraction.

## Next Iteration Ideas
1. **BTC+ETH with 100 Optuna trials**: The baseline uses 50 trials. With only 2 symbols, the search space may benefit from more exploration.
2. **BTC+ETH with calendar hour feature**: Add hour_of_day (0/8/16) as a feature.
3. **BTC+ETH with longer training window**: Try 18 or 24 months instead of 12.

## Lessons Learned
- The 3-day (4320 min) timeout is well-calibrated for 4%/2% barriers on 8h BTC/ETH candles. Shorter hurts.
