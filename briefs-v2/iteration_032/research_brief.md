# Iteration v2/032 Research Brief

**Type**: EXPLORATION (4-symbol pivot, swap SOL for ADA)
**Track**: v2 — keep trade density while reducing concentration
**Parent baseline**: iter-v2/029 (forced reset)
**Date**: 2026-04-15
**Researcher**: QR (autopilot)
**Branch**: `iteration-v2/032` on `quant-research`

## Motivation

iter-031 showed that adding ADA as a 5th symbol helps primary seed
(XRP concentration 69% → 42%) but the 10-seed mean OOS regressed 26%
because 3 seeds went fully distressed. Adding a 5th losing symbol to
bad seeds cascaded losses.

The first iter-032 attempt was a 3-symbol portfolio (DOGE+XRP+ADA)
that ALSO regressed — smoke test showed OOS monthly dropping to +0.76
on primary seed. Root cause: **the hit-rate gate has cross-symbol
coupling**. With fewer symbols, its "last 20 trades" lookback spans
more calendar time and kills different trades. DOGE wpnl on the same
32 trades dropped from +30.12 (iter-031, 5-sym) to +9.83 (iter-032
3-sym smoke) purely because gate decisions were different.

**Pivot**: keep trade density at 4 symbols, but swap SOL (worst primary-seed
contributor: −1.66 wpnl) for ADA (real signal: +22.13 wpnl on iter-031
primary seed).

## Hypothesis

4 symbols = DOGE + XRP + NEAR + ADA:
1. **Preserves gate coupling**: 4-symbol trade density unchanged
2. **Replaces SOL noise with ADA signal**: net-positive contributor swap
3. **Matches iter-029's structural shape** but with a better symbol mix

Expected: both IS and OOS improve; concentration drops on primary seed
below the 50% rule (first pass); mean OOS comparable to or better than
iter-029 baseline.

## Changes vs iter-029

| Change | Before | After |
|---|---|---|
| V2_MODELS | DOGE, SOL, XRP, NEAR | **DOGE, XRP, NEAR, ADA** |
| Features | 40 | 40 (same) |
| Optuna trials | 15 | 15 |
| Risk gates | 7 | 7 |

## Section 6: Risk Management Design

Same 7 gates. Cross-symbol coupling via hit-rate gate is a known
consideration but not a primitive — it's a byproduct of the lookback
window. With 4 symbols (same density as iter-029), the gate behavior
should be similar.

### Pre-registered failure-mode prediction

**Most likely outcome**: primary seed passes concentration (40-42% XRP
share, meets 50% rule for the first time). 10-seed mean improves vs
iter-029 slightly. 8-9 profitable seeds. Seed variance still a problem
but less severe than iter-031 (no 5-symbol cascade).

**Pre-registered OOS mean**: +0.90 to +1.05 monthly (beating iter-029).

## Success criteria

**Gating**:
- Seed concentration audit PASS (n=4 thresholds)
- Mean OOS monthly > iter-029 baseline (+0.8956)
- Profitable seeds ≥ 8/10
- Primary seed XRP share < 50%

**Non-gating**:
- Primary seed OOS ≥ iter-029 primary (+1.28)
- Balance ratio in target 1.0-2.0
