# Engineering Report — Iteration 059

**Date**: 2026-03-28
**Status**: EARLY STOP (Year 1 fail-fast)

## Implementation

Added `per_symbol: bool = False` parameter to `LightGbmStrategy`. When enabled:
- `_train_for_month_per_symbol()`: Iterates over unique symbols, filters training indices per symbol, trains separate LightGBM + Optuna per symbol
- Per-symbol state stored in `_models`, `_selected_cols_map`, `_confidence_threshold_map` dicts keyed by symbol
- `_get_signal_per_symbol()`: Looks up the symbol-specific model for prediction
- Pooled mode (`_train_for_month_pooled`, `_get_signal_pooled`) preserved unchanged for backward compatibility

## Data Issue: Stale Slow Features

**Initial run** used 137 features (not 106) because parquet files still contained slow features from iter 057-058's data regeneration. The global intersection picked up 31 slow features that shouldn't have been there.

**Fix**: Regenerated BTC and ETH parquets from current code (no slow feature generation). Global intersection returned to 106 features. Backtest re-run with correct 106 features.

**First run (137 features)**: IS Sharpe=0.14, WR=38.6%, early stop Year 2024
**Second run (106 features)**: IS Sharpe=-0.44, WR=34.0%, early stop Year 2022

Both runs failed, but the 106-feature run was even worse — isolating the per-symbol model as the degradation cause.

## Backtest Results

| Metric | Iter 059 IS | Baseline IS |
|--------|-------------|-------------|
| Sharpe | -0.44 | +1.60 |
| Win Rate | 34.0% | 43.4% |
| Profit Factor | 0.94 | 1.31 |
| Max Drawdown | 107.5% | 64.3% |
| Total Trades | 259 | 574 |
| PnL | -40.9% | +387.9% |

### Per-Symbol Breakdown

| Metric | BTC (per-symbol) | ETH (per-symbol) | BTC (baseline) | ETH (baseline) |
|--------|-----------------|-----------------|----------------|----------------|
| Trades | 114 | 145 | 257 | 317 |
| WR | 35.1% | 33.1% | 40.5% | 45.7% |
| TP Rate | 27.2% | 31.7% | 27.2% | 36.3% |
| SL Rate | 59.6% | 65.5% | 51.0% | 52.4% |
| PnL | -20.1% | -20.7% | +81.8% | +306.1% |

### Early Stop Trigger

Year 2022 (first year of predictions): PnL=-39.4%, WR=34.1% (258 trades). Breached fail-fast threshold (negative PnL).

## Trade Execution Verification

Sampled 10 trades from trades.csv. All verified:
- Entry prices match close of signal candle
- SL exits at exactly -4.0% (net -4.1% with fees)
- TP exits at exactly +8.0% (net +7.9% with fees)
- Timeout exits with correct PnL calculations
- No anomalies detected

## Key Finding

Per-symbol models with ~2200 training samples are worse than pooled models with ~4400 samples. Both BTC AND ETH degraded significantly:
- **ETH** collapsed from 45.7% WR to 33.1% — near random. Lost 12.6pp.
- **BTC** dropped from 40.5% to 35.1% — lost 5.4pp.
- SL rates increased dramatically (BTC: 51%→60%, ETH: 52%→66%)
- Total trade count halved (574→259) — model is less decisive

The pooled model's cross-symbol learning is essential, not dilutive. ETH data helps BTC predictions and vice versa — removing this signal sharing destroyed performance.
