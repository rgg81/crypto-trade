# Phase 7.5 Critic Review — iter-v3/042

OVERALL: **EXPLORATION-NEGATIVE** — universal (1.5, 0.75) ATR caused divergent per-symbol effects. TRX -33 swing while BCH +42 swing. IS aggregate collapsed -1.39.

## Lesson — Universal Customizations Cause Divergence

Cycle 2 + cycle 3 evidence:
- Universal fracdiff (iter-v3/034): BCH +38, TRX -20, ALGO -8 (mixed; IS broke)
- Universal ATR (1.5, 0.75) (iter-v3/042): BCH +42, TRX -33, ALGO -14 (mixed; IS collapsed)
- Universal feature pruning (iter-v3/041): BCH -26 (one-symbol breakage)

Universal customizations consistently produce per-symbol divergence. The 4-symbol universe has heterogeneous regime characteristics; one-size-fits-all rarely works.

## Recommendations

iter-v3/043: REVERT universal ATR + add Kaufman efficiency_ratio_50 as universal engineered feature.

Rationale:
- Different mechanism than regime_momentum (sign-flip → trend-strength ratio)
- Well-trodden technical analysis indicator
- May be universally interpretable

## Catalog Row

`| iter-v3/042 | 2026-05-09 | Universal DEFAULT_ATR_MULTIPLIERS (2.0,1.0)→(1.5,0.75) (LDO config applied universally) | -1.39 (vs iter-v3/040 +0.79) | +2.0752 (Δ +0.31; BCH +42 / TRX -33) | EXPLORATION-NEGATIVE | NO — universal labeling change has divergent per-symbol effects same as universal features; iter-v3/043 = revert + Kaufman efficiency_ratio_50 |`
