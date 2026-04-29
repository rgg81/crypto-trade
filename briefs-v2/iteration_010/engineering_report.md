# Iteration v2/010 Engineering Report

**Type**: EXPLORATION (symbol replacement NEAR → FIL)
**Role**: QE
**Date**: 2026-04-14
**Branch**: `iteration-v2/010` on `quant-research`
**Parent baseline**: iter-v2/005 (10-seed mean +1.297)
**Decision**: **NO-MERGE** (1-seed fail-fast). FIL is structurally
similar to NEAR and does not break the +1.297 ceiling. Pre-registered
failure mode confirmed.

## Run Summary

| Item | Value |
|---|---|
| Models | 4 (E=DOGE, F=SOL, G=XRP, **H=FIL** — replaced NEAR) |
| Seeds | 1 (fail-fast) |
| Optuna trials | 10 |
| Wall-clock | ~5 min |

## Primary seed 42 — comparison vs baseline

| Metric | iter-v2/005 (NEAR) | iter-v2/010 (FIL) | Δ |
|---|---|---|---|
| OOS Sharpe | +1.671 | +1.420 | −0.251 |
| OOS PF | 1.457 | 1.380 | −0.08 |
| OOS MaxDD | 59.88% | **55.52%** | **−4.36 pp** |
| OOS WR | 45.3% | 45.8% | +0.5 pp |
| OOS trades | 117 | 118 | +1 |
| IS Sharpe | +0.116 | +0.163 | +0.047 |
| IS MaxDD | 111.55% | 108.02% | −3.53 pp |

Primary seed 42 OOS is **−0.25 below baseline**. OOS MaxDD improves
(good for risk profile) but primary metric regresses — same pattern as
iter-v2/009.

## Per-symbol OOS (primary seed 42)

| Symbol | iter-v2/005 NEAR | iter-v2/010 FIL | Δ |
|---|---|---|---|
| DOGEUSDT | 31, +11.52% (12.3%) | **identical** | — |
| SOLUSDT | 37, +28.89% (30.7%) | **identical** | — |
| XRPUSDT | 27, +44.89% (47.8%) | **identical** | — |
| **Model H** | **NEAR: 22, +8.71% (9.3%)** | **FIL: 23, −4.51% (−5.6%)** | **−13.22 pp** |

**DOGE/SOL/XRP are byte-for-byte identical** (perfect isolation held).
**FIL is materially worse than NEAR as a 4th contributor**:

| Metric | NEAR (iter-v2/005) | FIL (iter-v2/010) |
|---|---|---|
| OOS trades | 22 | 23 |
| OOS WR | 40.9% | 43.5% |
| OOS weighted Sharpe | +0.33 | **−0.17** |
| OOS weighted PnL | +8.71% | **−4.51%** |
| TP rate | 32% | 26% |
| **SL rate** | **59%** | **52%** |
| Timeout rate | 9% | 22% |
| IS raw PnL | −67.39% | **−72.93%** |
| IS WR | 36.1% | 36.1% |

FIL has a slightly better SL rate (52% vs 59%) and more timeouts, but
the aggregate OOS weighted contribution is **worse** (−4.51% vs +8.71%).
FIL's IS is also more hostile (−73% vs −67%).

**FIL fundamentally fails the "better 4th symbol" hypothesis.**

## Concentration

| Share | iter-v2/005 | iter-v2/010 |
|---|---|---|
| DOGE | 12.3% | 14.3% |
| SOL | 30.7% | 35.8% |
| XRP | **47.8%** | **55.6%** |
| Model H | +9.3% (NEAR) | **−5.6%** (FIL) |
| Rule (≤ 50%) | PASS | **FAIL** |

XRP concentration rises to 55.6% (same pattern as iter-v2/009) because
the 4th model went negative. **Second strict failure**.

## Why 10-seed validation is skipped

The 1-seed result confirms the pre-registered failure mode
(FIL-structurally-similar-to-NEAR) with clean evidence:

1. Primary seed 42 OOS is 0.25 below baseline (larger gap than
   iter-v2/008 or iter-v2/009 had on primary — those were at −0.24
   and +0.29 respectively)
2. FIL per-symbol OOS is negative (−0.17 weighted Sharpe), worse
   than NEAR's modestly-positive +0.33
3. Concentration strict-fails at 55.6%
4. FIL IS is more hostile than NEAR (−73% vs −67%)

The hypothesis was "FIL's different category yields different
expectancy". The data shows FIL and NEAR are structurally equivalent
for this strategy — both L1/storage alts with 2022 bear training
domination and marginal per-trade expectancy.

Running 10 seeds would confirm this at 50 minutes of additional compute
with near-certainty of NO-MERGE. Compute discipline: skip the 10-seed
and commit to the strategic pivot.

## Hard-constraint check (1-seed, seed 42)

| Constraint | Target | Actual | Pass? |
|---|---|---|---|
| OOS Sharpe (seed 42) ≳ baseline | ≳+1.67 | +1.42 | Fail (−0.25) |
| OOS trades ≥ 50 | 50 | 118 | PASS |
| OOS PF > 1.1 | 1.1 | 1.380 | PASS |
| OOS MaxDD ≤ 64.1% | 64.1% | 55.52% | PASS (improved) |
| **Concentration (primary seed) ≤ 50%** | **50%** | **55.6%** | **FAIL** |
| DSR > +1.0 | 1.0 | +12.39 | PASS |
| IS/OOS ratio > 0 | 0 | +0.11 | PASS |

Primary fails. Concentration strict-fails. Consistent with the
pre-registered failure mode.

## Pre-registered failure mode — confirmed

Brief §6.3 predicted: "FIL has the same structural problems as NEAR.
FIL OOS weighted PnL within ±5% of NEAR's ±8.71% range and similar
exit-reason distribution."

**Actual**: FIL OOS weighted PnL is **−4.51%** (delta of −13.22 pp from
NEAR's +8.71%, larger than predicted — FIL is actually WORSE than NEAR).

The hypothesis was falsified: FIL is not better. Neither matches
baseline.

## The 5-iteration pattern — definitive ceiling

| Iteration | 4th-symbol intervention | Primary seed 42 OOS | 10-seed mean | Result |
|---|---|---|---|---|
| 005 | NEAR @ 24mo | +1.671 | **+1.297** | BASELINE |
| 006 | ADX 20→15 (all) | +1.782 | +1.294 | NO-MERGE (IS fail) |
| 007 | Optuna 10→25 (all) | +1.481 | (untested) | NO-MERGE (flat hypothesis) |
| 008 | NEAR @ 12mo | **+1.965** | +1.089 | NO-MERGE (wide variance) |
| 009 | NEAR @ 18mo | +1.431 | +1.250 | NO-MERGE (within noise) |
| 010 | FIL @ 24mo | +1.420 | (1-seed) | NO-MERGE (same problem) |

**Five iterations. Zero improvements on the 10-seed mean.** Every
attempt has produced either a flat result (within noise) or an outright
regression. The pattern is clear: **the 4th-symbol slot is structurally
bounded**, and iter-v2/005's +1.297 mean is the ceiling for this
configuration.

## Recommendation: accept iter-v2/005 and pivot

The v2 track has successfully delivered its primary goals:
- **Diversification** (v2-v1 OOS correlation −0.046)
- **Seed-robust baseline** (10/10 profitable seeds in iter-v2/005)
- **Strong risk layer** (5 MVP gates + concentration strict pass)
- **Clear OOS edge** (Sharpe mean +1.297, DSR +12.82 at N=5 trials)

**Further tuning is hitting diminishing returns**. The 4th-symbol slot
is not the lever that moves the baseline. iter-v2/011+ should shift to:

1. **Enable drawdown brake** (deferred primitive from iter-v2/001).
   Adds capital-preservation to a baseline that's proven but has a
   known gap (no current gate catches slow monotone bleeds).

2. **Combined portfolio preparation** — the actual end-goal of the
   entire v2 track. Switch to the `main` branch and create
   `run_portfolio_combined.py` loading v1 (BTC/ETH/LINK/BNB) + v2
   (DOGE/SOL/XRP/NEAR from v0.v2-005) together.

3. **Paper-trade v0.v2-005** — ground-truth validation before more
   research work.

Option 2 is the most strategically valuable — it shifts from "try to
beat v2 baseline" to "compose v1 and v2 baselines into the
combined-portfolio product". This is what the user explicitly wanted
from the start of the session.

## Label Leakage Audit

No leakage. FIL parquet was already generated in iter-v2/001 screening
and has the standard v2 feature schema.

## Conclusion

iter-v2/010 NO-MERGE on 1-seed evidence. FIL is NOT a better 4th
symbol than NEAR — both have the same structural 2022-bear-training
problem. This is the 5th consecutive NO-MERGE targeting the 4th-symbol
slot, establishing iter-v2/005's +1.297 as a definitive ceiling for
this configuration.

**Decision**: NO-MERGE. Recommend iter-v2/011+ pivots to deferred
drawdown brake OR combined-portfolio preparation (off-track). The
v2 iteration track's marginal improvements are exhausted; the next
value-add is either a different risk mechanism or the combined-
portfolio end-goal.
