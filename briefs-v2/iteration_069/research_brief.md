# iter-v2/069 Research Brief — Prune 6 redundant features (Category A driven)

**Type**: EXPLOITATION (single variable, prune only)
**Parent baseline**: iter-v2/059-clean
**Bold-idea slot**: iter-v2/070 planned to ADD new features; iter-v2/069
  isolates the PRUNE impact as a clean control variable

## Section 0 — Data Split

`OOS_CUTOFF_DATE = 2025-03-24` — immutable.

## Category A — Feature Contribution Analysis (driver)

Full EDA in `briefs-v2/iteration_068/qr_phase1_findings.md`. Key numbers:

| Pair | |rho| | Decision |
|---|---|---|
| `range_realized_vol_50` ↔ `parkinson_vol_50` | **1.000** | drop `parkinson_vol_50` |
| `parkinson_vol_20` ↔ `garman_klass_vol_20` | 0.997 | drop `garman_klass_vol_20` |
| `parkinson_vol_20` ↔ `rogers_satchell_vol_20` | 0.988 | drop `rogers_satchell_vol_20` |
| `vwap_dev_50` ↔ `close_pos_in_range_50` | 0.927 | drop `close_pos_in_range_50` |
| `atr_pct_rank_500` ↔ `atr_pct_rank_1000` | 0.905 | drop `atr_pct_rank_1000` |
| `vwap_dev_20` ↔ `close_pos_in_range_20` | 0.905 | drop `close_pos_in_range_20` |

**Pruning decisions**: drop 6, keep 34. All decisions preserve the
shorter-horizon or more-informative representative of each redundant
cluster. 0 information loss (since kept features are >0.90 correlated
with dropped ones).

## Category G — Stationarity Analysis

iter-v2/068 QR Phase 1 flagged 8 features with mean-drift >0.3σ between
IS halves. Of the 6 being dropped, 3 are among the worst drifters:
- `parkinson_vol_50` drift 0.78σ (dropped ✓)
- `garman_klass_vol_20` drift 0.65σ (dropped ✓)
- `rogers_satchell_vol_20` drift 0.62σ (dropped ✓)

Pure prune improves stationarity by side effect.

## Category E — Trade Pattern Analysis

iter-v2/059-clean's 2024-11 disaster (16 trades all-short, WR 6%,
−33 wpnl) was documented earlier. The 6 pruned features don't have a
mechanistic link to that regime miss — pruning is independent of this
pattern. iter-v2/070+ will specifically address 2024-11 via new feature
families (RSI divergence etc.).

## Section 6 — Risk Management Design

### 6.1 Active primitives (unchanged)

Same as iter-v2/059-clean: vol-scaling, ADX, Hurst, z-score OOD 2.5,
low-vol filter, BTC trend filter. Hit-rate off, drawdown brake off.

### 6.3 Pre-registered failure-mode prediction

**Expected outcome**: pruning 6 near-duplicate features REDUCES colsample
variance. LightGBM with `colsample_bytree=0.6-0.8` no longer wastes
trees on quasi-identical vol features. Expected: slight IS improvement
(cleaner training signal) and slight OOS improvement (less overfit to
particular redundant feature by chance).

**Failure mode**: the model actually WAS using the 4 vol estimators as
a "noise reduction" (averaging slightly-different vol measures). Pruning
removes that. Could cause OOS regression.

**Failure signature**: if OOS monthly Sharpe drops >10% vs iter-v2/059-clean,
revert and treat the vol-estimator cluster as intentional redundancy.

**Success signature**: OOS monthly ≥ +1.659 AND IS monthly ≥ +1.042.

## MERGE criteria

| # | Criterion | Target |
|---|---|---|
| 1 | Combined IS+OOS monthly | ≥ 2.70 (baseline) |
| 2 | OOS monthly Sharpe | ≥ 0.85 × 1.659 = 1.41 |
| 3 | IS monthly Sharpe | ≥ 0.85 × 1.042 = 0.88 |
| 4 | OOS MaxDD | ≤ 27.1% |
| 5 | PF, trades, Sharpe>0 | — |
| 6 | Concentration ≤ 50% | — |

Bold idea quota carry-forward: iter-v2/069 is EXPLOITATION. iter-v2/070
must be EXPLORATION with new feature families to satisfy the 3-iter
bold-idea rule.

## Implementation

Single source-file change: remove 6 entries from
`V2_FEATURE_COLUMNS` in `src/crypto_trade/features_v2/__init__.py`.
Keep column order discipline: delete in place, do NOT reorder others.

v2 features parquets already contain all 48 columns (the 6 "dropped"
features still exist in the parquets — we just don't pass them to LGBM).
So no feature regeneration needed.

## Expected runtime

~2.5h single-seed.
