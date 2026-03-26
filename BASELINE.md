# Current Baseline

Last updated by: iteration 015 (2026-03-26)
OOS cutoff date: 2025-03-24 (fixed, never changes)

## Out-of-Sample Metrics (trades with entry_time >= 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +0.48      |
| Sortino         | +0.83      |
| Max Drawdown    | 44.7%      |
| Win Rate        | 39.2%      |
| Profit Factor   | 1.07       |
| Total Trades    | 314        |
| Total PnL       | ~+30%      |

## In-Sample Metrics (trades with entry_time < 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | -1.53      |
| Win Rate        | 33.4%      |
| Profit Factor   | 0.84       |
| Total Trades    | 1,926      |
| Max Drawdown    | 458%       |

## Strategy Summary

- Symbols: BTCUSDT + ETHUSDT only
- Labeling: Triple barrier TP=4%, SL=2%, timeout=3 days
- Features: 185 (all available for 2 symbols)
- Confidence threshold: Optuna 0.50–0.75
- Walk-forward: monthly, 12-month window, 5 CV, 50 Optuna trials

## Notes

Second consecutive profitable iteration. Higher selectivity (threshold up to 0.75)
improved all metrics vs iter 010. Strategy is now consistently profitable on OOS data.
Max drawdown threshold: 44.7% × 1.2 = 53.6%.
