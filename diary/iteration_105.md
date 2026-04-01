# Iteration 105 Diary

**Date**: 2026-04-01
**Type**: EXPLORATION
**Merge Decision**: NO-MERGE (EARLY STOP)

**Trigger**: Year 2022: PnL=-32.5%, WR=32.0%, 122 trades. IS Sharpe -0.41.

**OOS cutoff**: 2025-03-24

## Hypothesis

Adding BNB (lowest NATR ratio 1.2x) to the pooled model increases trade count and diversification.

## What Failed

BNB failed Gate 4 (pooled compatibility):
- BNB per-symbol WR: 27.6% (below break-even 33.3%)
- BTC WR degraded: 43.2% → 28.6% (-14.6pp!)
- ETH WR degraded: 42.4% → 36.5% (-5.9pp)

The pooled model learned averaged patterns across 3 symbols, producing a signal that worked for none of them individually. The 3-symbol model's optimization landscape is fundamentally different from 2-symbol — Optuna finds different hyperparameters that don't serve BTC or ETH as well.

## Key Insight: CV Gap Increase Hurts

The CV gap went from 44 to 66 rows (3 symbols × 22 candles). This means 50% more data is excluded between CV folds. With the same 5 folds, more data is wasted, reducing effective training samples per fold. Combined with the larger gap, Optuna has less signal to optimize against.

**Math**: With ~6,480 samples (3 symbols × 24mo), 5 folds = 1,296 per fold. Gap = 66 rows = 5.1% of each fold. The gap cost per fold increased from 3.4% (2-sym) to 5.1% (3-sym). This compounds across 5 folds.

## Exploration/Exploitation Tracker

Last 10 (iters 096-105): [X, E, E, E, X, E, E, E, E, **E**]
Exploration rate: 8/10 = 80%
Type: **EXPLORATION** (symbol expansion)

## Research Checklist Categories Completed

- **B (Symbol Universe)**: Full screening of 7 candidates. NATR ratios, BTC correlations computed. BNB selected as best candidate (lowest NATR 1.2x). Fails Gate 4 — WR below break-even.
- **E (Trade Patterns)**: Per-symbol breakdown shows BNB drags the pool. BTC WR collapses from 43.2% to 28.6%.
- **F (Statistical Rigor)**: 122 IS trades in 2022 is enough for convergence — the 31.7% WR is genuinely below break-even, not a small-sample artifact.
- **H (Overfitting)**: Adding a 3rd symbol is not a multiple-testing risk.

## Lessons Learned

1. **Symbol expansion with pooled model is harder than expected.** Even BNB (the most compatible candidate by NATR) degrades the model. The pooled model's hyperparameters are co-optimized for BTC+ETH and don't generalize to 3 symbols.

2. **CV gap scales with symbol count.** 3 symbols → gap=66 (50% more than 44). This reduces effective CV training data, making optimization less reliable.

3. **BTC WR collapse is the red flag.** BTC went from 43.2% to 28.6% when BNB was added. This means the model learned BNB-influenced patterns that actively hurt BTC predictions. The symbols' dynamics are too different for a single model to serve all three.

## Next Iteration Ideas

1. **EXPLORATION: Heterogeneous ensemble.** Replace 5 identical-seed LGBMs with LightGBM+XGBoost+CatBoost. Each model type learns different patterns, providing genuine diversity.

2. **EXPLORATION: Accept baseline and focus on live deployment.** OOS Sharpe +1.01 is profitable. Further iterations may not improve it. Shift effort to live trading infrastructure (API execution, position management, monitoring).

3. **EXPLORATION: Reduced Optuna search space.** Narrow the hyperparameter ranges based on what the baseline consistently selects. If training_days always lands at 300-500, narrow the range to [250, 500]. Fewer options → faster convergence → potentially better solutions. But this is EXPLOITATION (parameter tuning).
