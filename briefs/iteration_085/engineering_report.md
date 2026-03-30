# Iteration 085 Engineering Report

**Date**: 2026-03-30
**QE**: Claude (autopilot)

## Implementation Summary

Added regression labeling mode to the LightGBM strategy:
- New `optimize_and_train_regression()` in optimization.py (LGBMRegressor, magnitude threshold)
- New `use_regression` parameter in LightGbmStrategy
- Regression target: `long_pnls - short_pnls` (direction value)
- Inference: trade when `|prediction| > magnitude_threshold`, direction = sign(prediction)

## Backtest Results

**EARLY STOP**: Year 2025 PnL=-81.3%, WR=25.0%, 64 trades.

### In-Sample

| Metric | Iter 085 | Baseline (068) |
|--------|----------|----------------|
| Sharpe | +0.82 | +1.22 |
| WR | 43.5% | 43.4% |
| PF | 1.27 | 1.35 |
| MaxDD | 46.8% | 45.9% |
| Trades | 232 | 373 |

### Out-of-Sample

| Metric | Iter 085 | Baseline (068) |
|--------|----------|----------------|
| Sharpe | **-2.01** | +1.84 |
| WR | **27.1%** | 44.8% |
| PF | **0.54** | 1.62 |
| MaxDD | **63.0%** | 42.6% |
| Trades | 48 | 87 |
| Net PnL | **-54.5%** | +94.0% |

Per-symbol OOS: BTC 26.1% WR (-23.9%), ETH 28.0% WR (-30.6%). Both catastrophic.

## Trade Execution Verification

The regression model used magnitude thresholds in the 2-7 range (Optuna-tuned). The model predicts direction values, and only trades when |prediction| exceeds the threshold. This significantly reduced trade count (232 IS vs 373 baseline) but the directional accuracy in OOS was catastrophic — both symbols below break-even.
