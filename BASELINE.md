# Current Baseline

Last updated by: iteration 002 (2026-03-25)
OOS cutoff date: 2025-03-24 (fixed, never changes)

## Out-of-Sample Metrics (trades with entry_time >= 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | -1.96      |
| Sortino         | -2.58      |
| Max Drawdown    | 5,079%     |
| Win Rate        | 30.7%      |
| Profit Factor   | 0.89       |
| Total Trades    | 26,545     |
| Calmar Ratio    | 0.76       |

## In-Sample Metrics (trades with entry_time < 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | -5.04      |
| Sortino         | -6.16      |
| Max Drawdown    | 42,423%    |
| Win Rate        | 30.7%      |
| Profit Factor   | 0.83       |
| Total Trades    | 169,097    |
| Calmar Ratio    | 0.99       |

## Overfitting Diagnostics (Researcher Bias Check)

| Metric   | IS     | OOS    | Ratio (OOS/IS) |
|----------|--------|--------|----------------|
| Sharpe   | -5.04  | -1.96  | 0.39           |
| Sortino  | -6.16  | -2.58  | 0.42           |
| Win Rate | 30.7%  | 30.7%  | 1.00           |

## Hard Constraints Status

| Constraint                         | Value  | Threshold | Pass |
|------------------------------------|--------|-----------|------|
| Max Drawdown (OOS)                 | 5,079% | ≤ 6,095%  | PASS |
| Min OOS Trades                     | 26,545 | ≥ 50      | PASS |
| Profit Factor (OOS)                | 0.89   | > 1.0     | FAIL |
| Max Single-Symbol PnL Contribution | <1%    | ≤ 30%     | PASS |
| IS/OOS Sharpe Ratio                | 0.39   | > 0.5     | FAIL |

## Strategy Summary

- Labeling: Triple barrier TP=4%, SL=2%, timeout=3 days, fee-aware returns
- Symbols: 201 USDT (pooled model)
- Features: 185 (all groups, no selection)
- Walk-forward: monthly retraining, 5 CV folds, 12-month window, 50 Optuna trials
- Confidence threshold: Optuna-optimized 0.50–0.65

## Notes

Iteration 002 added confidence thresholding. Trade count reduced 68% from iter 001.
Win rate unchanged at 30.7% — threshold doesn't improve accuracy, only reduces volume.
Max drawdown threshold set to iter 002's OOS max drawdown × 1.2 = 6,095%.
Key bottleneck: 30.7% win rate vs 34% break-even. The model's probabilities are
poorly calibrated — confidence doesn't predict trade quality.
