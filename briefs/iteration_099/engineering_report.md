# Engineering Report — Iteration 099

## Change Summary

Implemented per-symbol LightGBM models: each symbol gets independent Optuna optimization, confidence threshold, and feature weights. Added `per_symbol_models=True` parameter to `LightGbmStrategy`.

## Implementation Details

**Code changes** (`lgbm.py`):
1. Added `per_symbol_models: bool = False` parameter
2. New `_train_per_symbol()` method: loops over each unique symbol, filters training data to that symbol only, runs independent Optuna + ensemble training
3. Per-symbol state: `_sym_models`, `_sym_thresholds`, `_sym_selected_cols`
4. `get_signal()` routes to per-symbol model when available
5. Feature cache uses sorted column union across all symbols; per-symbol column extraction via index mapping

**CV gap**: Changed from `(timeout_candles + 1) * n_symbols = 44` to `(timeout_candles + 1) * 1 = 22` per symbol (correct: single-symbol training set has no cross-symbol label overlap).

## Label Leakage Audit

- CV gap: 22 rows per symbol (correct for single-symbol training)
- TimeSeriesSplit with gap=22 verified in Optuna logs
- Walk-forward: training window boundary enforced per-symbol
- No cross-symbol label contamination possible (each model sees only its own symbol)

## Results

**EARLY STOP** — Year 2022: PnL=-82.1%, WR=34.6%, 130 trades.

### IS Metrics (partial — stopped after 2022)

| Metric | Iter 099 (per-symbol) | Baseline (093, pooled) |
|--------|----------------------|------------------------|
| Sharpe | -0.83 | +0.73 |
| WR | 35.1% | 42.8% |
| PF | 0.82 | 1.19 |
| MaxDD | 139.9% | 92.9% |
| Trades | 131 (early stop) | 346 |

### Per-Symbol IS Breakdown

| Symbol | Trades | WR | Net PnL |
|--------|--------|----|---------|
| BTCUSDT | 69 | 40.6% | +3.8% |
| ETHUSDT | 62 | 29.0% | -80.8% |

**ETH collapsed.** BTC was reasonable (40.6% WR ~ baseline 43.2%). ETH went from 42.4% (pooled) to 29.0% (per-symbol). ETH's per-symbol model overfitted severely.

## Root Cause: Insufficient Samples/Feature Ratio

Per-symbol training data: ~2,160 samples (24 months × 90 candles/month × 1 symbol).
Features: 185.
Ratio: 2,160 / 185 = **11.7** (below the 50 minimum guideline).

Optuna selected `training_days=10` (≈30 samples) for some months of the last seed — fitting a 185-feature model to 30 samples is pure memorization.

## Key Finding

ETH *benefits* from BTC's training data in the pooled model. This is counterintuitive given their different directional biases (ETH OOS longs 56.5% vs BTC OOS longs 28.0%). The pooled data provides regularization through diversity — BTC's patterns prevent ETH's model from overfitting to ETH-specific noise.

## Trade Execution Verification

Sampled 10 trades from IS trades.csv:
- Entry prices match close prices of signal candles: verified
- SL/TP calculations using dynamic ATR barriers: verified
- Timeout durations: 7 days (10080 min): verified
- PnL calculations net of 0.1% fees: verified
- No anomalies detected in trade execution
