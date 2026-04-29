# Iteration v2/025 Diary

**Date**: 2026-04-15
**Type**: EXPLORATION (3-symbol DOGE+SOL+XRP, drop NEAR)
**Parent baseline**: iter-v2/019
**Decision**: **NO-MERGE** — both means well below 1.0

## Results

**10-seed mean**:
| Metric | Value |
|---|---|
| IS monthly Sharpe | **+0.4999** |
| OOS monthly Sharpe | **+0.5904** |
| OOS trade Sharpe | +0.8103 |
| Profitable seeds | 9/10 |
| Balance ratio | **1.18x** (very balanced) |

**Primary seed 42**:
- IS monthly +0.67, OOS monthly +1.31 (both >0.5)
- Trade Sharpe IS +0.78, OOS +1.70
- OOS MaxDD 56.73% (high — hit-rate gate fires less with sparse stream)

## Pattern across iterations 021-025

| Iter | Config | Mean IS | Mean OOS | Balance |
|---|---|---|---|---|
| 019 baseline (4 sym + NEAR) | | ~0.40 est | ~1.10 est | 2.7x |
| 021 (3 sym + 5-seed ensemble) | | +0.36 | +1.75 | 4.9x |
| 023 (TRX replace NEAR) | | +0.61 | +0.70 | 1.14x |
| 024 (5 sym add TRX) | | +0.64 | +0.97 | 1.51x |
| **025 (3 sym, drop NEAR)** | | **+0.50** | **+0.59** | **1.18x** |

**No symbol combination pushes 10-seed mean above 1.0 on both IS and OOS.**

## The diagnostic

Symbol-space exploration has hit a ceiling. Primary seed 42 varies
from +1.31 to +2.60 on OOS across iterations, but 10-seed mean
clusters around +0.6-1.0. The seed-level variance dominates.

Underlying issue: sparse strategy (100-160 trades/seed/year) has
high monthly variance regardless of symbol choice. Each model seed
finds different local optima, producing divergent trade
distributions.

Path forward cannot be symbol choice. Must change the model
itself.

## Next iteration (iter-v2/026)

User feedback: "try other symbols, features". Symbols exhausted.
**Pivot to features**.

Plan: Add BTC cross-asset features to v2's feature catalog.
Currently v2 uses 35 features, none of which are cross-asset.
Adding BTC 3/7/14-day returns and BTC realized vol should give
the model cross-asset regime awareness, which could reduce
per-seed variance.

This is expensive: requires regenerating feature parquets for all
v2 symbols (~10 min) plus model retraining. But it's the
user-requested direction.

Candidates for new features:
- `btc_ret_3d` — BTC 3-day log return
- `btc_ret_7d` — BTC 7-day log return
- `btc_ret_14d` — BTC 14-day log return
- `btc_vol_14d` — BTC 14-day realized vol
- `sym_vs_btc_ret_7d` — symbol's 7-day return minus BTC's 7-day return

## MERGE / NO-MERGE

**NO-MERGE**. Neither mean reaches 1.0. Balance is achieved (1.18x)
but both metrics are too low in absolute terms to be a production
baseline.
