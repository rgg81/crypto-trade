# Research Brief: 8H LightGBM Iteration 093

**Type**: EXPLORATION (honest CV baseline validation — 5-seed ensemble)
**Date**: 2026-03-31

## 0. Data Split & Backtest Approach

- OOS cutoff date: 2025-03-24 (project-level constant)
- Walk-forward backtest runs on FULL dataset (IS + OOS), monthly retraining
- Report layer splits at OOS_CUTOFF_DATE

## Core Hypothesis

Validate that the signal found in iter 091 (OOS Sharpe +0.89) is not seed-dependent by increasing ensemble from 3 to 5 seeds. Use symbol-scoped feature discovery (185 features) instead of global intersection (106).

## Configuration

- CV gap: 44 rows (22 candles × 2 symbols) — no label leakage
- Features: 185 (symbol-scoped, BTC+ETH, 6 base groups)
- Model: LGBMClassifier binary, ensemble 5 seeds [42, 123, 456, 789, 1001]
- Walk-forward: monthly, 24mo window, 5 CV folds, 50 Optuna trials
- Execution: Dynamic ATR barriers TP=2.9, SL=1.45, cooldown=2
