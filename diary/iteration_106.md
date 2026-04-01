# Iteration 106 Diary

**Date**: 2026-04-01
**Type**: EXPLORATION
**Merge Decision**: NO-MERGE (EARLY STOP in 2025, OOS Sharpe +0.48 < baseline +1.01)

**Trigger**: Year 2025: PnL=-6.5%, WR=34.6%, 107 trades. Early-stopped in OOS period.

**OOS cutoff**: 2025-03-24

## Hypothesis

Heterogeneous ensemble (5 LGBMs + 1 XGBoost + 1 CatBoost) provides genuine directional diversity that identical-seed LGBMs cannot.

## What Happened

IS metrics IMPROVED: Sharpe +0.80 (vs +0.73), MaxDD 73.7% (vs 92.9%). The heterogeneous ensemble genuinely helped IS performance.

OOS metrics DEGRADED: Sharpe +0.48 (vs +1.01), WR 37.1% (vs 42.1%). Early-stopped in 2025.

This is a textbook overfitting pattern: better IS, worse OOS. The XGB/CB models learn slightly different overfit patterns from the same training data. When averaged with LGBMs, they add noise to the predictions rather than improving them.

## Per-Symbol Analysis

| Symbol | IS WR | OOS WR | Baseline OOS WR |
|--------|-------|--------|-----------------|
| ETH | 43.8% | 43.5% | 50.0% |
| BTC | 41.9% | 30.2% | 33.3% |

ETH OOS WR dropped from 50.0% to 43.5% (still profitable at 2:1 RR). BTC dropped from 33.3% to 30.2% (below break-even). The heterogeneous ensemble hurt both symbols but killed BTC.

## Key Insight: Different Algorithms ≠ Better Signal

XGBoost and CatBoost use fundamentally different tree-building algorithms than LightGBM. But they train on the SAME data with the SAME features. Their "diversity" comes from algorithmic inductive bias differences, not from seeing different information. This diversity doesn't help because:

1. If LightGBM overfits to pattern X, XGBoost overfits to a similar pattern X' (since all patterns come from the same data)
2. Averaging X and X' doesn't cancel overfitting — it just averages two slightly different overfit signals
3. The only way to get useful diversity is from different DATA (different features, different symbols, different timeframes)

## Exploration/Exploitation Tracker

Last 10 (iters 097-106): [E, E, E, X, E, E, E, E, E, **E**]
Exploration rate: 9/10 = 90%
Type: **EXPLORATION** (heterogeneous ensemble)

## Lessons Learned

1. **Heterogeneous ensembles don't help when all models see the same data.** Diversity in algorithm is insufficient — need diversity in information.
2. **IS improvement without OOS improvement = overfitting.** The 10% IS Sharpe gain was illusory.
3. **XGBoost and CatBoost with translated LGBM params are not well-calibrated.** The Optuna params were optimized for LightGBM's leaf-wise growth. XGBoost's level-wise and CatBoost's ordered boosting respond differently to the same hyperparams.

## FINAL ASSESSMENT: 14 Consecutive NO-MERGE

Iterations 094-106 have exhaustively tested:
- Feature changes (094, 095, 100)
- Weight changes (097, 098)
- Per-symbol models (099)
- Post-hoc filtering (102, 103, 104)
- Symbol expansion (105)
- Heterogeneous ensemble (106)
- Baseline validation (096, 101)

**Every approach has failed.** The baseline (iter 093) with OOS Sharpe +1.01 is the definitive optimum for this LightGBM-based approach on BTC+ETH with 8h candles.

## Next Steps

**Accept the baseline as the production model.** Further iteration within this framework is not productive. The next meaningful step is live deployment or a fundamentally different approach (different timeframe, different asset class, or different modeling paradigm entirely).
