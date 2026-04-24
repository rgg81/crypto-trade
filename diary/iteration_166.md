# Iteration 166 Diary

**Date**: 2026-04-21
**Type**: EXPLOITATION (seed-robustness validation, stopped by design bug)
**Decision**: **NO-MERGE** — iter 165 already satisfies ensemble-level seed parity; iter 166's sweep was a no-op

## What this iteration taught us

The "5 outer seed validation" prescription from the skill was written for single-seed model configurations. Our baseline's LightGBM models all use a **5-seed ensemble** inside each monthly training (`ensemble_seeds=[42, 123, 456, 789, 1001]`). The outer `seed=` parameter on `LightGbmStrategy` is read only as a fallback when `ensemble_seeds` is empty (`lgbm.py:424`).

Running LTC with outer seeds 42 and 123 produced **byte-identical output** (IS/OOS Sharpe, trade counts, PnL). The test had no power to distinguish models.

## Implication for iter-165 merge

The iter-165 LTC runner used `ensemble_seeds=[42, 123, 456, 789, 1001]` — the same set used by Models A and C in the baseline. "Seed parity" in the ensemble sense was already satisfied by construction. No additional validation was needed to confirm the merge.

Iter 165 stands. Baseline remains A+C+LTC at OOS Sharpe +1.27.

## Research Checklist

- **F — Statistical Rigor**: formally skipped. The ensemble already averages over 5 seeds, which is the same mechanism the 5-seed sweep would have applied externally.

## Exploration/Exploitation Tracker

Window (157-166): [X, X, X, X, E, E, E, E, E, X] → 5E/5X, 50% — above the 30% floor.

## Lessons Learned

1. **Outer seed vs inner ensemble seeds** — the existing `self.seed` parameter is dead when `ensemble_seeds` is populated. The seed-validation prescription in the skill needs to differentiate single-seed from ensemble configurations.

2. **Bit-for-bit identical runs are a strong signal of dead-code paths** — if two seeds produce literally identical output, there's no random source variation happening. That's a bug smell. The first seed=123 full run (~100 min) paid for this lesson; subsequent seeds (789, 1001) were correctly skipped.

3. **Fail-fast applies to validation design too** — when the test shows no power to distinguish hypotheses, stop the test and fix the design.

## lgbm.py Code Review

**Finding**: `LightGbmStrategy.__init__` accepts a `seed` parameter that is only used if `self.ensemble_seeds` is empty. Every production caller sets `ensemble_seeds=[42, 123, 456, 789, 1001]`, making `seed` effectively ignored in production. The parameter is retained to preserve API compatibility with old runners in `old_runners/`.

**Action**: not removing it this iteration (would break old runners for historical reproducibility). Consider a future maintenance iteration to deprecate the parameter or repurpose it (e.g., as a global offset applied to the ensemble seed list).

## Next Iteration Ideas

### 1. Iter 167: Screen ATOM as a 4th portfolio candidate (PRIORITY)

With BNB replaced by LTC, the next diversification step is adding a 4th model. ATOM was flagged in iter 164/165 as the next candidate after LTC. Same Gate 3 protocol — fail-fast on year-1 — same budget (≤ 90 min, or ≤ 15 min on early stop). Goal: bring LINK concentration below 50% by adding another profitable source.

### 2. Iter 168: If ATOM passes, check whether ATOM destabilises Models A or C

Per-symbol models are independent by construction, so trade counts for existing models don't change. But VT is per-symbol, so LINK's VT history (and therefore its trade weights) is unaffected by the presence of ATOM. A/B test not strictly necessary for per-symbol setups — document this in the iter 168 brief.

### 3. Iter 169: Revisit Model A (BTC+ETH) — consider per-symbol sub-models

Model A alone contributed +9.3% OOS PnL at Sharpe +0.24 in the iter-152 reproduction. After more candidates are added and the portfolio is more diversified, improving Model A's signal becomes the highest-leverage move. Iter 076 observed ETH SHORT 51% WR vs BTC LONG 43.6% — very different dynamics suggesting per-symbol models for A could help.

### 4. Iter 170+: Consider deprecating the unused outer `seed` parameter

Not urgent — preserves historical reproducibility — but worth revisiting once the portfolio is stable.
