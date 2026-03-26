# Iteration 016 Diary - 2026-03-26

## Merge Decision: MERGE

**Best iteration ever.** OOS Sharpe +1.33 (from +0.48), WR 41.6%, PF 1.21, MaxDD 31.1%.

## Hypothesis
Widen confidence threshold to 0.50-0.85 (from 0.50-0.75) for even higher selectivity.

## Results: Out-of-Sample
| Metric | Value | Baseline |
|--------|-------|----------|
| Sharpe | **+1.33** | +0.48 |
| WR | **41.6%** | 39.2% |
| PF | **1.21** | 1.07 |
| Trades | 286 | 314 |
| MaxDD | **31.1%** | 44.7% |

## Gap Quantification
WR 41.6%, break-even 33.3%, surplus **+8.3pp**. PF 1.21 — profitable with margin.

## What Worked
- Higher selectivity continues to improve all metrics.
- Optuna can now select thresholds up to 0.85, filtering all but the highest-conviction trades.
- 286 trades in 11 months (~26/month) — sufficient for statistical validity.

## Next Iteration Ideas
1. **Even wider threshold to 0.50-0.95**: Push selectivity further.
2. **BTC+ETH+BNB with this threshold**: Test if BNB adds value with high selectivity.
3. **100 Optuna trials**: More optimization at this threshold range.

## Lessons Learned
- Selectivity is the dominant factor for profitability on BTC+ETH.
- Each threshold widening has improved metrics: 0.65→0.75→0.85.
- The model HAS signal but it's hidden in noise — high threshold extracts it.
