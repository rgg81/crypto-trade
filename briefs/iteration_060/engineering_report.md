# Engineering Report — Iteration 060

**Date**: 2026-03-28
**Status**: EARLY STOP (Year 2 fail-fast)

## Implementation

Added `regression=True` mode to LightGbmStrategy and optimization pipeline:
- `optimize_and_train_regression()`: Uses LGBMRegressor with Huber loss
- Target: `long_pnls - short_pnls` (direction-signed PnL advantage)
- Signal: `prediction > +return_threshold` → LONG, `prediction < -return_threshold` → SHORT
- `return_threshold` optimized by Optuna in [0.5, 8.0] range
- `_signal_regression()` in lgbm.py for prediction-time signal generation

## Backtest Results

| Metric | Iter 060 IS | Baseline IS |
|--------|-------------|-------------|
| Sharpe | +0.34 | +1.60 |
| Win Rate | 39.0% | 43.4% |
| Profit Factor | 1.075 | 1.31 |
| Max Drawdown | 59.9% | 64.3% |
| Total Trades | 213 | 574 |
| PnL | +35.6% | +387.9% |

### Per-Symbol (reversed from baseline!)

| Metric | BTC (regression) | ETH (regression) | BTC (baseline) | ETH (baseline) |
|--------|-----------------|-----------------|----------------|----------------|
| Trades | 99 | 114 | 257 | 317 |
| WR | 41.4% | 36.8% | 40.5% | 45.7% |
| PnL | +44.8% | -9.1% | +81.8% | +306.1% |
| % of Total | 125.7% | -25.7% | 21.1% | 78.9% |

### Early Stop Trigger

Year 2022: +7.4% PnL (passed Year 1 checkpoint)
Year 2023: -28.3% PnL (WR 35.7%, 84 trades) → fail-fast triggered

## Key Observations

1. **Very high return threshold**: Optuna consistently selected return_threshold > 5.0 (best: 6.32). Only trades with predicted |advantage| > 6.32% were taken. This reduced trade count from 574 to 213.

2. **Noisy optimization**: Many -10.0 penalties in Optuna trials (insufficient trades in CV folds). The regression predictions are not well-calibrated — most predictions cluster near zero, making the threshold very sensitive.

3. **Symbol reversal**: BTC became the profitable symbol while ETH lost money. The regression model learns different patterns than classification — likely because the continuous target captures different signal structure.

4. **MaxDD improved**: 59.9% vs 64.3% — fewer but slightly better-filtered trades.

## Trade Execution Verification

Verified 10 sampled trades: entry prices, SL/TP calculation, and PnL all correct. No anomalies.
