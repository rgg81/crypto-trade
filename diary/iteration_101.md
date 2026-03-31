# Iteration 101 Diary

**Date**: 2026-03-31
**Type**: EXPLOITATION
**Merge Decision**: NO-MERGE (baseline reproduction, no changes to merge)

**OOS cutoff**: 2025-03-24

## Purpose

Validate that the baseline (iter 093) can be reproduced after parquet regeneration in iter 100 destroyed the original 185-feature parquets.

## What Happened

**Attempt 1 (193 features)**: EARLY STOP. Year 2022: PnL=-26.5%, WR=37.4%. The 8 extra features (2 calendar + 6 interaction) from groups added in iters 070/072 acted as distractors, causing Optuna to find worse solutions.

**Attempt 2 (185 features)**: EXACT REPRODUCTION. IS Sharpe +0.7339, OOS Sharpe +1.0129. All metrics identical to baseline iter 093. The 5-seed ensemble is fully deterministic.

## Critical Discovery

**Calendar and interaction features are confirmed harmful.** When included in the parquets (193 features), they cause early stop in 2022. When excluded (185 features), the model reproduces perfectly. These features were tested in iters 070 and 072 and found harmful — they should NEVER be included in BTC/ETH parquets.

**Parquet regeneration rule**: Use ONLY 6 groups: momentum, volatility, trend, volume, mean_reversion, statistical. The feature `__init__.py` registers 8+ groups (including calendar, interaction, fracdiff), but only these 6 produce the validated 185-feature set.

## Exploration/Exploitation Tracker

Last 10 (iters 092-101): [X, E, X, E, X, E, E, E, E, **X**]
Exploration rate: 6/10 = 60%
Type: **EXPLOITATION** (baseline reproduction)

## Next Iteration Ideas

The model is confirmed at OOS Sharpe +1.01 with 185 features. Every structural change since iter 093 has failed (per-symbol, pruning, weighting, fracdiff). The model is at its local optimum.

1. **EXPLORATION: Meta-labeling (AFML Ch. 3).** Secondary model trained on out-of-fold primary predictions. Predicts whether each trade will be profitable. Uses meta-features: primary confidence, NATR, ADX, rolling WR. Doesn't modify the primary model — just adds a filter. This is the most promising remaining AFML technique.

2. **EXPLORATION: Dynamic confidence threshold per month.** Instead of a single Optuna-optimized threshold for the whole training period, compute a separate threshold for each Optuna CV fold. Use the MEDIAN across folds as the production threshold. This addresses months where the model is overconfident.

3. **EXPLORATION: Reduced Optuna search space for regularization.** The baseline allows min_child_samples [5, 100] and max_depth [3, 5]. With 185 features and ~4,320 samples (ratio 23), the model might benefit from stronger regularization: min_child_samples [20, 200], max_depth [2, 4]. This forces the model to learn simpler patterns.
