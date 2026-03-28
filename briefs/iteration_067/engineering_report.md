# Iteration 067 — Engineering Report

## Change
Multi-seed ensemble: 3 LightGBM models per walk-forward month (seeds 42, 123, 789). Averaged predicted probabilities before confidence threshold gating. Averaged confidence thresholds.

## Result

| Metric | Ensemble (067) | Baseline (063) |
|--------|---------------|---------------|
| IS Sharpe | +1.23 | +1.48 |
| IS MaxDD | **50.0%** | 74.9% |
| OOS Sharpe | +1.64 | +1.95 |
| OOS MaxDD | 39.0% | 18.4% |
| OOS Trades | 114 | 100 |
| OOS/IS | 1.34 | 1.32 |
| Runtime | 3844s (~64min) | ~1200s (~20min) |

Ensemble IS MaxDD best ever (50% vs 74.9%). But OOS MaxDD 39% > 22.1% limit = hard fail.
No seed variance (deterministic output). 3x runtime as expected.

## Trade Verification
Spot-checked 10 trades. Execution correct. ATR barriers applied properly.
