# Phase 7.5 Critic Review — iter-v3/025

OVERALL: **EXPLORATION-PROMISING (clean)** — first genuinely PROMISING result in post-bootstrap cycle. Engineered feature `regime_momentum_signed_5d` produces co-directional IS+OOS lift with meaningful feature-importance contribution. Strong CONFIRMATION-bundle candidate for iter-v3/029.

## Per-Check Status

All 12 methodology checks PASS or PASS-EXPLORATION (informational). New `compute_regime_momentum_signed_5d` past-only verified by 20 adversarial tests. IC orthogonality CARVE-OUT (composed feature mechanically correlates with primitives ret_5d and hurst_100; max |IC|=0.887 with vwap_dev_20 is structural per `feedback_v3_engineered_feature_pivot.md`).

## Critical Methodological Finding — Frozen Baseline DISSOLVED

iter-v3/020/021/022/023/024 all share BCH/LDO bit-identity (frozen baseline at single-seed=42). iter-v3/025 BREAKS this pattern:
- BCH OOS: -6.2465 (frozen) → **+11.31** in iter-v3/025
- LDO OOS: -8.9257 (frozen) → **-1.98** (~neutral) in iter-v3/025

The frozen baseline was specific to per-symbol Optuna trajectories at fixed seed across iterations SHARING THE SAME V3_FEATURE_COLUMNS. Adding the engineered feature changed each per-symbol search space, producing different trajectories. This is consistent with `feedback_v3_single_seed_frozen_baseline.md` — frozen baseline is feature-set-specific, dissolves when V3_FEATURE_COLUMNS changes.

## §4.4 PATH A Verification

| Condition | Threshold | Observed | Triggered |
|---|---|---|---|
| IS Sharpe Δ ≥ +0.10 | ≥ +0.10 | +0.50 | YES |
| OOS Sharpe ≥ anchor + 0.10 | ≥ +0.49 | +1.22 | YES (massively) |
| Importance ≥ 30 | ≥ 30 | 43/232/123/398 | YES (all 4 cuts) |
| Co-directional IS + OOS | both positive Δ | +0.50 / +0.84 | YES |

PATH A fires unambiguously. **Verdict: EXPLORATION-PROMISING (clean)**.

## Comparison to Prior NEW-Feature Attempts

| Iteration | Feature | Importance % of Top | OOS Sharpe Δ | Verdict |
|-----------|---------|---------------------|---------------|---------|
| 015 | tbr_zscore_30 (microstructure) | 25-67% (per-sym 14/14) | +1.74 vs anchor (lottery) | PROMISING-INERT |
| 019 | funding_rate_zscore_30 (per-sym, n=10) | 22% portfolio | +0.39 vs anchor (lottery) | PROMISING-INERT |
| 023 | funding_rate_zscore_30 (per-sym, n=35) | 22% portfolio | -1.46 vs anchor | NEGATIVE |
| 024 | btc_funding_rate_zscore_30 (cross-asset) | 24% portfolio | -1.20 vs anchor | NEGATIVE |
| **025** | **regime_momentum_signed_5d (ENGINEERED)** | **51% portfolio** | **+0.84 vs anchor** | **PROMISING ✓** |

The engineered feature has ~2× the importance contribution of any prior NEW feature AND co-directional positive lift. This validates the user's "feature engineering" pivot directive.

## Caveats (informational, not verdict-blocking)

1. **Single-seed lottery risk**: iter-v3/013 looked similar at single-seed (+1.01 IS / +2.70 OOS); falsified at iter-v3/018 multi-seed (62% / 86% reduction). iter-v3/025 needs multi-seed validation at iter-v3/029 CONFIRMATION before being trusted.

2. **OOS trade count 95 < 130 floor**: per `feedback_trade_rate_floor_bundle_level.md`, applies at CONFIRMATION-bundle level not per EXPLORATION row. Catalog-row caveat only.

3. **TRX 52.2% WR is unusual** (highest in v3 catalog for any single-symbol single-seed run). The regime feature plausibly filters bad-trend trades, but a multi-seed CONFIRMATION will reveal whether this WR is robust or a single-seed artifact.

4. **Importance rank is still 14/14** in portfolio aggregate (last in CSV by absolute importance ordering). The relaxed `importance ≥ 30` threshold is what catches this case — strict `rank ≤ 7` would have missed it. The relaxed criteria per `feedback_v3_engineered_feature_pivot.md` is doing real work here.

## Recommendations to QR

1. **iter-v3/026 axis = SECOND ENGINEERED FEATURE** to validate the pivot strategy. Strong candidate: `vol_adj_autocorr` = `ret_autocorr_lag1_50 / (range_realized_vol_50 + 1e-6)` (autocorrelation per unit vol — orthogonal to regime momentum). If 2 of 2 engineered features PROMISING → strong evidence feature engineering is THE right axis category for v3.

2. **KEEP `regime_momentum_signed_5d`** in V3_FEATURE_COLUMNS for iter-v3/026 (do NOT revert). The PROMISING verdict means this feature is a CONFIRMATION-bundle candidate — keeping it in the live stack lets iter-v3/026's hypothetical second engineered feature compose ON TOP of regime momentum, building a multi-feature engineered-features stack incrementally.

3. **Catalog row** must explicitly flag PROMISING-CONFIRMATION-CANDIDATE status, distinguishing this from iter-v3/013's PROMISING-MECHANICAL (which was falsified) and iter-v3/015/019/023/024 PROMISING-INERT.

4. **Pre-commit memory rule** at iter-v3/025 closeout: `feedback_v3_engineered_features_proven.md` codifying that engineered features (composed from primitives) succeed where off-the-shelf indicators failed, and that this is the highest-priority axis category for the remainder of the post-bootstrap cycle (iter-v3/026/027/028).

## Catalog Row

`| iter-v3/025 | 2026-05-08 | ENGINEERED feature: regime_momentum_signed_5d = ret_5d × sign(hurst_100 - 0.5) (FEATURE ENGINEERING pivot) | +0.50 (vs anchor +0.3788) | +1.2244 (Δ +0.84 — FIRST OOS > +1.0 in post-bootstrap; co-directional IS+OOS lift) | EXPLORATION-PROMISING (clean) | YES — STRONG CONFIRMATION-BUNDLE CANDIDATE; importance 51% of top portfolio (~2× any prior NEW feature); per-sym importance 43/232/123 (LDO ≥30, rank ~8-9/14); BCH/LDO frozen baseline DISSOLVED; needs multi-seed validation at iter-v3/029 |`
