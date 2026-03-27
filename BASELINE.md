# Current Baseline

Last updated by: iteration 047 (2026-03-27)
OOS cutoff date: 2025-03-24 (fixed, never changes)

## Out-of-Sample Metrics (trades with entry_time >= 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +1.16      |
| Win Rate        | 44.9%      |
| Profit Factor   | 1.27       |
| Max Drawdown    | 75.9%      |
| Total Trades    | 136        |

## In-Sample Metrics (trades with entry_time < 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +1.60      |
| Win Rate        | 43.4%      |
| Profit Factor   | 1.31       |
| Max Drawdown    | 64.3%      |
| Total Trades    | 574        |

## Seed Validation (5 seeds)

| Seed | IS Sharpe | OOS Sharpe |
|------|----------|-----------|
| 42   | +1.60    | +1.16     |
| 123  | +1.76    | -0.32     |
| 456  | +1.32    | +1.66     |
| 789  | +1.02    | +0.51     |
| 1001 | +1.19    | -0.95     |

IS: **5/5 positive** (mean +1.38, std 0.27)
OOS: **3/5 positive** (mean +0.41, std 0.95)

## Strategy Summary

- Symbols: BTCUSDT + ETHUSDT only
- Training: **24 months** (covers bull + bear markets)
- Labeling: Triple barrier **TP=8%, SL=4%**, timeout=**7 days**
- Features: 106 (global intersection)
- Confidence threshold: Optuna 0.50–0.85
- Walk-forward: monthly, 5 CV folds, 50 Optuna trials

## Notes

**BREAKTHROUGH** — first strategy with both IS and OOS positive Sharpe.
First to pass the year-1 fail-fast checkpoint (profitable in 2022, first year of predictions).
Key insight: 24mo training + wider barriers (8%/4%) + longer timeout (7 days) = the model
predicts large BTC/ETH moves with 43-45% accuracy, which is well above the 33.3% break-even.
