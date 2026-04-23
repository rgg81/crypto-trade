# QR Phase 1 — Feature-level EDA findings (IS-only)

**Computed**: 2026-04-23, strict IS only (close_time < 2025-03-24).
**Data**: pooled IS across DOGE/SOL/XRP/NEAR (20,637 rows).
**Tool**: `qr_phase1_feature_eda.py`.

## 1. Feature correlation — MASSIVE redundancy

`V2_FEATURE_COLUMNS` has 40 features but 8 pairs are highly correlated
(|rho| > 0.85). Several are essentially IDENTICAL:

| Pair | rho | Action |
|---|---|---|
| `range_realized_vol_50` ↔ `parkinson_vol_50` | **1.000** | drop one |
| `parkinson_vol_20` ↔ `garman_klass_vol_20` | 0.997 | near-duplicate |
| `garman_klass_vol_20` ↔ `rogers_satchell_vol_20` | 0.996 | near-duplicate |
| `parkinson_vol_20` ↔ `rogers_satchell_vol_20` | 0.988 | near-duplicate |
| `vwap_dev_50` ↔ `close_pos_in_range_50` | 0.927 | very close |
| `atr_pct_rank_500` ↔ `atr_pct_rank_1000` | 0.905 | different horizons, mostly same |
| `vwap_dev_20` ↔ `close_pos_in_range_20` | 0.905 | near-duplicate |
| `ema_spread_atr_20` ↔ `vwap_dev_50` | 0.878 | moderate |

**4 out of the "efficient OHLC volatility estimators" (Parkinson, Garman-Klass,
Rogers-Satchell, realized-vol-50) are virtually identical on 8h crypto data.**
They're meaningfully different in theory but not empirically on this data.
This is model capacity spent on nothing — LightGBM with `colsample_bytree<1`
just randomly picks one of the 4 clones in each tree.

**Proposed pruning**: drop 6 redundant features → 40 → 34 features. Keep:
- `parkinson_vol_20` (the representative OHLC vol)
- `atr_pct_rank_200` (keep 200 and 500, drop 1000)
- `vwap_dev_20`, `vwap_dev_50` (drop `close_pos_in_range_20`, `_50`)
- `range_realized_vol_50` (drop `parkinson_vol_50`)
- Drop `garman_klass_vol_20`, `rogers_satchell_vol_20`

## 2. Non-stationarity — 8 features drift significantly across IS halves

| Feature | Mean-drift (in std units) |
|---|---|
| `btc_vol_14d` | **0.971** ← largest |
| `range_realized_vol_50` | 0.782 |
| `parkinson_vol_50` | 0.782 |
| `max_dd_window_50` | 0.778 |
| `parkinson_vol_20` | 0.660 |
| `garman_klass_vol_20` | 0.648 |
| `rogers_satchell_vol_20` | 0.621 |
| `fracdiff_logclose_d04` | 0.441 |

Rolling vol features consistently non-stationary — crypto market's vol
has regime-shifted lower over 2022→2024. The model trains on one vol
regime and predicts in another.

**Proposed fix**: convert rolling vols to PERCENTILE RANKS over their own
history (as already done with `atr_pct_rank_X`). Pure levels are non-
stationary; ranks are stationary by construction.

## 3. Feature distribution — all features have healthy variance

No dead features. All 40 have >10 unique values and non-zero IQR.
Clean on this dimension.

## 4. Predictive power — strongest/weakest features (Spearman with 3-bar fwd return)

### Strongest (top 10):

| Feature | mean_rho | std across symbols |
|---|---|---|
| `fracdiff_logclose_d04` | **−0.0728** | 0.016 |
| `hl_range_ratio_20` | +0.0383 | 0.015 |
| `bb_width_pct_rank_100` | +0.0372 | 0.010 |
| `atr_pct_rank_200` | +0.0333 | 0.010 |
| `volume_mom_ratio_20` | +0.0278 | 0.009 |
| `fracdiff_logvolume_d04` | +0.0262 | 0.016 |
| `ret_skew_100` | +0.0210 | 0.018 |
| `atr_pct_rank_500` | +0.0207 | 0.017 |
| `obv_slope_50` | +0.0194 | 0.015 |
| `volume_cv_50` | +0.0181 | 0.016 |

**Key observation**: `fracdiff_logclose_d04` is the STRONGEST predictor
with NEGATIVE correlation (high fracdiff → lower forward return).
Fracdiff captures slow mean reversion — elevated fracdiff levels
historically precede pullbacks.

### Weakest (bottom 10 by |mean rho|):

`ret_skew_200` (-0.0004), `parkinson_gk_ratio_20` (-0.0002),
`sym_vs_btc_ret_7d` (-0.0005), `hurst_200` (+0.0025),
`ema_spread_atr_20` (+0.0037), `hurst_diff_100_50` (+0.0037),
`btc_ret_7d` (-0.0034), `close_pos_in_range_50` (-0.0047),
`ret_autocorr_lag1_50` (+0.0048), `parkinson_vol_50` (+0.0048).

**Many features appear to have near-zero univariate predictive power.**
Univariate rho is a CRUDE metric — features can be useful as
interactions even if univariately weak. Don't prune based on univariate
rho alone. But this flags candidates for "bold replacement" if we want
to refresh the feature set.

## Implications for QR bold proposals

1. **Feature pruning iteration** (EXPLOITATION): drop 6 redundant
   features, expect slight OOS improvement from reduced colsample
   variance. Safe move.

2. **Feature refresh iteration** (EXPLORATION): replace weak features
   with BOLD new ideas:
   - **RSI divergence feature**: price-making-new-high but RSI-making-
     lower-high. Different family, not a retread of v1.
   - **Liquidity impact proxy**: (abs(close - open) × volume) / range —
     measures trade-driven moves vs indecision
   - **Regime-change acceleration**: (hurst_100 - hurst_200) delta
   - **Gap/continuation feature**: open - prior close (overnight gap proxy)

3. **Non-stationarity fix**: ensure ALL features are stationary by
   construction (ranks, ratios, z-scores). Pure levels are a source
   of non-stationarity. Current features in violation: rolling vol
   levels (not ranked).
