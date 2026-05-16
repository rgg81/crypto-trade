# Phase 7.5 Critic Review — iter-v3/030

OVERALL: **EXPLORATION-NEGATIVE (clean)** — per-symbol feature subset for LDO did NOT help; LDO got materially worse (-29.99 OOS vs -3.07 anchor); IS Sharpe collapsed to 0.05; IS MaxDD 70.55% (worst-ever in v3). Hypothesis falsified: LDO is a structural mismatch problem, not an overfit-from-too-many-features problem.

## Per-Check Status

All 12 methodology checks PASS or PASS-EXPLORATION (informational). V3_FEATURES_PER_SYMBOL architecture works correctly (BCH/TRX/ALGO bit-identical to iter-v3/029 confirms the per-symbol dispatch is clean).

## §4.4 Classification

PATH C fires: IS Δ -0.75 ≪ -0.10 threshold. Same 22× IS/OOS suspicious-divergence pattern as iter-v3/026/027.

## LDO 9-of-9 OOS-Negative Trajectory

Established the chronic LDO underperformance across 9 consecutive iterations:
- iter-v3/018 multi-seed: -22.05 OOS (21.4% WR, 14 trades)
- iter-v3/020-027 single-seed frozen baseline: -8.93 OOS (38.5% WR, 13 trades) — across 8 iterations
- iter-v3/029 with ALGO addition: -3.07 OOS (36.4% WR, 11 trades) — best LDO performance
- iter-v3/030 with 7-feature subset: **-29.99 OOS (26.7% WR, 15 trades) — WORST**

The MKR drop-threshold rule (`feedback_v3_mkr_threshold_compression.md`) compresses the per-symbol-exclusion threshold to 5 consecutive negatives. LDO hit this at iter-v3/022; per-symbol-diagnostic axes have now been tried across iter-v3/030 (7-feature subset = LDO-specific axis); next mandated step per the rule = DROP LDO.

## Recommendations to QR

**iter-v3/031 axis MANDATORY = DROP LDOUSDT** from V3_MODELS:

1. V3_MODELS: 4 → 3 (BCH+TRX+ALGO)
2. REQUIRED_GAP: 88 → 66
3. KEEP V3_FEATURE_COLUMNS=14 (with regime_momentum_signed_5d preserved)
4. CLEAR V3_FEATURES_PER_SYMBOL dict (LDO entry obsolete; helper still works for future per-symbol experiments — do NOT remove the architecture)
5. ITERATION_LABEL "v3-030" → "v3-031"

Predicted (per iter-v3/013 PROMISING-MECHANICAL precedent — drop-MKR):
- BCH/TRX/ALGO trade rosters BIT-IDENTICAL to iter-v3/029 (per-symbol Optuna independence)
- LDO drag (-3.07 OOS) removed mechanically
- Portfolio Sharpe lifts by mechanical accounting cleanup
- IS Sharpe: [+0.85, +1.05] median +0.92 (anchor +0.79; +0.13 mechanical lift from removing LDO IS contribution)
- OOS Sharpe: [+1.85, +2.10] median +1.95 (anchor +1.77; +0.18 mechanical lift)
- Concentration: TRX top concentration may rise to 60-65% (3-symbol denominator)
- Bundle OOS trades: 109 (anchor 120, minus LDO 11) — drops below 130 floor

Per `feedback_v3_promising_mechanical_subtype.md`: drop-LDO will be classified PROMISING-MECHANICAL, NOT PROMISING — strictly accretive drag-removal, NOT new edge ingredient.

## Catalog Row

`| iter-v3/030 | 2026-05-08 | Per-symbol feature subset for LDO (V3_FEATURES_PER_SYMBOL["LDOUSDT"] = 7-feature top-7 from iter-v3/028 multi-seed) | -0.75 (vs iter-v3/029 +0.7926) — IS Sharpe collapse 0.05 | +1.0611 (Δ -0.70 vs anchor; OOS still positive but single-seed-suspect at 22× IS/OOS) | EXPLORATION-NEGATIVE (clean) | NO — LDO 7-feature subset HURT not helped (-29.99 vs -3.07 OOS); IS MaxDD 70.55% worst-ever; LDO structural mismatch confirmed; iter-v3/031 = DROP LDO (mechanical drag removal per iter-v3/013 precedent) |`
