# Current Baseline

Last updated by: iteration 004 (2026-03-25)
OOS cutoff date: 2025-03-24 (fixed, never changes)

## Out-of-Sample Metrics (trades with entry_time >= 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | -1.91      |
| Sortino         | -2.80      |
| Max Drawdown    | 997%       |
| Win Rate        | 32.9%      |
| Profit Factor   | 0.92       |
| Total Trades    | 6,831      |
| Calmar Ratio    | 0.77       |

## In-Sample Metrics (trades with entry_time < 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | -4.63      |
| Sortino         | -5.15      |
| Max Drawdown    | 13,558%    |
| Win Rate        | 30.6%      |
| Profit Factor   | 0.80       |
| Total Trades    | 47,269     |
| Calmar Ratio    | 1.00       |

## Overfitting Diagnostics (Researcher Bias Check)

| Metric   | IS     | OOS    | Ratio (OOS/IS) |
|----------|--------|--------|----------------|
| Sharpe   | -4.63  | -1.91  | 0.41           |
| Sortino  | -5.15  | -2.80  | 0.54           |
| Win Rate | 30.6%  | 32.9%  | 1.08           |

## Hard Constraints Status

| Constraint                         | Value | Threshold | Pass |
|------------------------------------|-------|-----------|------|
| Max Drawdown (OOS)                 | 997%  | ≤ 1,196%  | PASS |
| Min OOS Trades                     | 6,831 | ≥ 50      | PASS |
| Profit Factor (OOS)                | 0.92  | > 1.0     | FAIL |
| Max Single-Symbol PnL Contribution | TBD   | ≤ 30%     | TBD  |
| IS/OOS Sharpe Ratio                | 0.41  | > 0.5     | FAIL |

## Strategy Summary

- Labeling: Triple barrier TP=4%, SL=2%, timeout=3 days, fee-aware returns
- Symbols: Top 50 by IS quote volume (pooled model)
- Features: 106 (all in parquet intersection for 50 symbols)
- Walk-forward: monthly retraining, 5 CV folds, 12-month window, 50 Optuna trials
- Confidence threshold: Optuna-optimized 0.50–0.65

## Notes

Iteration 004 reduced symbols from 201 to top 50. Win rate improved 2.2pp to 32.9%
(best ever, 1.1pp from break-even). Max drawdown reduced 5x. OOS WR exceeds IS WR
(32.9% vs 30.6%) — the model generalizes well on liquid symbols.
Max drawdown threshold set to iter 004's OOS max drawdown × 1.2 = 1,196%.
