# Phase 7.5 Critic Review — iter-v3/031

OVERALL: **EXPLORATION-NEGATIVE (clean — counter-intuitive)** — drop-LDO HURT both IS (-0.51) and OOS (-0.17). The drop-MKR precedent did NOT transfer because LDO is IS-positive/OOS-marginally-negative (overfit pattern), not IS-negative/OOS-negative (true drag like MKR was).

## Per-Check Status

All 12 methodology checks PASS or PASS-EXPLORATION. BCH/TRX/ALGO bit-identical to iter-v3/029 (per-symbol Optuna independence confirmed).

## §4.4 Classification

PATH C fires unambiguously on IS axis (Δ -0.51 ≪ -0.10).

## Critical Methodology Lesson

The "drop chronically-OOS-negative symbol" heuristic from iter-v3/013/feedback_v3_mkr_threshold_compression.md only applies when the symbol is **drag in BOTH directions** (IS-negative AND OOS-negative). LDO violates this pattern:
- LDO IS PnL contribution: +40.03 (POSITIVE — actually fits IS well)
- LDO OOS PnL contribution: -3.07 (SMALL negative)
- Net: IS-overfit pattern, not true drag

The 9-of-9 OOS-negative trajectory (used to justify drop-LDO) was MISLEADING. Should have checked IS contribution before dropping.

**Memory rule recommendation**: `feedback_v3_drop_symbol_requires_dual_drag.md` — codify that drop-symbol only applies when chronic-negative on BOTH IS AND OOS. IS-positive/OOS-mildly-negative is an OVERFIT signature requiring a DIFFERENT fix (better features, better labels, or different model architecture).

## Recommendations to QR

iter-v3/032 axis: **RESTORE LDO + try per-symbol ATR multipliers** (NEW labeling architecture extending the per-symbol pattern from V3_FEATURES_PER_SYMBOL).

Rationale:
1. iter-v3/030 showed LDO doesn't benefit from per-symbol feature subset
2. iter-v3/031 showed LDO can't be dropped without losing IS edge
3. LDO's issue is REGIME MISMATCH (different volatility profile) → addressable at LABELING layer, not feature layer
4. ATR(2.0, 1.0) is universal across all symbols; LDO might need different multipliers
5. Direct response to user's "features per symbol" extended to "labels per symbol"

Implementation:
- Add `V3_ATR_MULTIPLIERS_PER_SYMBOL` dict
- Default: (2.0, 1.0) for BCH+TRX+ALGO
- LDO: try (2.5, 1.25) or (1.5, 0.75) — TBD by EDA on LDO volatility distribution
- Architecture parallel to V3_FEATURES_PER_SYMBOL

Predicted (single-seed):
- IS Sharpe [+0.70, +0.95] (anchor iter-v3/029 +0.79 + small LDO labeling lift)
- OOS Sharpe [+1.60, +1.95] (anchor +1.77; LDO contribution likely shifts)

## Catalog Row

`| iter-v3/031 | 2026-05-08 | DROP LDO from V3_MODELS (4→3 BCH+TRX+ALGO); REQUIRED_GAP 88→66 (drag-removal hypothesis) | -0.51 (vs iter-v3/029 +0.7926) | +1.5991 (Δ -0.17 — slight worsening; LDO contributed positively to IS aggregate so removal HURT) | EXPLORATION-NEGATIVE (clean — counter-intuitive) | NO — drop-MKR precedent did NOT transfer; LDO IS-positive (+40 PnL) / OOS-marginally-negative (-3) ≠ true drag like MKR (-23/-25); methodology lesson: drop-symbol requires DUAL drag (IS-neg AND OOS-neg). iter-v3/032 = restore LDO + per-symbol ATR multipliers (LABELING layer) |`
