# Phase 7.5 Critic Review — iter-v3/036

OVERALL: **EXPLORATION-NEGATIVE** — TRX vol_adj_autocorr hurt TRX (-15.16 swing); same INERT/HARMFUL pattern as iter-v3/026 universal application. Feature closed.

## §4.4 Classification

PATH C fires on per-symbol axis (TRX dropped -15.16 OOS PnL, -10pp WR drop).

## Lesson

Per-symbol feature additions only help when the feature has GENUINE signal for that symbol. fracdiff for BCH worked (BCH has memory persistence regime). vol_adj_autocorr for TRX failed (TRX doesn't have signal in autocorrelation/vol ratio). Random per-symbol pairings don't help.

iter-v3/035 remains the best result and the iter-v3/039 CONFIRMATION bundle target.

## Recommendations

iter-v3/037: REVERT TRX vol_adj_autocorr + ADD LDO-only cross_asset_divergence_norm.

LDO uniquely uses btc_ret_14d at rank 6 (other symbols rank 14) — has BTC-coupling signal. cross_asset_divergence_norm = (sym_ret_7d - btc_ret_14d) / (vwap_dev_20 + 1e-6) captures relative-strength normalized. Per-symbol application may work where universal (iter-v3/027) failed.

## Catalog Row

`| iter-v3/036 | 2026-05-08 | TRX-only vol_adj_autocorr via V3_FEATURES_PER_SYMBOL | -0.12 (vs iter-v3/035 -0.10) | +2.3366 (Δ -0.52; TRX dropped -15.16 / 42.0% WR) | EXPLORATION-NEGATIVE | NO — vol_adj_autocorr universal+per-symbol both failed; feature CLOSED; iter-v3/037 = revert + LDO-only cross_asset_divergence_norm |`
