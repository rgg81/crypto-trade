# Iteration 030 Diary - 2026-03-26 — EXPLORATION
## Merge Decision: NO-MERGE
OOS Sharpe -0.47 < baseline +1.33.
## Type: EXPLORATION (6%/3% barriers)
## Results: IS Sharpe -0.15, IS WR 39.4%, OOS Sharpe -0.47, OOS WR 40.8%.

## Barrier Sweep Summary (BTC+ETH, threshold 0.85)
| Barriers | IS Sharpe | OOS Sharpe | IS WR | OOS WR |
|----------|----------|-----------|-------|--------|
| 4%/2%    | -0.96    | **+1.33** | 34.0% | 41.6%  |
| 6%/3%    | -0.15    | -0.47     | 39.4% | 40.8%  |
| 8%/4%    | -0.04    | -0.36     | 42.2% | 46.0%  |

## Key Insight
Bigger barriers improve IS dramatically but hurt OOS. The 4%/2% baseline adapts fastest to recent market changes. For IS+OOS both positive, the solution is probably the 4%/2% baseline with a later start_time (iter 025 got IS to -0.14).

## Exploration/Exploitation Tracker
Last 10: [X, X, E, E, E, E, X, E, E, **E**] → 7/10 = 70% exploration — time to exploit!
