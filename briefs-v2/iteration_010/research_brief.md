# Iteration v2/010 Research Brief

**Type**: EXPLORATION (symbol replacement)
**Track**: v2 — diversification arm
**Parent baseline**: iter-v2/005 (10-seed mean +1.297)
**Date**: 2026-04-14
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

## Motivation

iter-v2/006-009 are all NO-MERGE (4 consecutive failures). Every
NEAR-related intervention (ADX threshold, Optuna depth, NEAR 12mo
window, NEAR 18mo window) failed to lift the 10-seed mean above
iter-v2/005's +1.297. The common thread: NEAR's per-trade expectancy
is structurally bounded by its 32% TP / 59% SL exit distribution, and
its 2022 −92% crash dominates training data regardless of window length.

iter-v2/010 is the **final 4th-symbol replacement attempt**: swap NEAR
with FILUSDT. FIL is NEAR's closest screening-profile sibling (v1 corr
0.665 same, 4,845 IS candles vs 4,847, $257M daily volume vs $240M)
but with a **different 2022 trajectory** (FIL −87% peak-to-trough vs
NEAR −92%). FIL is in a different category (decentralized storage
vs L1 blockchain), which might change the exit distribution.

## Hypothesis

FIL as Model H should yield a 4th contributor with:

1. **Different exit distribution** than NEAR's 32/59/9 (TP/SL/timeout)
2. **Better per-trade expectancy** because 2022 was slightly less hostile
3. **Less cross-seed variance** because FIL's hyperparameter landscape
   might be smoother than NEAR's

If any of these are materially true, the 10-seed mean should rise
above +1.297.

## Failure-mode prediction (pre-registered)

Most likely way to fail: **FIL has the same structural problems as
NEAR**. All cryptocurrency L1-adjacent alts with similar screening
profiles share the 2022 bear training domination. 10-seed mean lands
at +1.15-1.30, similar to NEAR-based iterations. Signal: FIL OOS
weighted PnL within ±5% of NEAR's ±8.71% range and similar
exit-reason distribution.

**If this failure mode confirms**, the 4th-symbol slot is structurally
bounded — no v1-uncorrelated alt with a 2022 bear training period can
exceed the current baseline. The v2 track has found its ceiling.

## Configuration (one variable changed from iter-v2/005)

| Setting | iter-v2/005 | iter-v2/010 | Changed? |
|---|---|---|---|
| Model H symbol | NEARUSDT | **FILUSDT** | **Yes** |
| Everything else | Same | Same | — |

## Research Checklist Coverage

This is the 5th iteration under the "3+ consecutive NO-MERGE" rule
(006, 007, 008, 009 NO-MERGE). Full research checklist applied in
iter-v2/009; iter-v2/010 is a narrow single-variable test of the
4th-symbol replacement hypothesis. No new categories added — the
research arguments in iter-v2/009's brief (Categories B, C, E, I)
apply to this iteration as well.

## Success Criteria

Primary: 10-seed mean OOS Sharpe > +1.297.

Hard constraints: same as iter-v2/009.

## Section 6: Risk Management Design

### 6.1-6.2

Unchanged from iter-v2/005. Same 5 gates, same thresholds.

### 6.3 Pre-registered failure-mode prediction

"The most likely way iter-v2/010 fails is that FIL has fundamentally the
same structural problems as NEAR — 2022 bear domination, marginal
per-trade expectancy, non-monotonic Optuna landscape. FIL OOS weighted
PnL lands within ±5% of NEAR's, and the 10-seed mean lands at
+1.15-1.30 (within noise of baseline). If this confirms, iter-v2/011
should pivot entirely off 4th-symbol tuning — no alt with similar
screening can break through iter-v2/005's ceiling."

### 6.4-6.5

Unchanged.
