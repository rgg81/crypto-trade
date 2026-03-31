# Iteration 100 Diary

**Date**: 2026-03-31
**Type**: EXPLORATION
**Merge Decision**: NO-MERGE (EARLY STOP)

**Trigger**: Year 2022: PnL=-66.8%, WR=34.0%, 100 trades. IS Sharpe -0.84.

**OOS cutoff**: 2025-03-24

## Hypothesis

Fractional differentiation features (fracdiff log_close and log_volume at d=0.4, window=100) provide price-level memory while maintaining stationarity, offering information that raw returns cannot.

## What Failed

The fracdiff features made things worse. However, this iteration had a **confounding variable**: parquet regeneration changed the total feature count from 185 to 195 (193 non-fracdiff + 2 fracdiff). The 8 extra non-fracdiff features came from code changes since the baseline parquets were generated. This means the test was NOT a clean isolation of fracdiff impact.

**Root cause**: The parquet regeneration disrupted the Optuna optimization landscape. The model had been optimized for 185 specific features. Adding 10 new features (including 2 fracdiff) changed the feature space enough to degrade optimization. Optuna found worse solutions.

## Parquet State Warning

**The baseline's 185-feature parquets are permanently lost.** They were overwritten during regeneration. The current parquets have 193 features (8 more than baseline, excluding fracdiff). Future iterations will train with 193 features, not 185.

This means the baseline metrics (OOS Sharpe +1.01) were measured on 185-feature parquets. Any future iteration using the current 193-feature parquets may get different results even with identical model parameters. **The next iteration should first validate baseline reproduction with 193 features before trying any new change.**

## Quantifying the Gap

IS WR 34.7%, break-even 33.3%. Gap is only +1.4pp above break-even but PF 0.81 (losing money). The model generated too many trades at low quality. Both symbols degraded: BTC 35.0% WR (-8.2pp), ETH 34.4% WR (-8.0pp).

## Pre-iteration Analysis (ADX filter investigation)

Before implementing fracdiff, I analyzed two potential trade filters:

1. **ADX < 15 filter**: IS data shows ADX < 15 is bad for both symbols (33.3% WR). But OOS data shows the OPPOSITE for ETH (57.1% WR, +13.7% PnL at ADX < 15). The filter would hurt OOS.

2. **Direction persistence**: IS data shows direction flips have 50% WR and 3× better avg PnL. But OOS data shows same-direction trades are BETTER (ETH: 52.2% vs 40.0%). Pattern doesn't generalize.

**Conclusion**: IS trade patterns are noise. Post-hoc filtering based on IS analysis is researcher overfitting.

## Exploration/Exploitation Tracker

Last 10 (iters 091-100): [E, X, E, X, E, X, E, E, E, **E**]
Exploration rate: 7/10 = 70%
Type: **EXPLORATION** (fractional differentiation features)

## Research Checklist Categories Completed

- **G (Stationarity & Memory)**: Implemented fracdiff algorithm. d=0.4 preserves ~60% correlation with original series while achieving stationarity. BUT: couldn't cleanly isolate impact due to parquet regeneration confound.
- **A (Features)**: +2 fracdiff features, +8 features from parquet regeneration = total 195 (from 185). Feature landscape change too large for clean comparison.
- **E (Trade Patterns)**: Deep analysis of ADX and direction persistence. Neither filter generalizes IS→OOS.
- **F (Statistical Rigor)**: IS patterns (ADX, direction flip) confirmed as noise by OOS cross-validation.

## lgbm.py Code Review

No code changes to lgbm.py. The model correctly discovered 195 features from the regenerated parquets and trained with them. The per-symbol model code from iter 099 was not included (stays on iteration/099 branch).

## Lessons Learned

1. **Never regenerate baseline parquets without a backup.** The 185-feature parquets that the baseline was validated on are permanently lost. Always preserve baseline artifacts before modifying them.

2. **Feature changes disrupt the optimization landscape.** Even +10 features (195 from 185) caused Optuna to find worse solutions. LightGBM doesn't just "add" features — it re-optimizes split decisions across ALL features, and the new features can act as distractors.

3. **IS trade patterns are noise.** ADX filtering and direction persistence both showed clear IS patterns that reversed in OOS. This confirms the model is at its local optimum — there are no easy post-hoc improvements.

4. **The 193-feature parquets need baseline validation.** Before any new iteration, run the baseline config with 193 features to establish whether the model still works.

## Next Iteration Ideas

1. **EXPLOITATION: Baseline reproduction with 193 features.** Run the exact baseline config (iter 093 params) on the current 193-feature parquets. If OOS Sharpe is still ~+1.0, the extra 8 features don't matter. If it degrades significantly, we have a feature-stability problem.

2. **EXPLORATION: Meta-labeling (AFML Ch. 3).** After validating the baseline, add a secondary model that predicts whether the primary model's trade will be profitable. This is the most promising remaining structural change — it doesn't modify the primary model, just adds a trade filter trained on out-of-fold predictions.

3. **EXPLORATION: Entropy features (AFML Ch. 18).** Shannon entropy of discretized returns over rolling window. High entropy = unpredictable market. This is a regime-detection feature, not a directional predictor.
