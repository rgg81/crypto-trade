# LightGBM Master Advisor — iter-v1/051 — Phase 4.5 (Pre-Design)

## Context Read

- Track: v1; cycle-6 EXP-6 — multi-seed re-validation of iter-v1/050 PROMISING-PARTIAL
- Cohort: **single-symbol DOT (DOTUSDT)**. /050 IS Sharpe -0.1138 (DOT IS Δ +1.1162 vs -1.23 baseline).
- Axis: VALIDATION sub-type. No new feature. Drop inert vol-spike gate (0% fire rate).
- Seeds: --seeds 4 (outer seed offsets 0, 5, 10, 15 from ENSEMBLE_SEEDS roster).
- Feature stack: V1_FEATURE_COLUMNS_PRUNED unchanged at 46 cols.
- Same n_trials=18, ENSEMBLE_SIZE=3 as /050.

## Phase 4.5 Assessment

### What Changed vs /050

1. **Vol-spike regime gate DROPPED**: gate never fired (0% IS / 0% OOS) → mechanically INERT.
   Removing it has no expected effect on IS Sharpe — the +1.1162 IS Δ was 100% feature-attributed.

2. **Seeds 4 outer seeds (offsets 0, 5, 10, 15)**: each outer seed uses a different 3-seed
   inner ensemble window from ENSEMBLE_SEEDS. Outer seed 0 (offset=0) = canonical seed_42, which
   matches /050's single-seed run for sanity validation.

### ML Perspective on Multi-Seed Validation

DOT cohort has ~125 IS trades at /050. With n_trials=18 and ENSEMBLE_SIZE=3 per cell, the
IS Sharpe at each outer seed is a noisy estimate. The key question: is the +1.1162 IS Δ
structurally driven by `dot_vs_btc_ret_ratio_30`'s predictive content, or is it a lucky
arrangement of inner ensemble seeds that happened to vote consistently?

**Expected per-seed variance**: with DOT's small IS trade count, the seed-to-seed IS Sharpe
variance could be ±0.5 to ±1.0. A mean IS Δ of +1.1162 with ±0.6 std would still confirm
PROMISING-PARTIAL (mean in [+0.50, +1.23)). A mean IS Δ < +0.50 confirms LOTTERY-NEGATIVE
— feature importance at rank 8/45 is consistent with learned signal, but single-seed can
produce rank artifacts on DOT's small cohort.

## Top 3 Recommendations

### 1. seed=42 sanity check IS the most important diagnostic

If outer seed 0 (offset=0) produces IS Sharpe materially different from /050's -0.1138 (e.g.
more than ±0.10), the /051 dispatch implementation has a bug (e.g. regime gate accidentally
retained). The seed=42 sub-run should reproduce /050 essentially identically (within Optuna
stochasticity tolerance at n_trials=18).

**Pre-register F5 falsifier**: |/051 seed=42 IS Sharpe - /050 IS Sharpe| ≤ 0.10. FAIL =
implementation error.

### 2. Watch for baseline-frozen-IS pattern at offsets 5/10/15

Prior v1 experience (/013 BASIN-LOTTERY, /026 frozen-baseline pattern) showed that
non-canonical outer seed offsets can land in particularly bad basins on small cohorts.
DOT with 93 BASELINE IS trades → 125 /050 IS trades has thin per-fold coverage.

If max(per-seed IS Δ) - min(per-seed IS Δ) > +1.0 (F3 stability falsifier), classify
BASIN-LOTTERY even if mean is positive.

### 3. No new LightGBM HP tuning needed

This is a seed-validation run. HP search space is identical to /050. No colsample, num_leaves,
min_child_samples changes. The n_trials=18 budget is intentionally consistent with /050 for
fair comparison.

## Prior Distribution (4 outcome bands)

| Band | Prior | Reasoning |
|---|---|---|
| PROMISING-SPECIALIST-CONFIRMED | 10% | Would require mean IS Δ ≥ +1.23 across all 4 seeds — unlikely given DOT's noise floor |
| PROMISING-PARTIAL-CONFIRMED | 45% | Feature genuinely learned; partial lift survives seed variation |
| LOTTERY-CONFIRMED-NEGATIVE | 35% | Single-seed lottery; mean IS Δ < +0.50 |
| BASIN-LOTTERY | 10% | High per-seed variance (F3 stability fail) even if mean is positive |

**Modal outcome: PROMISING-PARTIAL-CONFIRMED (45%)**. The /050 feature importance rank 8/45
is a positive signal — rank 8 in a 46-col model suggests meaningful split budget allocation,
not a noise-fit artifact. But DOT's small cohort means per-seed variance is high.

## Risks

1. **offset=5 inner seeds [2002, 3003, 4004]**: these seeds were never used in a DOT-only
   single-cohort run. Unknown prior for this cohort + seed combination.
2. **n_trials=18 is near Optuna's TPE warmup**: 18 trials barely exceeds the expected ~15-20
   random-search warm-up before TPE starts exploiting. Per-seed IS Sharpe could be largely
   determined by the random warm-up phase, not the HPO exploitation phase.

## What I Did NOT Recommend

- No ENSEMBLE_SIZE increase (keep 3; compare apples-to-apples with /050)
- No n_trials increase (keep 18; this is the EXPLORATION budget; increases would confound comparison)
- No feature changes (validation run; any change destroys the comparison)
- No new risk gate (regime gate was INERT; adding a replacement is a /052+ axis)

## Closing Note

**Confidence: MEDIUM-HIGH** on correct setup. The only ML-relevant decision here is seed
count and whether the gate drop is clean. Both are confirmed in tests.

The genuine question /051 should answer: **is /050's +1.1162 IS Δ basin-dependent at n_trials=18
with seed=42, or does it survive seed perturbation?**

— Phase 4.5 advisor authored 2026-06-01 (iteration-v1/051 multi-seed re-validation)
