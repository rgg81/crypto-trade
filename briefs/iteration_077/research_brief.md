# Research Brief: 8H LightGBM Iteration 077

**Type: EXPLOITATION** — ATR multiplier tuning from iter 076

## 0. Data Split & Backtest Approach

- OOS cutoff date: 2025-03-24 (project-level constant)
- The researcher used ONLY IS data (before 2025-03-24) for all design decisions
- Walk-forward on full dataset, report layer splits at cutoff
- Monthly retraining, 24-month window, 5 CV folds, 50 Optuna trials

## Research Reference

This iteration builds directly on iter 076's research (categories A, C, E, F). Key findings that inform this change:

- **NATR_21 distribution**: P10=1.63%, P25=2.11%, P50=2.78%, P75=3.71%, P90=4.98%
- **Iter 076 (TP=2.9×NATR, SL=1.45×NATR)**: Median barriers 8.05%/4.03%. IS Sharpe +1.30 (better), OOS Sharpe +1.72 (7% below baseline). OOS MaxDD halved (21.6% vs 42.6%).
- **Hypothesis for gap**: In quiet markets (P10), iter 076 barriers were 4.73%/2.37% — the model learned to trade small moves with lower conviction. Wider multipliers should restore the implicit confidence filter that the baseline's fixed 8%/4% labels provide.

## Change from Iter 076

| Parameter | Iter 076 | Iter 077 | Effect on median barriers |
|-----------|----------|----------|--------------------------|
| TP multiplier | 2.9 | **3.2** | 8.05% → **8.89%** |
| SL multiplier | 1.45 | **1.6** | 4.03% → **4.45%** |

Quiet market barriers (P10 NATR=1.63%):
- Iter 076: TP=4.73%, SL=2.37%
- Iter 077: TP=5.22%, SL=2.61%
- Baseline: TP=8.00%, SL=4.00% (fixed)

The wider multipliers shift barriers UP by ~10%, partially restoring the confidence filter while keeping dynamic ATR scaling.

## 1. Labeling

- Method: Triple barrier with dynamic ATR barriers
- TP = **3.2** × NATR_21 (wider than iter 076's 2.9)
- SL = **1.6** × NATR_21 (wider than iter 076's 1.45)
- Timeout = 7 days, Fee = 0.1%
- RR ratio maintained at 2:1

## 2-4. Symbol Universe / Data Filtering / Features

Unchanged from iter 076/baseline: BTC+ETH, 106 features (global intersection), no filters.

## 5-6. Model / Walk-Forward

Unchanged: 3-seed ensemble [42, 123, 789], 24mo window, 5 CV folds, 50 Optuna trials.

## 7. Backtest Requirements

- Execution: Dynamic ATR barriers TP=**3.2**×NATR_21, SL=**1.6**×NATR_21 (aligned with labeling)
- Cooldown: 2 candles, timeout: 7 days

## 8. Report Requirements

Standard IS/OOS split. comparison.csv with baseline comparison.
