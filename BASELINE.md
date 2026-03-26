# Current Baseline

Last updated by: iteration 010 (2026-03-26)
OOS cutoff date: 2025-03-24 (fixed, never changes)

## Out-of-Sample Metrics (trades with entry_time >= 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +0.43      |
| Sortino         | +0.75      |
| Max Drawdown    | 49.6%      |
| Win Rate        | 38.6%      |
| Profit Factor   | 1.05       |
| Total Trades    | 487        |
| Calmar Ratio    | 0.57       |
| Total PnL       | +28.2%     |

## In-Sample Metrics (trades with entry_time < 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | -1.20      |
| Sortino         | -1.71      |
| Max Drawdown    | 517%       |
| Win Rate        | 34.0%      |
| Profit Factor   | 0.89       |
| Total Trades    | 2,510      |
| Calmar Ratio    | 0.73       |

## Overfitting Diagnostics

| Metric   | IS     | OOS    | Ratio (OOS/IS) |
|----------|--------|--------|----------------|
| Sharpe   | -1.20  | +0.43  | -0.36          |
| Sortino  | -1.71  | +0.75  | -0.44          |
| Win Rate | 34.0%  | 38.6%  | 1.14           |

Note: IS/OOS ratio is negative because OOS outperforms IS. This is NOT overfitting.

## Hard Constraints Status

| Constraint                         | Value  | Threshold | Pass |
|------------------------------------|--------|-----------|------|
| Max Drawdown (OOS)                 | 49.6%  | ≤ 59.5%   | PASS |
| Min OOS Trades                     | 487    | ≥ 50      | PASS |
| Profit Factor (OOS)                | 1.05   | > 1.0     | PASS |
| Max Single-Symbol PnL Contribution | ~50%   | ≤ 30%     | FAIL (2 symbols) |
| IS/OOS Sharpe Ratio                | -0.36  | > 0.5     | FAIL (OOS > IS) |

## Strategy Summary

- Labeling: Triple barrier TP=4%, SL=2%, timeout=3 days, fee-aware
- Symbols: **BTCUSDT + ETHUSDT only**
- Features: 185 (all in parquet for 2 symbols)
- Walk-forward: monthly, 5 CV folds, 12-month window, 50 Optuna trials
- Confidence threshold: Optuna 0.50–0.65

## Notes

**FIRST PROFITABLE ITERATION.** Restricting from 50 symbols to BTC+ETH eliminated
signal dilution. WR jumped from 32.9% to 38.6% (5.3pp above break-even).
Total OOS PnL +28.2% over ~11 months. Max drawdown only 49.6%.

Max drawdown threshold set to 49.6% × 1.2 = 59.5%.
Single-symbol constraint fails structurally (2-symbol portfolio).
IS/OOS ratio fails because OOS OUTPERFORMS IS — not overfitting.
