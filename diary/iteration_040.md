# Iteration 040 Diary - 2026-03-26 — EXPLOITATION
## Merge Decision: NO-MERGE
OOS -0.24 < baseline +1.33. Fixed threshold 0.75 worse than Optuna-optimized.

## Finding: The adaptive Optuna threshold IS valuable — it picks different thresholds per month based on model confidence that month. Fixing it removes this adaptability and generates too many low-quality trades.

## Session Summary (40 iterations)
- Baseline: iter 016 (BTC+ETH, 4%/2%, Optuna threshold 0.50-0.85, seed 42)
- OOS Sharpe: +1.33 (seed 42), +1.14 (seed 456), -1.15 (seed 123). Mean +0.44.
- IS Sharpe: -0.96 (structural — 2021 cold-start + 2022 bear)
- Feature engineering (iters 026-037): ALL attempts to modify features made OOS worse
- The 106-feature global intersection + Optuna threshold is a robust local optimum
