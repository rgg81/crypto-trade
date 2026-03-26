# Iteration 014 Diary - 2026-03-26

## Merge Decision: NO-MERGE
OOS Sharpe -0.34 (baseline +0.43). 24-month training window improved IS but degraded OOS.

## Results: Out-of-Sample
| Metric | Value | Baseline |
|--------|-------|----------|
| Sharpe | -0.34 | +0.43 |
| WR | 36.8% | 38.6% |
| PF | 0.96 | 1.05 |
| Trades | 421 | 487 |

## Key Finding
IS improved massively (Sharpe -1.20→-0.02, WR 34.0%→37.4%) — the 24-month window gives the model more data in-sample. But OOS degraded — the model overfits to older market dynamics that don't persist.

## Next Iteration Ideas
1. **BTC+ETH with 100 Optuna trials**: More optimization on the 2-symbol, 12-month baseline.
2. **Add hour-of-day as feature**: Simple calendar signal.
3. **Widen confidence threshold range to 0.50-0.75**: Allow model to be more selective.
