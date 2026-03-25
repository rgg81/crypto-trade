# Current Baseline

Last updated by: (no iterations completed yet)
OOS cutoff date: 2025-03-24 (fixed, never changes)

## Out-of-Sample Metrics (trades with entry_time >= 2025-03-24)

| Metric          | Value  |
|-----------------|--------|
| Sharpe          | —      |
| Sortino         | —      |
| Max Drawdown    | —      |
| Win Rate        | —      |
| Profit Factor   | —      |
| Total Trades    | —      |
| Calmar Ratio    | —      |

## In-Sample Metrics (trades with entry_time < 2025-03-24)

| Metric          | Value  |
|-----------------|--------|
| Sharpe          | —      |
| Sortino         | —      |
| Max Drawdown    | —      |
| Win Rate        | —      |
| Profit Factor   | —      |
| Total Trades    | —      |
| Calmar Ratio    | —      |

## Overfitting Diagnostics (Researcher Bias Check)

| Metric   | IS  | OOS | Ratio (OOS/IS) |
|----------|-----|-----|----------------|
| Sharpe   | —   | —   | —              |
| Sortino  | —   | —   | —              |
| Win Rate | —   | —   | —              |

## Hard Constraints Status

| Constraint                         | Value | Threshold | Pass |
|------------------------------------|-------|-----------|------|
| Max Drawdown (OOS)                 | —     | ≤ TBD     | —    |
| Min OOS Trades                     | —     | ≥ 50      | —    |
| Profit Factor (OOS)                | —     | > 1.0     | —    |
| Max Single-Symbol PnL Contribution | —     | ≤ 30%     | —    |
| IS/OOS Sharpe Ratio                | —     | > 0.5     | —    |

## Strategy Summary

- Labeling: (none yet)
- Symbols: (none yet)
- Features: (none yet)
- Walk-forward: monthly retraining, timeseries CV, 1-year minimum window

## Notes

Initial baseline. First iteration (001) will populate these values upon merge.
The max drawdown threshold will be set to the first iteration's OOS max drawdown × 1.2 after it merges.
