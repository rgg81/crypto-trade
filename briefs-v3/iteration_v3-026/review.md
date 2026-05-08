# Phase 7.5 Critic Review — iter-v3/026

OVERALL: **EXPLORATION-NEGATIVE-SUSPICIOUS-OOS** — vol_adj_autocorr added on top of regime_momentum produced IS Sharpe collapse to 0.05 (PATH C fires) + OOS spike to +1.45 (would be v3-historic high but single-seed-untrustable). The 27× IS/OOS daily Sharpe ratio is structurally absurd. Verdict NEGATIVE on IS axis (controlled at single-seed EXPLORATION); OOS lift unfalsifiable without multi-seed re-test.

## Per-Check Status

All 12 methodology checks PASS or PASS-EXPLORATION (informational). New compute_vol_adj_autocorr past-only verified by 20 adversarial tests. IC carve-out per `feedback_v3_engineered_feature_pivot.md`.

## Anomaly Summary

| Metric | Anchor | iter-v3/025 ref | iter-v3/026 |
|--------|--------|------------------|-------------|
| IS monthly Sharpe | +0.3788 | +0.8788 | **+0.0493** (lowest in post-bootstrap) |
| OOS monthly Sharpe | +0.3869 | +1.2244 | +1.4501 (would be v3-historic high) |
| IS daily Sharpe | — | 1.86 | **0.12** (collapsed) |
| OOS daily Sharpe | — | 2.03 | 3.36 (extreme) |
| IS MaxDD | 22.0% | 27.5% | **51.37%** (worst in v3) |
| BCH concentration | 40-87% | 35% | 78% (single-symbol carry returned) |

## Falsifier 4 (importance threshold)

vol_adj_autocorr portfolio importance 283 (45% of top 630). Above the ≥30 threshold per `feedback_v3_engineered_feature_pivot.md`. Feature is USED by model, NOT INERT. This RULES OUT PROMISING-INERT classification.

## §4.4 Classification

PATH C fires unambiguously on IS axis: IS Δ -0.83 vs iter-v3/025 reference, IS Δ -0.33 vs anchor. The OOS +1.45 is single-seed-suspect for the same reasons iter-v3/013 (single-seed +2.70 falsified to +0.39 multi-seed) was.

The combination "IS Sharpe near-zero + huge OOS lift + Worst IS MaxDD ever + single-symbol concentration regression" cannot be classified PROMISING.

## Mechanism

Combining 2 engineered features (regime_momentum + vol_adj_autocorr) overwhelmed depth-3-5 LightGBM's representational capacity. Optuna at n_trials=35 found IS-noise hyperparams that happen to generalize to a favorable OOS regime by chance. The 27× IS/OOS ratio is the diagnostic signature.

## Lesson — Engineered Features DO NOT STACK Linearly

iter-v3/025 alone: regime_momentum_signed_5d → IS +0.88 / OOS +1.22 (clean PROMISING).
iter-v3/026 stacked: + vol_adj_autocorr → IS +0.05 / OOS +1.45 (IS collapse + suspect OOS).

Two engineered features with 0.075 cross-IC produce DESTABILIZED IS at the same trial budget that worked for one. This is a PIVOT-VALIDATION signal: the FIRST engineered feature axis worked (iter-v3/025); STACKING engineered features on top requires a different methodology than single-feature additions.

**Recommendation**: at iter-v3/027, DROP vol_adj_autocorr (revert to 14 features = regime_momentum + base 13). Try a DIFFERENT engineered feature in isolation rather than stacking.

## Recommendations to QR

1. **iter-v3/027 axis = DIFFERENT engineered feature, ALONE on top of regime_momentum**:
   - Drop vol_adj_autocorr
   - Try cross_asset_divergence_norm = (sym_ret_7d - btc_ret_14d) / (vwap_dev_20 + 1e-6)
     - Different mechanism: relative-strength normalized
     - Uses existing primitives (sym_ret_7d, btc_ret_14d, vwap_dev_20)
     - Predicted bands similar to iter-v3/025 [+0.30, +0.55] IS / [+0.40, +0.65] OOS

2. **NEW memory rule**: `feedback_v3_engineered_features_dont_stack.md` codifying that 2 engineered features at the same Optuna budget at single-seed produces IS overfit collapse. Pre-commits stacking experiments to multi-seed validation only.

3. **Catalog row** must explicitly flag NEGATIVE-SUSPICIOUS-OOS outcome — distinguish from clean NEGATIVE (feature inert OR feature actively hurts both axes). The 27× IS/OOS ratio is the diagnostic.

## Catalog Row

`| iter-v3/026 | 2026-05-08 | SECOND engineered feature: vol_adj_autocorr stacked on regime_momentum (V3_FEATURE_COLUMNS 14→15) | -0.83 (vs iter-v3/025 ref); -0.33 (vs anchor) | +1.4501 (would be v3-historic high — but single-seed-suspect; 27× IS/OOS daily Sharpe ratio is structurally absurd) | EXPLORATION-NEGATIVE-SUSPICIOUS-OOS | NO — IS PATH C fires; OOS untrustable at single-seed (iter-v3/013 precedent: +2.70 OOS falsified to +0.39 at multi-seed); engineered features don't stack at single-seed n_trials=35; iter-v3/027 = DIFFERENT engineered feature alone on top of regime_momentum (drop vol_adj_autocorr) |`
