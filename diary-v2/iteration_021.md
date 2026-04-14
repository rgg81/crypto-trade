# Iteration v2/021 Diary

**Date**: 2026-04-15
**Type**: EXPLORATION (drop NEAR + 5-seed ensemble)
**Parent baseline**: iter-v2/019
**Decision**: **NO-MERGE** — ensemble made strategy too conservative, both IS and OOS regressed

## Result vs iter-v2/019

| Metric | iter-v2/019 | iter-v2/021 | Δ |
|---|---|---|---|
| Total trades | 461 | 351 | **−24%** |
| OOS trades | 117 | 69 | **−41%** |
| IS monthly Sharpe | +0.50 | **+0.36** | **−0.14** |
| OOS monthly Sharpe | +2.34 | **+1.75** | **−0.59** |
| OOS trade Sharpe | +2.60 | +1.89 | −0.71 |
| IS trade Sharpe (qs) | +0.57 | +0.42 | −0.15 |

Every metric regressed. **NO-MERGE**.

## Root cause — ensemble thinning

The 5-seed ensemble averages predictions from 5 independently-trained
LightGBM models. For a signal to fire, at least 3 of 5 models need
to agree (majority vote). This is MORE CONSERVATIVE than 1-seed.

**Effect on trade count**:
- Drop NEAR removed ~72 IS + 22 OOS trades (accounted for 94 of the 110 total trade reduction)
- 5-seed ensemble agreement further removed ~26 OOS trades (from 95 to 69)

**Effect on monthly Sharpe**:
- Mean PnL roughly proportional to trade count (fewer trades → lower mean)
- Monthly std dominated by the rare bad month (unchanged or slightly higher)
- Net: Sharpe DROPS because mean drops faster than std

**The ensemble is the wrong lever for monthly Sharpe**. The user
wants MORE balance (higher IS Sharpe), which requires more stable
monthly distribution. Making the strategy more conservative
(fewer signals) INCREASES variance contribution per trade.

## Lesson

**Ensemble averaging reduces prediction noise but also reduces
signal count**. For sparse strategies that need MORE trades (not
fewer), ensembling is the wrong tool.

Better approaches for balanced Sharpe:
1. Add more symbols (increase trade density)
2. Replace a bad symbol with a better one (keep count, improve quality)
3. Add features to improve per-trade signal (retrain model)

## Next iteration plan (iter-v2/022)

Revert iter-021's changes. Keep iter-v2/019's 4-symbol, 1-seed
structure. **Replace NEAR with LTCUSDT**:
- LTC's 2022 drawdown was ~−60% (vs NEAR's −92%)
- Oldest altcoin, stable, PoW (different narrative from current DOGE/SOL/XRP)
- LTC features exist in `data/features_v2/LTCUSDT_8h_features.parquet`
- Low correlation to existing basket
- Will test 1-seed, then 10-seed if promising

## MERGE / NO-MERGE

**NO-MERGE**. Cherry-pick the docs (research brief + this diary)
and the monthly-Sharpe metric addition (useful for iter-022+).
Revert the ensemble + drop-NEAR changes.
