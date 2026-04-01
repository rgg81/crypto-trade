# Engineering Report — Iteration 104

## Results

| Metric | Iter 104 (4/5 agree) | Baseline (093) |
|--------|---------------------|----------------|
| IS Sharpe | +0.69 | +0.73 |
| OOS Sharpe | +0.97 | +1.01 |
| IS WR | 42.3% | 42.8% |
| OOS WR | 43.4% | 42.1% |
| IS Trades | 343 (-3) | 346 |
| OOS Trades | 106 (-1) | 107 |
| OOS MaxDD | 45.7% | 46.6% |

The filter removed 3 IS and 1 OOS trade. The 5 seeds agree on direction >99% of the time.

## Label Leakage Audit

Identical to baseline — no training changes, only inference filtering.
