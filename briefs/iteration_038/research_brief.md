# Research Brief: 8H LightGBM Iteration 038 — EXPLOITATION

## 0. Data Split: OOS cutoff 2025-03-24. Full data range.

## 1. Change: seed=123 (from seed=42)
Robustness test. If OOS Sharpe +1.33 is real signal, it should hold with a different seed. If it drops significantly, the result was seed-dependent (lucky).

## 2. Everything else: exact iter 016 baseline config.
