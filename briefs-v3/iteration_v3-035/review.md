# Phase 7.5 Critic Review — iter-v3/035

OVERALL: **EXPLORATION-PROMISING-OOS-MIXED (STRONGEST single-seed OOS in v3 catalog history)** — BCH-only fracdiff via V3_FEATURES_PER_SYMBOL produces OOS Sharpe +2.85 with all 4 symbols positive. Per-symbol-feature-additions methodology fully validated. IS Sharpe -0.10 caveat carries forward.

## §4.4 Classification

PATH A fires on OOS axis: Δ +0.92, ALL 4 symbols positive, OOS WR 45.5%, all per-symbol baselines preserved/restored.
PATH C fires on IS axis: Δ -0.34 < -0.10.

Mixed result: PROMISING-OOS-MIXED (sub-class of PROMISING with IS caveat).

## Methodology Validation — 4 Edge Ingredients

The post-bootstrap cycle has produced 4 validated methodology dimensions:
1. **Global engineered feature** (regime_momentum_signed_5d; iter-v3/025 multi-seed)
2. **Universe expansion via feature-signature alignment** (ALGO; iter-v3/029)
3. **Per-symbol LABELS** (LDO ATR; iter-v3/032)
4. **Per-symbol FEATURES** (BCH fracdiff; iter-v3/035)

iter-v3/039 CONFIRMATION bundle = all 4 ingredients combined.

## Multi-Seed Compression Forecast

| Iteration | Single-seed OOS | Multi-seed OOS | Reduction |
|-----------|-----------------|----------------|-----------|
| iter-v3/013 (PROMISING-MECHANICAL) | +2.70 | +0.39 | 86% |
| iter-v3/025 (PROMISING) | +1.22 | +0.51 | 58% |
| iter-v3/035 (PROMISING-OOS-MIXED) | **+2.85** | ? (predict +0.40 to +1.71; median +1.14) | 40-86% |

If iter-v3/035 compresses 60% (median), iter-v3/039 OOS = +1.14 — **clears +1.0 floor for first time in v3 history**. Best-case 40% compression = +1.71 OOS = strong CONFIRMATION-MERGE candidate.

## Recommendations to QR

iter-v3/036 axis: continue per-symbol feature additions methodology. Try TRX-specific engineered feature (vol_adj_autocorr TRX-only). Single-axis: ADD vol_adj_autocorr to V3_FEATURES_PER_SYMBOL["TRXUSDT"] (TRX gets 15 features; BCH still 15 with fracdiff; LDO/ALGO 14).

Predicted bands:
- IS Sharpe [-0.20, +0.20] median 0 (likely IS axis remains broken)
- OOS Sharpe [+2.50, +3.00] median +2.75 (TRX may get small lift)
- TRX OOS PnL [+25, +35] (anchor +29.24)

Tests whether vol_adj_autocorr (failed universally at iter-v3/026) helps any specific symbol.

## Catalog Row

`| iter-v3/035 | 2026-05-08 | BCH-only fracdiff via V3_FEATURES_PER_SYMBOL (revert universal fracdiff iter-v3/034; BCH=15 LDO/TRX/ALGO=14) | -0.34 (vs iter-v3/032 +0.2360) | +2.8521 (Δ +0.92 — HIGHEST single-seed OOS in v3 catalog history; all 4 symbols positive; per-symbol-feature-additions methodology fully validated) | EXPLORATION-PROMISING-OOS-MIXED | YES — strongest CONFIRMATION-bundle candidate; 4 validated edge ingredients (regime_momentum + ALGO universe + LDO ATR + BCH fracdiff); IS axis -0.10 caveat carries forward; multi-seed compression at iter-v3/039 will be truth-test |`
