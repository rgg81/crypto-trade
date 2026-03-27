# Engineering Report: Iteration 051

## Configuration

- **Change**: Timeout extended from 7 days to **14 days** (20160 min)
- **Symbols**: BTCUSDT, ETHUSDT
- **Training**: 24 months, 5 CV folds, 50 Optuna trials
- **Barriers**: TP=8%, SL=4%, timeout=**14 days** (20160 min)
- **Confidence threshold**: Optuna 0.50–0.85
- **Seed**: 42

## Results

| Metric | IS | OOS | Ratio |
|--------|-----|-----|-------|
| Sharpe | +1.51 | -0.65 | -0.43 |
| WR | 42.1% | 32.4% | 0.77 |
| PF | 1.39 | 0.88 | 0.64 |
| MaxDD | 54.5% | 82.7% | 1.52 |
| Trades | 413 | 102 | — |
| PnL | +370% | -32% | — |

OOS/IS ratio negative — complete failure to generalize.

## Per-Symbol (OOS)

| Symbol | Trades | WR | PnL | % of Total |
|--------|--------|-----|------|------------|
| BTCUSDT | 36 | 38.9% | +8% | -24.6% |
| ETHUSDT | 66 | 28.8% | -39% | 124.6% |

ETH WR 28.8% — below break-even (33.3%). The 14-day window is too long for ETH.

## Finding

7-day timeout is optimal. 14 days allows too much price movement against positions. The model predicts direction well for 7-day horizons but accuracy degrades at 14 days.
