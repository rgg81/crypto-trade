# Current Baseline

Last updated by: iteration 063 (2026-03-28)
OOS cutoff date: 2025-03-24 (fixed, never changes)

## Out-of-Sample Metrics (trades with entry_time >= 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +1.95      |
| Win Rate        | 44.0%      |
| Profit Factor   | 1.66       |
| Max Drawdown    | 18.4%      |
| Total Trades    | 100        |

## In-Sample Metrics (trades with entry_time < 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +1.48      |
| Win Rate        | 45.3%      |
| Profit Factor   | 1.34       |
| Max Drawdown    | 74.9%      |
| Total Trades    | 541        |

## Seed Validation (5 seeds)

| Seed | IS Sharpe | OOS Sharpe |
|------|----------|-----------|
| 42   | +1.48    | +1.95     |
| 123  | +1.00    | +0.70     |
| 456  | +0.81    | +0.13     |
| 789  | +0.83    | +1.20     |
| 1001 | +1.46    | -0.78     |

IS: **5/5 positive** (mean +1.12, std 0.30)
OOS: **4/5 positive** (mean +0.64, std 0.96)

## Strategy Summary

- Symbols: BTCUSDT + ETHUSDT only
- Training: **24 months** (covers bull + bear markets)
- Labeling: Triple barrier **TP=8%, SL=4%**, timeout=**7 days**
- Execution barriers: **Dynamic ATR** — TP=2.9×NATR_21, SL=1.45×NATR_21
- Features: 106 (global intersection)
- Confidence threshold: Optuna 0.50–0.85
- Walk-forward: monthly, 5 CV folds, 50 Optuna trials

## Notes

**Iteration 063 BREAKTHROUGH** — dynamic ATR barriers adapt execution to volatility.
OOS Sharpe improved from +1.16 to +1.95 (+68%). OOS MaxDD improved from 75.9% to 18.4% (4x better).
Key insight: fixed 8%/4% barriers were too wide in low-volatility periods (2023-2025).
ATR scaling automatically tightens barriers when volatility is low, producing more TP hits and limiting drawdown.
Labeling stays fixed at 8%/4% — the model learns directional signal, execution adapts to conditions.
Previous baseline (iter 047) had only 3/5 seeds profitable; new baseline has 4/5.
