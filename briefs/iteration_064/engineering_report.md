# Iteration 064 — Engineering Report

## Change

Added `optimize_training_window: bool` parameter to `LightGbmStrategy`. When `False`, `open_times=None` is passed to `optimize_and_train()`, disabling the `training_days` Optuna parameter. The model uses the full 24-month training window without trimming.

## Implementation

- `lgbm.py`: New constructor parameter `optimize_training_window` (default `True`, backward-compatible)
- When disabled: `opt_open_times = None`, `opt_train_end = None` passed to optimizer
- `run_iteration_064.py`: Sets `optimize_training_window=False`

## Result: EARLY STOP

Seed 42 triggered the Year 1 checkpoint:
- Year 2022: PnL=-65.8%, WR=33.9%, 115 trades
- IS Sharpe: -0.91 (vs baseline +1.48)
- IS MaxDD: 139.9% (vs baseline 74.9%)
- Total IS trades: 116 (vs baseline 541) — early stop killed remaining years
- No OOS trades generated (stopped before OOS period)

## Root Cause

The `training_days` parameter (range [10, 500]) is NOT just a variance source — it's a **regime adaptation mechanism**. In each walk-forward month, Optuna finds the optimal training window length. This effectively:
1. Prioritizes recent data when market regime has shifted
2. Uses more data when the market is stable
3. Adapts automatically per prediction month

Without it, the full 24-month window includes stale regime data (e.g., 2020-2021 bull-market patterns) that actively hurts predictions in a new regime (2022 bear market). The WR dropped from 45.3% to 33.9% — below break-even for a 2:1 RR system.

## Comparison: IS Only (No OOS)

| Metric | Iter 064 | Baseline (063) |
|--------|----------|---------------|
| Sharpe | -0.91 | +1.48 |
| Win Rate | 33.6% | 45.3% |
| Profit Factor | 0.82 | 1.34 |
| Max Drawdown | 139.9% | 74.9% |
| Total Trades | 116 | 541 |

## Trade Verification

Spot-checked 5 trades from the 116 generated. Entry prices, SL/TP levels, and PnL calculations are correct. The ATR barrier mechanism works correctly — the trades just have terrible direction accuracy.
