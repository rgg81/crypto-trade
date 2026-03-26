# Iteration 012 Diary - 2026-03-26

## Merge Decision: NO-MERGE

OOS Sharpe +0.26 < baseline +0.43. Despite best-ever WR (40.7%) and MaxDD (24.7%), the primary metric didn't improve due to fewer trades.

## Hypothesis
BTC-only model to maximize signal concentration.

## Results: Out-of-Sample
| Metric | Value | Baseline |
|--------|-------|----------|
| Sharpe | +0.26 | +0.43 |
| WR | 40.7% | 38.6% |
| PF | 1.04 | 1.05 |
| Trades | 189 | 487 |
| MaxDD | 24.7% | 49.6% |

## Gap Quantification
WR 40.7%, break-even 33.3%, surplus +7.4pp. PF 1.04 (profitable). But fewer trades → lower Sharpe.

## What Worked
- **Highest WR ever: 40.7%** — BTC is very predictable for this model
- **Lowest MaxDD ever: 24.7%** — concentrated, high-quality trades
- **Profitable**: PF 1.04, positive PnL

## What Failed
- Only 189 trades over 11 months (~17/month). Too few for good Sharpe.
- The Sharpe penalty from low trade count outweighs the WR improvement.

## Next Iteration Ideas
1. **BTC+ETH with per-symbol model**: Train separate models for BTC and ETH, each making independent predictions. This preserves BTC's signal while adding ETH's volume.
2. **BTC+ETH with more Optuna focus on threshold**: The confidence threshold matters more with 2 symbols. A tighter threshold on ETH and looser on BTC might help.
3. **Reduce timeout to 2 days**: Faster trade resolution = more trades per month.

## Lessons Learned
- BTC-only achieves best WR (40.7%) and MaxDD (24.7%) but insufficient trade volume for good Sharpe.
- BTC+ETH (iter 010) is the sweet spot: enough trades (487) AND profitable WR (38.6%).
- The baseline (BTC+ETH) remains optimal for now.
