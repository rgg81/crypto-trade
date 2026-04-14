# Iteration v2/008 Research Brief

**Type**: EXPLORATION (per-symbol architecture change)
**Track**: v2 — diversification arm
**Parent baseline**: iter-v2/005 (10-seed mean +1.297, primary seed 42 +1.671)
**Date**: 2026-04-14
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

## Motivation

iter-v2/007 confirmed that NEAR's IS weakness is **structural, not
procedural**: bumping Optuna trials from 10 to 25 didn't lift
aggregate IS Sharpe. Instead, it redistributed per-symbol PnL — NEAR
IS swung +90 pp (−67% to +23%) but XRP and DOGE IS dropped by
~equal amounts. Aggregate was flat.

The iter-v2/007 diary identified Priority 1 as "shorter training
window for NEAR" with this rationale:

> "NEAR's 2022 bear market dominates its 24-month rolling training
> window. By using a 12-month training window for NEAR only, we
> avoid 2022 entirely in any month that predicts >= 2023-01."

iter-v2/008 implements this via a per-symbol `training_months` field
in `V2_MODELS`. DOGE/SOL/XRP keep 24 months; NEAR gets 12 months.

## Hypothesis

A 12-month rolling training window for NEAR specifically should:

1. **Avoid the 2022 bear market** in NEAR's training data for any
   walk-forward month predicting >= Jan 2023. This removes the hostile
   regime that dominated NEAR's 24-month window.
2. **Lift NEAR IS quality** from −67% raw (iter-v2/005) toward near-zero
   or positive territory.
3. **Improve NEAR OOS** because the OOS regime (2025+) is structurally
   more similar to 2024 than to 2022.
4. **Keep DOGE/SOL/XRP unchanged** (they continue to use 24 months).

Quantitative prediction (pre-registered):

- **NEAR IS Sharpe**: improves from hostile to neutral (per-symbol
  weighted Sharpe > 0)
- **NEAR OOS Sharpe**: roughly unchanged or modestly up (the OOS
  regime is 2025 which is already in all training windows regardless)
- **Aggregate OOS Sharpe (primary seed 42)**: +1.60 to +1.85 (±0.15
  of baseline +1.67)
- **10-seed mean**: +1.25 to +1.40 (at or above baseline +1.30)
- **Concentration**: XRP share roughly unchanged (47.8% ± 5 pp)
- **Trade count**: NEAR IS trade count may rise (earlier IS months
  become accessible with 12-month window vs 24); NEAR OOS unchanged

## Failure-mode prediction (pre-registered)

Most likely way to fail:

1. **Shorter window has less signal**. 12 months of training data is
   half the sample size. The LightGBM model may not find stable
   hyperparameters with so few samples (~1,400 samples per NEAR
   monthly fold instead of ~2,800). NEAR OOS could degrade.
2. **The fix is in the wrong direction**. NEAR's structural weakness
   might not be 2022-specific — it might be a general signal quality
   issue that a shorter window exposes more, not less.
3. **NEAR's early IS months (pre-2023) now have NEAR trades where
   they didn't before**. These early trades could be net losers
   (NEAR was volatile 2020-2022), dragging aggregate IS further
   despite the window change.

## Configuration (one variable changed from iter-v2/005)

| Setting | iter-v2/005 | iter-v2/008 | Changed? |
|---|---|---|---|
| DOGE training_months | 24 | 24 | — |
| SOL training_months | 24 | 24 | — |
| XRP training_months | 24 | 24 | — |
| **NEAR training_months** | **24** | **12** | **Yes** |
| Everything else | Same | Same | — |

Schema change: `V2_MODELS` tuples now carry `(name, symbol, training_months)`
so each model's window is specified inline.

## Research Checklist Coverage

EXPLORATION iteration (per-symbol architecture change). Category B
(Symbol Universe & Architecture) — specifically B3 Option B ("per-symbol
models with specialized hyperparameters"). Category I (Risk Management)
in §6 below.

## Success Criteria (inherits iter-v2/005 baseline)

Primary: **10-seed mean OOS Sharpe > +1.297**.

Hard constraints: same as iter-v2/005 — ≥7/10 profitable, ≥50 OOS trades,
PF > 1.1, concentration ≤ 50%, DSR > +1.0, v2-v1 correlation < 0.80.

**IS/OOS Sharpe ratio > 0** (relaxed from > 0.5 — the v2 track has an
ongoing IS/OOS divergence that's been documented since iter-v2/005;
keeping ratio positive is the near-term goal).

## Section 6: Risk Management Design

### 6.1 Active primitives

Unchanged from iter-v2/005. Same 5 gates, same thresholds.

### 6.2 Expected fire rates

NEAR gate stats may shift because the NEAR feature z-score OOD
training window is now half as long (12 months worth of feature stats
vs 24). If the short window captures less variance, the z-score gate
may fire MORE for NEAR. Watch this.

### 6.3 Pre-registered failure-mode prediction

"The most likely way iter-v2/008 fails is that 12 months is too short
for LightGBM to find stable hyperparameters — 1,400 samples per fold
is near the minimum viable training set. Signal: NEAR trade count
rises on IS (more early months accessible) but per-trade expectancy
worsens (less stable model). NEAR OOS stays roughly flat. Aggregate
OOS Sharpe lands close to baseline ±0.2.

If NEAR IS improves significantly (per-trade expectancy up by 50pp or
more) while NEAR OOS stays similar, the hypothesis is confirmed. If
NEAR per-trade expectancy stays negative on IS and neutral on OOS,
the 12-month window isn't the fix — try 18 months or replace NEAR
in iter-v2/009."

### 6.4 Exit Conditions

Unchanged.

### 6.5 Post-Mortem Template

Phase 7 will report:
- NEAR per-symbol IS/OOS comparison (trades, WR, per-trade PnL, Sharpe)
- Aggregate OOS/IS Sharpe vs baseline
- Concentration per symbol
- Gate efficacy (any NEAR-specific shifts)
- Optional: NEAR trade time distribution (are the extra IS trades
  concentrated in specific months?)
