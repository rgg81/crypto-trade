# Iteration 015 Diary - 2026-03-26

## Merge Decision: MERGE

All OOS metrics improved: Sharpe +0.43→+0.48, WR 38.6%→39.2%, PF 1.05→1.07, MaxDD 49.6%→44.7%.

## Hypothesis
Widen Optuna confidence threshold range from 0.50-0.65 to 0.50-0.75 for higher selectivity.

## Results: Out-of-Sample
| Metric | Value | Baseline |
|--------|-------|----------|
| Sharpe | +0.48 | +0.43 |
| WR | 39.2% | 38.6% |
| PF | 1.07 | 1.05 |
| Trades | 314 | 487 |
| MaxDD | 44.7% | 49.6% |

## Gap Quantification
WR 39.2%, break-even 33.3%, surplus +5.9pp. Strategy is profitable and improving.

## What Worked
- Higher selectivity (threshold up to 0.75) lets Optuna pick more confident trades per month
- Trade count dropped 35% (487→314) but quality improved across all metrics
- WR, PF, Sharpe, and MaxDD all improved simultaneously — clean signal

## Next Iteration Ideas
1. **BTC+ETH+BNB**: BNB had 33.7% IS WR. Add as a 3rd liquid large-cap.
2. **Further widen threshold to 0.50-0.85**: Even higher selectivity.
3. **Add hour-of-day feature**: Calendar signal.
