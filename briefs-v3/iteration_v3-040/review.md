# Phase 7.5 Critic Review — iter-v3/040

OVERALL: **EXPLORATION-PROMISING-MECHANICAL** — bit-identical reproduction of iter-v3/029 config. Cycle 3 anchor established for IS-lift work.

## Verification

iter-v3/029 (anchor) vs iter-v3/040: IS +0.7926/+0.7926, OOS +1.7653/+1.7653, all per-symbol bit-identical. Per-symbol Optuna independence confirmed when V3_FEATURES_PER_SYMBOL and V3_ATR_MULTIPLIERS_PER_SYMBOL are empty.

## Recommendations

iter-v3/041 axis: feature pruning (drop bottom-3 importance features universally). Safest IS-lift axis. EDA on iter-v3/028 multi-seed importance (canonical baseline) identifies bottom-3.

## Catalog Row

`| iter-v3/040 | 2026-05-09 | REVERT per-symbol customizations (clear V3_FEATURES_PER_SYMBOL + V3_ATR_MULTIPLIERS_PER_SYMBOL); cycle 3 anchor restore | bit-identical to iter-v3/029 +0.7926 | bit-identical +1.7653 | EXPLORATION-PROMISING-MECHANICAL | YES — clean cycle 3 anchor; iter-v3/041 = feature pruning bottom-3 |`
