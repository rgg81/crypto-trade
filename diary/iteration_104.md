# Iteration 104 Diary

**Date**: 2026-04-01
**Type**: EXPLORATION
**Merge Decision**: NO-MERGE (OOS Sharpe +0.97 < baseline +1.01, filter has negligible effect)

**OOS cutoff**: 2025-03-24

## Hypothesis

Require ≥4/5 ensemble models to agree on direction to filter low-conviction signals.

## What Happened

The filter removed only 4 trades total (3 IS + 1 OOS). The 5-seed ensemble agrees on direction >99% of the time. Seeds differ in probability magnitude, not direction. The filter is effectively a no-op.

OOS Sharpe dropped slightly (+0.97 vs +1.01) because the 4 removed trades happened to be slightly profitable on average.

## Key Insight: Seeds Don't Provide Directional Diversity

The 5 ensemble seeds (42, 123, 456, 789, 1001) share identical training data, labels, features, and Optuna hyperparameters. They differ only in LightGBM's internal randomness (subsample, colsample_bytree, tree building order). This produces models that are near-identical in directional predictions — their value comes from averaging probability magnitudes, reducing confidence noise, not from directional diversity.

To get genuine directional diversity, you'd need:
- Different feature subsets per model (random subspace method)
- Different training data per model (bagging)
- Different model types (heterogeneous ensemble)

## Exploration/Exploitation Tracker

Last 10 (iters 095-104): [E, X, E, E, E, X, E, E, E, **E**]
Exploration rate: 8/10 = 80%
Type: **EXPLORATION** (ensemble disagreement filter)

## Conclusion: 12 Consecutive NO-MERGE

Iterations 094-104 (12 consecutive) have tested:
- Feature changes: pruning (094,095), fracdiff (100) — all failed
- Weight changes: uniqueness (097), time decay (098) — all failed
- Architecture: per-symbol (099) — failed
- Post-hoc filtering: meta-labeling (102,103), ensemble agreement (104) — all failed or no effect
- Sharpe fix (096) — no effect
- Baseline reproduction (101) — exact match

**The model is definitively at its local optimum.** OOS Sharpe +1.01, 107 trades, +51% return. The only path to improvement is adding more symbols (more trades, more diversification) or fundamentally changing the model type.

## Next Iteration Ideas

1. **Accept baseline as final for BTC+ETH.** Deploy with current parameters. Focus engineering effort on live trading infrastructure rather than further optimization.

2. **Symbol universe expansion (Stage 2)**: Screen SOL, BNB, XRP through the 5-gate qualification protocol. Adding 1-2 qualified symbols would increase trade count and potentially improve Sharpe through diversification.

3. **Heterogeneous ensemble**: Replace 5 identical-seed LightGBMs with 3 different model types (LightGBM + XGBoost + CatBoost). This would provide genuine directional diversity.
