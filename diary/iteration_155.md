# Iteration 155 Diary

**Date**: 2026-04-07
**Type**: EXPLORATION (per-symbol VT architecture)
**Decision**: **NO-MERGE** — per-symbol VT confirmed inferior to universal config

## Findings

### Key Diagnostic (Motivation)

v0.152's universal VT (target=0.3, floor=0.33) is **not actually adaptive**:
- 78.4% of trades sit at floor 0.33
- 21.0% sit at default 1.0 (insufficient history)
- Only 0.5% get a middle scale

The config behaves as a **binary fresh-start switch**: "full exposure when new,
1/3 exposure once history accrues." Median realized vol per symbol (4-8%) is
far above target=0.3, so scale = 0.3/realized_vol ≈ 0.04-0.08 always clips to
0.33 floor.

### Grid 1: Per-symbol target_vol calibration

Calibrated target_vol_sym = median_realized_vol_sym × k, for k ∈ {0.3, ..., 2.0}.

**Every k fails.** IS Sharpe drops to +1.02 at k=0.30 and peaks at +1.19 at
k=1.00. OOS Sharpe drops to +2.43 at k=0.30 and crashes to +1.71 at k=1.50.

The universal target=0.3 baseline gives IS=+1.33, OOS=+2.83 — **strictly
better than every calibrated config**.

### Grid 2: Per-symbol floor (target held at 0.3)

Tested inverse-vol floors, LINK-tight, BTC-loose variants.

IS-best: **BTC-loose (0.67)** — floors={BTC:0.67, others:0.33}
- IS Sharpe: +1.3473 (+0.0153 vs baseline, +1.1%)
- **OOS Sharpe: +2.7484 (-0.0802 vs baseline, -2.8%)**
- OOS MaxDD: 25.66% (worse)

**IS-best fails OOS primary constraint.**

## Hard Constraints (IS-best)

| Check | Threshold | Actual | Pass |
|-------|-----------|--------|------|
| OOS Sharpe > baseline | > +2.83 | +2.75 | **FAIL** |
| OOS MaxDD ≤ 26.2% | ≤ 26.2% | 25.66% | ✓ |
| OOS trades ≥ 50 | ≥ 50 | 164 | ✓ |
| OOS PF > 1.0 | > 1.0 | 1.70 | ✓ |

## Mechanism

Any config that RAISES exposure (higher target or higher floor) hurts OOS
because July 2025 crash is undampened. The universal floor=0.33 is
empirically optimal: it's the most aggressive deleveraging that still keeps
enough exposure to profit during Q3-Q4 2025.

**Per-symbol tuning is a false dimension** for this portfolio — the universal
constraint captures the right risk posture for all four symbols.

## Honorable Mention

**LINK-tight(0.20)**: slightly lower OOS Sharpe (-1.4%) but meaningfully
better OOS MaxDD (-18%, down to 17.82%). Risk-adjusted trade-off, but
doesn't meet the primary-metric bar.

## Research Checklist

- **B (Symbol Universe)**: B3 architecture decision — per-symbol VT tested
  via both target_vol and floor parameters. Rejected: universal captures
  the right risk posture.
- **E (Trade Pattern)**: VT scale distribution diagnosed (78% floor, 21%
  default). Binary fresh-start mechanism identified as v0.152's edge.

## Exploration/Exploitation Tracker

Last 10 iterations: [E, E, E, X, X, X, X, X, X, **E**] (iters 146-155)
Exploration rate: 4/10 = 40% ✓

## Next Iteration Ideas

**Hard parameter space is now exhausted.** v0.152 confirmed globally optimal
across:
- min_scale ∈ [0.10, 0.75] (iter 152, 153)
- per-symbol target_vol k ∈ [0.3, 2.0] (iter 155 Grid 1)
- per-symbol floor (iter 155 Grid 2)
- temporal stability (iter 154)

### Remaining exploration ideas (if continuing research)

1. **Event-driven sampling + sample uniqueness** — Tier 1 from skill. Would
   require retraining. High-risk, high-reward. The dense-label uniqueness
   experiment failed in iter 097 because labels are too crowded; event-driven
   sampling fixes the prerequisite.

2. **Entropy features (AFML Ch. 18)** — Shannon entropy over 50-candle
   returns. Genuinely novel, never tested. Would require feature regeneration.

3. **CUSUM structural breaks (AFML Ch. 17)** — regime-change features, never
   tested. Could also feed event-driven sampling.

4. **Meta-labeling with richer meta-features** — iter 102 failed with 2
   meta-features. Needs 5-6 (NATR quartile, ADX regime, rolling WR,
   hour_of_day, primary confidence, BTC regime).

### Recommended action

**Stop pure-parameter iteration.** Any further research should be
structural/feature-level (items 1-4 above). Strategy v0.152 is
production-ready and paper-trading can proceed in parallel with longer-term
research iterations.
