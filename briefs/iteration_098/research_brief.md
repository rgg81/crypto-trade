# Iteration 098 — Research Brief

**Type**: EXPLORATION (time decay sample weighting)
**Date**: 2026-03-31
**Previous**: Iter 097 (NO-MERGE EARLY STOP — uniqueness weighting destroyed OOS)

## Section 0: Data Split (verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

## Hypothesis

Iter 097 showed that flattening |PnL| weights via uniqueness weighting hurt OOS. This iteration adds time decay weighting ONLY — preserving the |PnL| signal while adding recency bias.

The training window is 24 months. Patterns from 22 months ago may be less relevant than patterns from 2 months ago (market regime changes, structural breaks). Exponential time decay gives recent samples higher weight.

**Formula**: `weight = |PnL_weight| * exp(-lambda * age_months)` where `lambda = ln(2) / half_life` and `half_life = 12 months`.

Effect: oldest sample (24mo ago) gets weight × 0.25, newest gets weight × 1.0. The |PnL| range [1,10] is preserved — just modulated by recency.

**Single variable changed**: time decay multiplicative factor on sample weights.

## Research Analysis (4 categories)

### Category A: Feature analysis
185 features unchanged. Feature pruning is dead (iters 061, 073, 094, 095 all failed).

### Category C: Labeling
Labels unchanged. |PnL| weighting preserved (iter 097 lesson).

### Category E: Trade patterns (from iter 097 IS data)
- Best years: 2024 (+126.7%), 2022 (+25.7%)
- Worst months cluster in bear markets (2022-04: -26.9%, 2024-06: -22.3%)
- Time decay should help by down-weighting 2020-2021 patterns when predicting 2024+

### Category F: Statistical rigor
- Baseline WR 42.8%, 95% CI [37.6%, 48.0%], significantly above 33.3% break-even
- Time decay changes effective sample size but not the fundamental signal

## Configuration (iter 098)

**UNCHANGED from baseline (iter 093)**:
- Symbols, features (185), labeling, CV, ensemble, cooldown — all same

**CHANGED**:
- Sample weights: `|PnL| * time_decay(age)` instead of just `|PnL|`
- Time decay: exponential, half-life = 12 months
- Oldest sample in 24mo window: weight × 0.25, newest: × 1.0
- NO uniqueness weighting (iter 097 proved it harmful)
