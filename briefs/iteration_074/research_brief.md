# Research Brief: 8H LightGBM Iteration 074

**Type**: EXPLOITATION (baseline reproduction diagnostic)

## 0. Data Split & Backtest Approach
- OOS cutoff date: 2025-03-24 (project-level constant)
- The walk-forward backtest runs on the FULL dataset (IS + OOS) as one continuous process
- Monthly retraining, 24-month training window, 5 CV folds, 50 Optuna trials

## Motivation

After 6 consecutive NO-MERGEs (069-073), we need to understand the current state of the feature parquet before making further changes. The baseline (iter 068) was measured with 106 features, but the current parquet has 187 features for BTC/ETH (due to code from failed iters 070, 072 accidentally committed to main).

Additionally, iter 073 found a bug: `_discover_feature_columns()` scans ALL 760 parquet files. Other symbols have 251 features vs BTC/ETH's 187. The intersection across all symbols may differ from BTC/ETH alone.

## Research Analysis Reference

Research from iter 073 (categories A, C, E, F) still applies:
- Signal is real (mean PnL p=0.017, WR above break-even p=0.0002)
- Feature pruning destroys signal — per-month importance differs from global
- SHORT is better than LONG; ETH more profitable than BTC
- Bootstrap Sharpe CI [0.03, 0.22]

## Hypothesis

**Null hypothesis**: Running the exact baseline config (iter 068) with symbol-filtered discovery will produce results similar to the baseline, despite the parquet having 187 features (vs original 106).

This establishes whether:
1. The extra features from iters 070/072 are neutral (model ignores them)
2. Or harmful (model overfits to noise from extra features)

## 1-7. Configuration

**IDENTICAL to iter 068 baseline** — no changes except:
- Fix: `_discover_feature_columns()` passes `symbols` from master DataFrame (discovery bug fix from iter 073)
- The model will discover all 187 features from BTC/ETH parquets instead of the global intersection

All other parameters match iter 068 exactly:
- Labeling: TP=8%, SL=4%, timeout=7d
- Symbols: BTCUSDT, ETHUSDT
- Execution: Dynamic ATR TP=2.9×NATR_21, SL=1.45×NATR_21
- Cooldown: 2 candles
- Ensemble: seeds [42, 123, 789]
- Walk-forward: 24mo, 5 CV, 50 trials

## 8. Report Requirements
Standard IS/OOS split at OOS_CUTOFF_DATE with comparison.csv.
