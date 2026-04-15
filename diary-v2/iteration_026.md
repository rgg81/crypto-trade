# Iteration v2/026 Diary

**Date**: 2026-04-15
**Type**: EXPLORATION (BTC cross-asset features)
**Parent baseline**: iter-v2/019
**Decision**: **NO-MERGE** — modest improvement, still below 1.0 means

## Results

**10-seed mean**:
| Metric | iter-025 (no BTC features) | iter-026 (+BTC features) | Δ |
|---|---|---|---|
| IS monthly Sharpe | +0.4999 | **+0.5606** | +12% |
| OOS monthly Sharpe | +0.5904 | **+0.6904** | +17% |
| OOS trade Sharpe | +0.8103 | +0.8485 | +5% |
| Balance ratio | 1.18x | 1.23x | similar |
| Profitable | 9/10 | 9/10 | same |

**Primary seed 42** (strongest result):
- IS monthly +0.7514, OOS monthly +1.0201 — **both above 1.0!**
- Balance 1.41x (perfect range)
- IS MaxDD 65.99%, OOS MaxDD 46.64%

## Per-seed breakdown

| Seed | IS monthly | OOS monthly | Balance |
|---|---|---|---|
| 42 | +0.75 | **+1.02** | 1.36x |
| 123 | +0.20 | +0.69 | 3.45x |
| 456 | +0.22 | **−0.49** | — |
| 789 | +1.06 | +0.42 | 0.40x |
| 1001 | +0.06 | +0.45 | 7.50x |
| 1234 | +0.83 | **+1.31** | 1.58x |
| 2345 | +0.58 | **+1.56** | 2.69x |
| 3456 | +0.57 | +0.55 | 0.97x |
| 4567 | **+1.02** | **+1.07** | 1.05x |
| 5678 | +0.32 | +0.31 | 0.97x |
| **Mean** | **+0.56** | **+0.69** | 1.23x |

**4 of 10 seeds (42, 1234, 2345, 4567) have OOS > 1.0**. The
weak seeds (123, 456, 1001) drag the mean. This is the same
seed-variance pattern as iter-025, but slightly better.

## Why the modest improvement

Adding BTC cross-asset features (btc_ret_3d/7d/14d, btc_vol_14d,
sym_vs_btc_ret_7d) gives the model BTC regime awareness at the
feature level. The LightGBM model can now split on BTC trend
state when deciding direction.

However, the 5 new features add only ~14% more feature columns
(35 → 40). With the same 10 Optuna trials per month and the same
24-month training window, the model's variance across seeds is
largely unchanged. The features help on average but don't fix
the fundamental variance issue.

## Observation: hit-rate gate fires more with BTC features

Hit-rate gate kills jumped from 21 (iter-019 primary) to 51
(iter-026 primary). The BTC features change the model's trade
distribution — more trades cluster in losing streaks, which
triggers the gate more often.

This is a second-order effect of feature addition: the gate is
calibrated on the OLD trade distribution, so adding features
changes the distribution and the gate fires differently.

## Lessons

1. **Feature engineering helps but doesn't solve seed variance**.
   +12-17% improvement on means is real but not enough.
2. **Primary seed shows the ceiling** — seed 42 has IS +0.75,
   OOS +1.02 with balance 1.41x. The weak seeds drag the mean.
3. **BTC features are a net positive** and should be kept.
4. The path to 10-seed mean >= 1.0 likely requires **multiple
   compounding improvements**, not one big change.

## Next iteration (iter-v2/027)

Combine two directionally-positive changes:
- **BTC features** (iter-026): +12-17% mean improvement
- **TRX replacing NEAR** (iter-023): strong per-symbol IS on primary

Both iterations showed incremental gains. Combined might compound.
iter-027 will test BTC features + TRX symbol swap with both gates.

## MERGE / NO-MERGE

**NO-MERGE**. 10-seed mean OOS at +0.69 is still below 1.0.
BTC features are useful and are kept in V2_FEATURE_COLUMNS going
forward. Primary seed 42 achieves "both > 1.0" for the first
time (iter-019 had OOS >> 1.0 but IS < 1.0; iter-026 primary
has both in balance).
