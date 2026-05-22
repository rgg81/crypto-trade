# Phase 7.5 Critic Review — iter-v3/034

OVERALL: **EXPLORATION-NEGATIVE-IS-AXIS** with **VALUABLE PER-SYMBOL INSIGHT** — fracdiff_d05_close is per-symbol-specific (helps BCH +37.98 OOS swing, hurts TRX -20.11). Universal application produces IS Sharpe collapse to -0.16 but reveals the methodology innovation: feature ADDITIONS should be per-symbol, not universal.

## §4.4 Classification

PATH C fires: IS Δ -0.40 ≪ -0.10 threshold.

## Methodology Insight

Feature importance:
- regime_momentum_signed_5d: 251 (top)
- fracdiff_d05_close: 240 (rank 2; meaningfully used)

fracdiff is NOT INERT — both engineered features are meaningfully used. The IS Sharpe collapse is NOT from feature INERTness; it's from per-symbol mismatch (helps BCH, hurts TRX).

Per-symbol PnL trajectory comparison:
| Symbol | iter-v3/032 | iter-v3/034 | Δ |
|--------|-------------|-------------|------|
| BCH | +10.75 | +48.73 | **+37.98** ✓ |
| TRX | +29.24 | +9.13 | **-20.11** ✗ |
| ALGO | +20.87 | +12.63 | -8.24 ✗ |
| LDO | +3.98 | -2.83 | -6.81 ✗ |

Universal fracdiff = net OOS Sharpe still positive (+1.77) due to BCH carrying, but at cost of single-symbol concentration risk (BCH 68.86%) and IS axis breakdown.

## Methodology Recommendation

iter-v3/035 axis: **BCH-only fracdiff via V3_FEATURES_PER_SYMBOL**.

Rationale:
1. fracdiff genuinely helps BCH (+38 OOS swing)
2. Universal application hurts TRX/ALGO/LDO
3. Per-symbol architecture (V3_FEATURES_PER_SYMBOL) exists from iter-v3/030 — proven to work even if iter-v3/030 hypothesis (LDO subset) was wrong
4. BCH gets 15 features; LDO/TRX/ALGO keep 14
5. Tests "per-symbol engineered feature addition" methodology

This is the natural extension of iter-v3/032's per-symbol ATR (per-symbol labels) → per-symbol features (per-symbol additions, not subsets).

## Catalog Row

`| iter-v3/034 | 2026-05-08 | DROP VET (5→4) + ADD fracdiff_d05_close (LdP AFML Ch. 5) universal (V3_FEATURE_COLUMNS 14→15) | -0.40 (vs iter-v3/032 +0.2360) | +1.7713 (Δ -0.16; OOS MaxDD 17.55% best in v3) | EXPLORATION-NEGATIVE-IS-AXIS | NO — fracdiff per-symbol-specific (helps BCH +38 swing, hurts TRX -20); universal application breaks IS; iter-v3/035 = BCH-only fracdiff via V3_FEATURES_PER_SYMBOL |`
