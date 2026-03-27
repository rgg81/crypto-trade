# Engineering Report: Iteration 053

## Configuration

- **Change**: BNB+LINK as independent pair (separate model)
- **Symbols**: BNBUSDT, LINKUSDT
- **Training**: 24 months, 5 CV folds, 50 Optuna trials
- **Barriers**: TP=8%, SL=4%, timeout=7 days
- **Seed**: 42

## Results (IS only — early stopped)

| Metric | IS |
|--------|----|
| Sharpe | +1.08 |
| WR | 40.6% |
| PF | 1.18 |
| MaxDD | 79.9% |
| Trades | 411 |
| PnL | +172% |

## Per-Symbol (IS)

| Symbol | Trades | WR | PnL | % of Total |
|--------|--------|-----|------|------------|
| BNBUSDT | 156 | — | +87% | 50.6% |
| LINKUSDT | 255 | — | +85% | 49.4% |

Balanced contribution between symbols but IS Sharpe below BTC+ETH baseline (+1.60).
