# Current Baseline

Last updated by: iteration 001 (2026-03-25)
OOS cutoff date: 2025-03-24 (fixed, never changes)

## Out-of-Sample Metrics (trades with entry_time >= 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | -4.89      |
| Sortino         | -8.01      |
| Max Drawdown    | 16,387%    |
| Win Rate        | 30.9%      |
| Profit Factor   | 0.87       |
| Total Trades    | 83,408     |
| Calmar Ratio    | 0.93       |

## In-Sample Metrics (trades with entry_time < 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | -8.55      |
| Sortino         | -11.94     |
| Max Drawdown    | 117,381%   |
| Win Rate        | 30.2%      |
| Profit Factor   | 0.80       |
| Total Trades    | 415,268    |
| Calmar Ratio    | 1.00       |

## Overfitting Diagnostics (Researcher Bias Check)

| Metric   | IS     | OOS    | Ratio (OOS/IS) |
|----------|--------|--------|----------------|
| Sharpe   | -8.55  | -4.89  | 0.57           |
| Sortino  | -11.94 | -8.01  | 0.67           |
| Win Rate | 30.2%  | 30.9%  | 1.02           |

## Hard Constraints Status

| Constraint                         | Value   | Threshold   | Pass |
|------------------------------------|---------|-------------|------|
| Max Drawdown (OOS)                 | 16,387% | ≤ 19,664%   | —    |
| Min OOS Trades                     | 83,408  | ≥ 50        | PASS |
| Profit Factor (OOS)                | 0.87    | > 1.0       | FAIL |
| Max Single-Symbol PnL Contribution | <1%     | ≤ 30%       | PASS |
| IS/OOS Sharpe Ratio                | 0.57    | > 0.5       | PASS |

## Strategy Summary

- Labeling: Triple barrier TP=4%, SL=2%, timeout=3 days, fee-aware returns
- Symbols: 201 USDT (pooled model, no filtering)
- Features: 185 (all groups, no Optuna selection)
- Walk-forward: monthly retraining, 5 CV folds, 12-month window, 50 Optuna trials
- No confidence threshold — model trades every candle

## Notes

Initial baseline. Strategy is deeply unprofitable (negative Sharpe, 30% win rate, PF<1).
The primary issue is trading every candle with no selectivity — 498K total trades.
The max drawdown threshold is set to iteration 001's OOS max drawdown × 1.2 = 19,664%.
Next iteration should focus on trade filtering (confidence threshold, volatility gate, or
reduced trading frequency) to improve win rate above the ~34% break-even threshold.
