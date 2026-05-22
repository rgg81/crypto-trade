# Phase 7.5 Critic Review — iter-v3/041

OVERALL: **EXPLORATION-NEGATIVE** — pruning regime_momentum_signed_5d (rank 14 portfolio importance) broke BCH (-26 swing).

## Lesson

Pure importance-based pruning is misleading. regime_momentum_signed_5d had low aggregate importance (rank 14) but per-symbol load-bearing value (BCH model couldn't fit IS without it).

**Memory rule recommendation**: `feedback_v3_pruning_requires_per_symbol_check.md` — codify that pruning by aggregate importance can drop features with per-symbol load-bearing value. Future pruning decisions must check per-symbol importance distribution.

## Recommendations

iter-v3/042: REVERT pruning + try universal ATR (1.5, 0.75) tighter labels (LDO ATR config from iter-v3/032 applied universally). Tests labeling sensitivity without breaking per-symbol fit. Lower risk than feature changes.

## Catalog Row

`| iter-v3/041 | 2026-05-09 | Universal feature pruning (drop bottom-3: regime_momentum + sym_vs_btc + ret_skew_50; 14→11) | -0.78 (vs iter-v3/040 +0.79) | +1.0041 (Δ -0.76; BCH -26 swing) | EXPLORATION-NEGATIVE | NO — aggregate importance misleads; regime_momentum was load-bearing for BCH despite rank 14; iter-v3/042 = revert + universal tighter ATR |`
