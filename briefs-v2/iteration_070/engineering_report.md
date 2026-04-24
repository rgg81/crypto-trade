# iter-v2/070 Engineering Report — new features hurt

## Build

- Branch: `iteration-v2/070` from `quant-research` at `54a0e49`
- Added 2 features to V2_FEATURE_COLUMNS (34 → 36):
  - `liquidity_impact_20` in `volume_micro.py`
  - `return_zscore_20` in `tail_risk.py`
- All pre-flight checks passed with fresh data through 2026-04-23 23:59 UTC

## Results — significant regression

| Metric | iter-v2/069 (baseline) | **iter-v2/070** | Δ |
|---|---|---|---|
| IS monthly Sharpe | +0.874 | +0.725 | −17% |
| IS daily Sharpe | +1.032 | +0.674 | −35% |
| **OOS monthly Sharpe** | +2.108 | +1.303 | **−38%** |
| **OOS daily Sharpe** | +2.409 | +1.406 | **−42%** |
| Combined monthly | +2.982 | +2.028 | **−32%** |
| OOS PF | 2.413 | 1.699 | −30% |
| OOS WR | 54.5% | 43.1% | −11.4pp |
| **OOS MaxDD** | 18.80% | **32.61%** | **+73% worse** |
| OOS trades | 55 | 51 | −7% |

## Per-symbol OOS — all 4 regressed

| Symbol | iter-v2/069 wpnl | iter-v2/070 wpnl | Δ |
|---|---|---|---|
| SOLUSDT | +41.61 | +18.27 | **−56%** |
| XRPUSDT | +30.51 | +25.61 | −16% |
| NEARUSDT | +28.70 | +8.88 | **−69%** |
| DOGEUSDT | +15.26 | +10.31 | −32% |

Concentration (authoritative):

| Symbol | Share |
|---|---|
| XRPUSDT | **40.60%** ← new max, JUST OVER 40% inner cap (FAIL pass_inner) |
| SOLUSDT | 28.97% |
| DOGEUSDT | 16.35% |
| NEARUSDT | 14.08% |

pass_max (≤50%): TRUE. **pass_inner (≤40%): FALSE** (40.60%).

## Pre-registered failure signature — CONFIRMED

Brief: "if OOS monthly Sharpe < +1.79 (0.85 × 2.108), NO-MERGE. The model found no edge in the new features."

Actual: OOS monthly +1.30 — well below +1.79 threshold. Failure
signature matched exactly.

## Why the new features hurt

Two candidate explanations (can't disambiguate without further testing):

1. **Univariate rho was misleading**: `return_zscore_20` had the 2nd-strongest
   Spearman on 3-bar forward returns (−0.027) after fracdiff. But univariate
   rho doesn't tell you about interaction quality. The model found
   `return_zscore_20` correlated WITH existing features (esp. `vwap_dev_20`)
   and wasted capacity picking between them.

2. **colsample dilution**: going 34 → 36 features, LGBM's
   `colsample_bytree` randomly excludes a larger fraction of the
   predictors per tree. If the new features are weak or correlated, they
   absorb some sampling slots that would have gone to stronger
   predictors.

Combined: adding features blindly degraded the ensemble's feature diversity.

## MERGE criteria — all FAIL except concentration outer

| # | Criterion | Target | Actual | Pass |
|---|---|---|---|---|
| 1 | Combined monthly ≥ 2.98 | ≥ 2.98 | 2.03 | FAIL |
| 2 | OOS monthly ≥ 1.79 | ≥ 1.79 | 1.30 | FAIL |
| 3 | IS monthly ≥ 0.74 | ≥ 0.74 | 0.73 | FAIL (marginal) |
| 4 | OOS MaxDD ≤ 22.6% | ≤ 22.6% | 32.61% | FAIL |
| 5 | PF>1, trades>=50, SR>0 | — | 1.70, 51, +1.40 | PASS |
| 6 | Concentration outer ≤50% | — | 40.60% | PASS |
| 7 | Concentration inner ≤40% | — | 40.60% | FAIL (0.60 over) |

**Verdict: NO-MERGE.** Rollback the feature additions.

## Lesson for iter-v2/071+

1. **Don't add features based on univariate rho alone.** The rank's
   predictive power is a NECESSARY but not SUFFICIENT condition. The
   model may not be able to extract incremental value when the new
   feature correlates with existing predictors.
2. **36 features is not obviously better than 34** for this architecture.
   Feature ADDITION is trickier than PRUNING. The cost of noise > the
   benefit of extra signal for these specific features.
3. **Better feature-addition protocol**: train a model with candidate
   feature included, check SHAP/feature importance (not just univariate
   rho). If new feature ranks bottom-20%, drop before baseline run.
