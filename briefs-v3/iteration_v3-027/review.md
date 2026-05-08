# Phase 7.5 Critic Review — iter-v3/027

OVERALL: **EXPLORATION-NEGATIVE-SUSPICIOUS-OOS** — same anomaly pattern as iter-v3/026 but more extreme. IS Sharpe NEGATIVE for first time in post-bootstrap (-0.28); OOS Sharpe +1.68 (would be v3-historic high but single-seed-untrustable). Engineered features beyond regime_momentum_signed_5d destabilize IS axis at single-seed.

## Per-Check Status

All 12 methodology checks PASS or PASS-EXPLORATION. cross_asset_divergence_norm past-only verified by 4 adversarial tests.

## Anomaly Pattern (3-iteration trajectory)

| Iter | Engineered features | IS Sharpe | OOS Sharpe | IS MaxDD | OOS conc max |
|------|---------------------|-----------|------------|----------|--------------|
| 025 | regime_momentum (alone) | **+0.88** | +1.22 | 27.5% | 71% TRX |
| 026 | + vol_adj_autocorr | +0.05 | +1.45 | 51.4% | 78% BCH |
| 027 | + cross_asset_divergence | **-0.28** | +1.68 | **62.9%** | **91.6% TRX** |

**Monotonic IS degradation + monotonic OOS lift** = structural single-seed lottery on expanded loss surface. The IS MaxDD trajectory (27% → 51% → 63%) is the cleanest diagnostic.

## §4.4 Classification

PATH C fires decisively: IS Δ -0.66 vs anchor (way < -0.10 threshold). PATH A condition (rank ≤10 + IS lift) FAILS — feature is used (importance 64% of top portfolio) but IS axis collapses.

## Verdict Confirmation

EXPLORATION-NEGATIVE-SUSPICIOUS-OOS. IS controlled at single-seed EXPLORATION = decisive. OOS untrustable at single-seed (iter-v3/013 +2.70 → +0.39 multi-seed precedent).

## Critical Bundle Conclusion for iter-v3/029

**Only iter-v3/025 (regime_momentum_signed_5d ALONE) is the validated PROMISING result for the CONFIRMATION bundle.** All 4 attempts to add MORE engineered features (vol_adj_autocorr, cross_asset_divergence_norm, and the failed iter-v3/026/027) destabilized IS without producing trustable OOS lift.

The iter-v3/029 CONFIRMATION bundle is:
- Base: iter-v3/013 baseline (BCH+LDO+TRX, 13 features, ATR labeling, 7 risk gates)
- ADD: `regime_momentum_signed_5d` (V3_FEATURE_COLUMNS=14)
- Spec: `--seeds 2 --n-trials 35`, ENSEMBLE_SIZE=5, full DSR/PBO/PSR, 6h cap

This is a **MINIMAL bundle** — only 1 NEW edge ingredient validated across 9 EXPLORATIONs. The prior bootstrap baseline (iter-v3/018 multi-seed mean +0.38/+0.39) is what we're trying to lift via this single feature.

## Recommendations

**iter-v3/028 axis = REPLICATE iter-v3/025 ALONE at --seeds 2** (mini-CONFIRMATION sanity check):

Rationale:
1. iter-v3/025's single-seed +0.88 IS / +1.22 OOS is the CONFIRMATION bundle's only edge ingredient
2. iter-v3/013 single-seed +1.01 / +2.70 was falsified at iter-v3/018 multi-seed (62%/86% reduction)
3. Pre-validating iter-v3/025 at --seeds 2 (~30 min compute, 2× single-seed budget) gives early signal whether iter-v3/029 CONFIRMATION at --seeds 2 + n_trials=35 + ENSEMBLE_SIZE=5 (~3-4h compute) is worth the budget
4. If iter-v3/025 multi-seed falsifies → iter-v3/029 is dead-on-arrival; we save CONFIRMATION budget
5. If iter-v3/025 multi-seed holds → iter-v3/029 launches with high confidence

Spec for iter-v3/028:
- Same V3_FEATURE_COLUMNS as iter-v3/025 (revert iter-v3/027's swap; back to 14 with regime_momentum)
- DROP cross_asset_divergence_norm
- KEEP regime_momentum_signed_5d
- Run with `--seeds 2` (NOT --exploration) at default n_trials=35
- ENSEMBLE_SIZE=5 (default non-exploration)
- This is structurally a "mini-CONFIRMATION" — gives multi-seed Pareto + n_eff > 19 + DSR potentially non-zero

Alternative: try a DIFFERENT engineered feature alone (drop both regime_momentum and cross_asset; try fracdiff_d05_close). Risk: may validate the engineered-feature-pivot more broadly but burns the remaining EXPLORATION slot.

Critic strong prior: **iter-v3/028 = mini-validation of iter-v3/025 at --seeds 2**. Higher decision-information value than another EXPLORATION axis.

## Catalog Row

`| iter-v3/027 | 2026-05-08 | THIRD engineered feature: cross_asset_divergence_norm = (sym_ret_7d - btc_ret_14d) / (vwap_dev_20+1e-6) (atomic swap from vol_adj_autocorr; KEEP regime_momentum) | -0.66 (vs anchor +0.3788) — IS NEGATIVE for first time in post-bootstrap | +1.6786 (would be v3-historic high but single-seed lottery suspect; TRX 91.6% concentration; IS MaxDD 62.9% worst ever) | EXPLORATION-NEGATIVE-SUSPICIOUS-OOS | NO — IS PATH C fires; engineered feature stacking pattern (3-iter trajectory: +0.88/+0.05/-0.28) confirms structural single-seed instability; iter-v3/028 = mini-validation of iter-v3/025 at --seeds 2 before iter-v3/029 CONFIRMATION-bundle |`
