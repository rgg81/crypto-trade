# Research Brief: 8H LightGBM Iteration 040 — EXPLOITATION

## 0. Data Split: OOS cutoff 2025-03-24. Full data range.

## 1. Change: Fixed confidence threshold at 0.75 (remove from Optuna)

### Rationale
Seed sweep (iters 038-039) showed OOS Sharpe varies ±1.2 across seeds. A major source: Optuna picks different confidence thresholds per month per seed, causing wildly different trade counts.

By fixing threshold=0.75 (middle of the 0.50-0.85 range that worked well), we:
1. Remove one source of seed-dependent variance
2. Ensure consistent selectivity across all months and seeds
3. Let Optuna focus only on LightGBM hyperparams + training_days

## 2. Everything else: baseline config, seed=42.
