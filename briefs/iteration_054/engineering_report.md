# Engineering Report: Iteration 054

## Configuration

- **Change**: AVAX+DOT as independent pair (separate model)
- **Symbols**: AVAXUSDT, DOTUSDT
- **Training**: 24 months, 5 CV folds, 50 Optuna trials
- **Barriers**: TP=8%, SL=4%, timeout=7 days
- **Seed**: 42

## Results (IS only — early stopped)

| Metric | IS |
|--------|----|
| Sharpe | -0.24 |
| WR | 35.3% |
| PF | 0.96 |
| MaxDD | 112.4% |
| Trades | 266 |
| PnL | -25% |

## Per-Symbol (IS)

| Symbol | Trades | WR | PnL | % of Total |
|--------|--------|-----|------|------------|
| AVAXUSDT | 132 | — | -25% | 101.7% |
| DOTUSDT | 134 | — | +0.4% | -1.7% |

Worst-performing pair tested. Both symbols near or below break-even WR.
