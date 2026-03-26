# Current Baseline

Last updated by: iteration 016 (2026-03-26)
OOS cutoff date: 2025-03-24 (fixed, never changes)

## Out-of-Sample Metrics (trades with entry_time >= 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +1.33      |
| Sortino         | ~+2.0      |
| Max Drawdown    | 31.1%      |
| Win Rate        | 41.6%      |
| Profit Factor   | 1.21       |
| Total Trades    | 286        |
| Total PnL       | ~+50%      |

## Strategy Summary

- Symbols: BTCUSDT + ETHUSDT only
- Labeling: Triple barrier TP=4%, SL=2%, timeout=3 days
- Features: 185 (all available)
- Confidence threshold: Optuna 0.50–0.85
- Walk-forward: monthly, 12-month window, 5 CV, 50 Optuna trials

## Notes

Best iteration ever. Selectivity trend: 0.65→0.75→0.85 threshold ceiling, each
improving all metrics. OOS Sharpe progression: -4.89 → -1.96 → -1.91 → +0.43 → +0.48 → +1.33.
Max drawdown threshold: 31.1% × 1.2 = 37.3%.
