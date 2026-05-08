# iter-v3/033 — Per-Symbol Feature Analysis + 5th Symbol Selection

## Context

iter-v3/032 closed with 4-symbol V3_MODELS = {BCH+LDO+TRX+ALGO}. ALGO was added at iter-v3/029 under per-symbol-feature-signature alignment (composite 0.6517; OOS contribution +20.87 weighted_pnl, validating the methodology). LDO was restored at iter-v3/032 under per-symbol ATR multipliers (1.5, 0.75) — labeling-layer adjustment that lifted LDO from -3.07 to +3.98 OOS. iter-v3/033 axis: ADD a 5th symbol with the same per-symbol-feature-signature criterion, applied to the new 4-symbol incumbent universe (BCH+LDO+TRX+ALGO).

## Method

Phase 1 — re-extract per-symbol feature importance from iter-v3/032 model_importance_last_month_<SYM>.csv (IS-only) for ALL 4 incumbents including ALGO + LDO post-ATR-multiplier-restore. Compute rank_range (max-min) and rank_std across BCH+LDO+TRX+ALGO. Identify SHARED top-7 features (top-7 in BCH AND LDO AND TRX AND ALGO simultaneously).

Classification thresholds (adjusted for 4-symbol universe): rank_range ≥ 7 → HIGH-DISP-SYMBOL-SPECIFIC; 4-6 → MID-DISP; ≤ 3 → LOW-DISP-SHARED.

Phase 3 — for each candidate {FILUSDT, VETUSDT, ATOMUSDT}: run 3 gates. Gate 1 = data quality (coverage + pre-IS history); Gate 2 = liquidity (IS-window avg + P10 daily quote volume); Gate 3 = feature signature alignment composite (0.65·alignment_score + 0.20·natr_band_OK + 0.15·btc_coupling_z; alignment_score = mean abs Pearson of SHARED-top features' time-series vs each of 4 incumbents).

**Excluded candidates:** HBAR + AVAX (iter-v3/021 NEGATIVE-clean dead-path); ALGO (already absorbed at iter-v3/029); ADA (narrow pre-IS history per iter-v3/021 EDA).

## Per-symbol top-7 and bottom-7 features (4 incumbents)

| Symbol | Top-7 (rank 1-7) | Bottom-7 (rank 8-14) |
|---|---|---|
| **BCHUSDT** | ret_kurt_50 | ema_spread_atr_20 | range_realized_vol_50 | max_dd_window_50 | sym_vs_btc_ret_7d | ret_skew_200 | ret_kurt_200 | ret_skew_50 | hurst_100 | ret_autocorr_lag1_50 | btc_ret_14d | vwap_dev_20 | regime_momentum_signed_5d | hurst_diff_100_50 |
| **LDOUSDT** | ret_kurt_50 | vwap_dev_20 | ret_skew_200 | ret_kurt_200 | range_realized_vol_50 | ema_spread_atr_20 | sym_vs_btc_ret_7d | btc_ret_14d | max_dd_window_50 | hurst_100 | ret_skew_50 | ret_autocorr_lag1_50 | hurst_diff_100_50 | regime_momentum_signed_5d |
| **TRXUSDT** | range_realized_vol_50 | ema_spread_atr_20 | hurst_100 | vwap_dev_20 | ret_kurt_50 | ret_skew_200 | ret_skew_50 | ret_autocorr_lag1_50 | max_dd_window_50 | btc_ret_14d | ret_kurt_200 | sym_vs_btc_ret_7d | hurst_diff_100_50 | regime_momentum_signed_5d |
| **ALGOUSDT** | max_dd_window_50 | ret_skew_50 | range_realized_vol_50 | ret_kurt_50 | vwap_dev_20 | ret_skew_200 | ret_kurt_200 | ema_spread_atr_20 | ret_autocorr_lag1_50 | btc_ret_14d | hurst_diff_100_50 | hurst_100 | sym_vs_btc_ret_7d | regime_momentum_signed_5d |

## Cross-symbol feature dispersion ranking (4 incumbents)

Sorted by rank_range descending. HIGH dispersion = SYMBOL-SPECIFIC.

| Feature | rank_BCH | rank_LDO | rank_TRX | rank_ALGO | rank_range | norm_std | norm_mean | classification |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| vwap_dev_20 | 12 | 2 | 4 | 5 | 10 | 0.2063 | 0.6548 | HIGH-DISP-SYMBOL-SPECIFIC |
| hurst_100 | 9 | 10 | 3 | 12 | 9 | 0.1626 | 0.6058 | HIGH-DISP-SYMBOL-SPECIFIC |
| ret_skew_50 | 8 | 11 | 7 | 2 | 9 | 0.1472 | 0.6478 | HIGH-DISP-SYMBOL-SPECIFIC |
| sym_vs_btc_ret_7d | 5 | 7 | 12 | 13 | 8 | 0.0813 | 0.5865 | HIGH-DISP-SYMBOL-SPECIFIC |
| max_dd_window_50 | 4 | 9 | 9 | 1 | 8 | 0.1626 | 0.7215 | HIGH-DISP-SYMBOL-SPECIFIC |
| ret_kurt_200 | 7 | 4 | 11 | 7 | 7 | 0.0847 | 0.6500 | HIGH-DISP-SYMBOL-SPECIFIC |
| ema_spread_atr_20 | 2 | 6 | 2 | 8 | 6 | 0.1360 | 0.8255 | MID-DISP |
| ret_autocorr_lag1_50 | 10 | 12 | 8 | 9 | 4 | 0.1128 | 0.5381 | MID-DISP |
| range_realized_vol_50 | 3 | 5 | 1 | 3 | 4 | 0.1106 | 0.8242 | MID-DISP |
| ret_kurt_50 | 1 | 1 | 5 | 4 | 4 | 0.1300 | 0.8724 | MID-DISP |
| hurst_diff_100_50 | 14 | 13 | 13 | 11 | 3 | 0.1752 | 0.4210 | LOW-DISP-SHARED |
| ret_skew_200 | 6 | 3 | 6 | 6 | 3 | 0.0699 | 0.7093 | LOW-DISP-SHARED |
| btc_ret_14d | 11 | 8 | 10 | 10 | 3 | 0.1375 | 0.5643 | LOW-DISP-SHARED |
| regime_momentum_signed_5d | 13 | 14 | 14 | 14 | 1 | 0.0528 | 0.3216 | LOW-DISP-SHARED |

## Classification summary

- HIGH-DISP-SYMBOL-SPECIFIC (6): vwap_dev_20, hurst_100, ret_skew_50, sym_vs_btc_ret_7d, max_dd_window_50, ret_kurt_200
- MID-DISP (4): ema_spread_atr_20, ret_autocorr_lag1_50, range_realized_vol_50, ret_kurt_50
- LOW-DISP-SHARED (4): hurst_diff_100_50, ret_skew_200, btc_ret_14d, regime_momentum_signed_5d

## SHARED top-7 features across ALL 4 incumbents

**3 feature(s)** in the top-7 of BCH AND LDO AND TRX AND ALGO simultaneously: `range_realized_vol_50, ret_kurt_50, ret_skew_200`.

These are the alignment targets for Gate 3 — any new symbol's compatibility with V3_FEATURE_COLUMNS is best approximated by its feature-signature alignment with these.


## Phase 3 — Candidate evaluation (3 gates)

| Symbol | Gate1 | Gate2 | Gate3 alignment_score | composite | NATR_21% | NATR_OK | btc_coupling_std | raw_corr_mean | gates_pass |
|---|:---:|:---:|---:|---:|---:|:---:|---:|---:|:---:|
| **VETUSDT** | PASS | PASS | 0.5176 | 0.6833 | 3.97 | PASS | 0.0935 | 0.6058 | PASS |
| **FILUSDT** | PASS | PASS | 0.4619 | 0.6502 | 4.15 | PASS | 0.0938 | 0.5846 | PASS |
| **ATOMUSDT** | PASS | PASS | 0.4867 | 0.5164 | 3.54 | PASS | 0.0793 | 0.5828 | PASS |

## Per-feature alignment detail (for candidates that PASSED Gate 1+2)

alignment features used: `range_realized_vol_50+ret_kurt_50+ret_skew_200`

| Symbol | align_range_realized_vol_50 | align_ret_kurt_50 | align_ret_skew_200 |
|---|---:|---:|---:|
| VETUSDT | 0.7107 | 0.4434 | 0.3988 |
| FILUSDT | 0.6557 | 0.4042 | 0.3258 |
| ATOMUSDT | 0.6631 | 0.4652 | 0.3319 |

## Liquidity detail (Gate 2 numerical)

| Symbol | IS qvol mean | IS qvol P10 | OOS qvol mean | OOS qvol P10 |
|---|---:|---:|---:|---:|
| VETUSDT | $38,354,502 | $9,710,017 | $17,487,804 | $6,543,210 |
| FILUSDT | $220,690,320 | $68,535,083 | $152,992,153 | $72,684,521 |
| ATOMUSDT | $105,837,753 | $38,849,988 | $40,615,168 | $15,189,380 |

## Coverage detail (Gate 1 numerical)

| Symbol | IS klines | first close_time | pre-IS months | IS coverage % |
|---|---:|---:|---:|---:|
| VETUSDT | 2169 | 2020-02-14 | 37.50 | 100.00 |
| FILUSDT | 2169 | 2020-10-16 | 29.46 | 100.00 |
| ATOMUSDT | 2169 | 2020-02-07 | 37.73 | 100.00 |

## QR Recommendation

**TOP CANDIDATE**: **VETUSDT** (composite 0.6833; alignment_score 0.5176; NATR_21 3.97%).

All 3 gates PASS for VETUSDT: data quality (Gate 1), liquidity (Gate 2), feature signature alignment (Gate 3). The selection criterion is the same iter-v3/029 methodology that successfully predicted ALGO's positive contribution: highest feature-signature alignment with the incumbents' SHARED top-N features, NOT lowest raw return correlation (the iter-v3/021 falsified criterion).


## Sanity-check: per-symbol OOS PnL — iter-v3/032 (informational only)

*Feature selection above depends ONLY on IS importance ranks and IS-window kline data. The OOS columns confirm the concentration is real and motivates the 5th-symbol-add axis.*

| Symbol | IS trades | IS net_pnl% | OOS trades | OOS net_pnl% | OOS WR% |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 94 | +23.62 | 38 | +10.75 | 39.5 |
| LDOUSDT | 14 | -21.91 | 20 | +3.98 | 35.0 |
| TRXUSDT | 85 | -7.28 | 46 | +29.24 | 52.2 |
| ALGOUSDT | 63 | -33.50 | 25 | +20.87 | 40.0 |

## Caveats


- Alignment_score is computed on time-aligned feature time-series; it does NOT predict the candidate's per-symbol PnL contribution at single-seed n_trials=35. The empirical question this EXPLORATION answers is whether the alignment translates to productive LightGBM fitting in the 5-symbol bundle.
- Single-axis discipline: ONE NEW symbol; V3_MODELS 4 → 5; REQUIRED_GAP 88 → 110 = (21+1)×5. KEEP V3_FEATURE_COLUMNS=14 byte-identical (regime_momentum_signed_5d preserved). KEEP V3_ATR_MULTIPLIERS_PER_SYMBOL with LDO entry; do NOT apply the (1.5, 0.75) multiplier to the new symbol unless its IS NATR distribution suggests otherwise (band check below).
- iter-v3/021 / HBAR+AVAX (combined IS PnL -86%) is the structural warning: universe expansion at single-seed --exploration budget is risky. The per-symbol-feature-signature criterion is the corrected selection mechanism; iter-v3/029's ALGO success at +20.87 OOS confirms the methodology, but a single positive outcome does NOT guarantee generalization.
- NATR band test for the new symbol's labeling: if the candidate's NATR_21 distribution is materially higher than the (1.5, 0.75) band fits (>5% sustained), recommend testing default (2.0, 1.0) multipliers — NOT applying LDO's adaptation. (Diagnostic only; the iter-v3/033 brief uses default multipliers per single-axis discipline.)
