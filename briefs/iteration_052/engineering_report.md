# Engineering Report: Iteration 052

## Configuration

- **Change**: Added XRPUSDT to pooled BTC+ETH model
- **Symbols**: BTCUSDT, ETHUSDT, XRPUSDT
- **Training**: 24 months, 5 CV folds, 50 Optuna trials
- **Barriers**: TP=8%, SL=4%, timeout=7 days
- **Seed**: 42

## Results (IS only — early stopped)

| Metric | IS |
|--------|----|
| Sharpe | +0.54 |
| WR | 40.1% |
| PF | 1.09 |
| MaxDD | 144.6% |
| Trades | 531 |
| PnL | +114% |

## Per-Symbol (IS)

| Symbol | Trades | WR | PnL | % of Total |
|--------|--------|-----|------|------------|
| ETHUSDT | 167 | — | +127% | 112.3% |
| BTCUSDT | 151 | — | +28% | 24.7% |
| XRPUSDT | 213 | — | -42% | -37.0% |

XRP generated the most trades but was net negative. Adding it to the pool degraded BTC and ETH performance as well (pool contamination).
