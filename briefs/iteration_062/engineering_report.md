# Engineering Report — Iteration 062

**Date**: 2026-03-28
**Status**: Full completion (but OOS negative)

## Backtest Results

| Metric | Iter 062 IS | Baseline IS | Iter 062 OOS | Baseline OOS |
|--------|-------------|-------------|-------------|-------------|
| Sharpe | **+1.99** | +1.60 | **-0.41** | +1.16 |
| Win Rate | 45.7% | 43.4% | 35.7% | 44.9% |
| Profit Factor | 1.42 | 1.31 | 0.93 | 1.27 |
| Max Drawdown | 50.7% | 64.3% | 58.0% | 75.9% |
| Total Trades | 514 | 574 | 157 | 136 |
| PnL | +460.5% | +387.9% | -28.4% | +78.6% |
| OOS/IS Sharpe | -0.21 | 0.72 | — | — |

### Per-Symbol OOS
- BTC: 57 trades, 35.1% WR, -20.5% PnL
- ETH: 100 trades, 36.0% WR, -7.9% PnL

## Key Finding

Correlation dedup produced the **best IS results ever** (Sharpe 1.99, PF 1.42) but the **worst OOS** (Sharpe -0.41, negative PnL). This is extreme researcher overfitting — OOS/IS ratio -0.21.

**Why**: Removing correlated features removed implicit regularization. LightGBM's `colsample_bytree` randomly subsets features per tree. Correlated features provide redundant information across subsets, preventing over-reliance on any single feature. Removing them concentrated the model's fitting power, improving IS fit but destroying OOS generalization.

## Trade Execution Verification

Verified 10 trades. All correct.
