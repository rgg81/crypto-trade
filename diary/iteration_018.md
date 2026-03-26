# Iteration 018 Diary - 2026-03-26

## Merge Decision: NO-MERGE
OOS Sharpe dropped +1.33→-0.16. Adding BNB diluted signal.

## Results: Out-of-Sample
| Metric | Value | Baseline |
|--------|-------|----------|
| Sharpe | -0.16 | +1.33 |
| WR | 37.3% | 41.6% |
| PF | 0.98 | 1.21 |
| Trades | 502 | 286 |

## What Failed
- BNB added noise even with 0.85 threshold. BNB's 33.7% IS WR is not strong enough.
- The BTC+ETH model is specific to these two assets. Adding any 3rd symbol hurts.

## Next Iteration Ideas
1. **BTC+ETH with 100 trials at 0.85**: More optimization at the proven config.
2. **Add hour-of-day as feature**: Calendar signal with BTC+ETH at 0.85.
3. **Try 3 CV folds instead of 5**: Less aggressive cross-validation may help with small sample sizes.

## Lessons Learned
- BTC+ETH is the optimal symbol set. BNB (iter 018) and top 5 (iter 011) both hurt.
- The strategy's edge is specific to the two most liquid crypto assets.
