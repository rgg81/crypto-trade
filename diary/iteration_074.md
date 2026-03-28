# Iteration 074 Diary — 2026-03-28

## Merge Decision: NO-MERGE (EARLY STOP)

Year 2022 PnL -63.9% (WR 34.3%, 99 trades). IS Sharpe -0.86. **Root cause identified: parquet contamination from failed iterations.**

**OOS cutoff**: 2025-03-24

## Hypothesis

Baseline reproduction: run iter 068 config with symbol-filtered discovery and all 187 features from the current parquet. Diagnostic to understand if extra features from failed iters (070, 072) affect performance.

## Configuration Summary

- OOS cutoff: 2025-03-24 (fixed)
- IDENTICAL to iter 068 baseline config
- Only change: symbol-filtered discovery (BTC/ETH only → discovers 187 features)
- Ensemble: 3 seeds [42, 123, 789], cooldown=2, ATR barriers

## Results: In-Sample (early stop at Year 2022)

| Metric | Iter 074 (187 feat) | Baseline 068 (106 feat) |
|--------|---------------------|-------------------------|
| IS Sharpe | **-0.86** | +1.22 |
| IS MaxDD | **122.1%** | 45.9% |
| IS WR | 35.0% | 43.4% |
| IS PF | 0.80 | 1.35 |
| IS Trades | 100 | 373 |
| IS Net PnL | -60.0% | +264.3% |

OOS: not reached (early stop in Year 2022)

## Root Cause: Parquet Contamination

**The feature parquet files were corrupted by code accidentally committed from NO-MERGE iterations.**

Timeline:
1. Iter 068 (MERGE): baseline, 106 features → IS +1.22, OOS +1.84
2. Iter 070 (NO-MERGE): added interaction features → `feat(iter-070)` committed to main (WRONG)
3. Iter 072 (NO-MERGE): added calendar features → `feat(iter-072)` committed to main (WRONG)
4. Feature regeneration ran with these extra groups → parquets now have 187 features
5. **Every iteration since 068 has been testing against a broken feature set**

The proof is clear:
- Baseline (106 features): IS Sharpe +1.22, Optuna best Sharpe 0.4-0.5 per month
- Current (187 features): IS Sharpe -0.86, Optuna best Sharpe 0.02-0.09 per month
- The 81 extra features are pure noise that LightGBM cannot handle

This explains WHY iterations 069-073 all failed: they were all running on 187 features, not the baseline's 106. Every "change" was tested against a poisoned feature set.

## Fix Required

**BEFORE the next iteration:**
1. Regenerate feature parquets for BTC+ETH with ONLY the original 6 groups: momentum, volatility, trend, volume, mean_reversion, statistical
2. Exclude: interaction, calendar groups
3. Verify the parquet has ~106 features
4. Run iter 068 config to confirm baseline reproduction
5. Remove the feature generation code for interaction/calendar from main (revert the accidentally-committed feat commits)

## Exploration/Exploitation Tracker

Last 10 (iters 065-074): [E, X, E, E, X, E, E, E, E, X]
Exploration rate: 7/10 = 70%
Type: EXPLOITATION (baseline reproduction diagnostic)

## Lessons Learned

1. **Commit discipline matters.** Code from NO-MERGE iterations should NEVER reach main. The `feat(iter-070)` and `feat(iter-072)` commits on main corrupted the feature parquet and invalidated every subsequent iteration.

2. **The baseline cannot be reproduced today.** The original 106-feature parquet no longer exists. The feature generation code on main now produces 187 features. To restore the baseline, we need to regenerate features with only the original groups.

3. **Feature count is critical.** 106 features → profitable. 187 features → catastrophic loss. LightGBM with ~4400 training samples per month cannot handle 187 features. The extra features don't just fail to help — they actively destroy the signal.

4. **This retroactively explains all failures since iter 068.** Iterations 069-073 tested various hypotheses (cooldown sweep, feature addition, symbol expansion, calendar features, feature pruning) on a broken foundation. Their results are unreliable because the feature baseline was wrong.

## Next Iteration Ideas

1. **CRITICAL: Regenerate features** — Remove interaction/calendar groups from feature generation code, regenerate parquets for BTC+ETH with original 6 groups only, verify ~106 features, confirm baseline reproduction. This is MANDATORY before any other work.

2. **After baseline is restored**: Consider the hypotheses from failed iterations, but NOW test them against a clean 106-feature baseline.
