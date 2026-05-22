# iter-v3/126 EDA Synthesis — Multi-Frequency Feature Stack (8h + 24h)

## Axis context
- /126 axis: FEATURE-CADENCE-STACK at fixed label horizon (NEW dimension in v3 catalog).
- 8h base candles + 24h-aggregated features merged causally via merge_asof.
- Universe: REVERT to /121 baseline BCH/LDO/TRX (isolates the multi-frequency axis from the /125 wild-universe confound).
- Anchor: /121 BASELINE (IS +1.3108 / OOS +0.9682 multi-seed).

## Pre-flight gate results summary

### Top-3 candidates by composite score
| Rank | Candidate | T3 R²<0.50 PASS (3 syms) | T4 |IC|<0.40 PASS (pooled) | T5 max rank | T7 SSC-RISK PASS | T6 mean AUC lift | Score |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | d24_ret_autocorr_lag1_50 | 3/3 | 1/1 | 3 | 1/1 | +0.0147 | 8.17 |
| 2 | d24_hurst_diff_100_50 | 3/3 | 1/1 | 4 | 1/1 | +0.0032 | 6.92 |
| 3 | d24_hurst_100 | 3/3 | 1/1 | 11 | 1/1 | +0.0101 | 6.91 |
| 4 | d24_regime_momentum_signed_5d | 3/3 | 1/1 | 13 | 1/1 | +0.0107 | 6.77 |
| 5 | d24_ret_skew_50 | 3/3 | 0/1 | 4 | 1/1 | +0.0069 | 5.29 |

## All-candidates verdicts
| Candidate | T3 R²(BCH) | T3 R²(LDO) | T3 R²(TRX) | T4 max |IC| | T4 partner | T5 ranks (BCH/LDO/TRX) | T6 lift (3-sym mean) | T7 max share |
|---|---:|---:|---:|---:|---|---|---:|---:|
| d24_hurst_100 | 0.115 | 0.161 | 0.125 | 0.105 | hurst_100 | 7/5/11 | +0.0101 | 0.422 |
| d24_hurst_diff_100_50 | 0.165 | 0.155 | 0.046 | 0.159 | hurst_100 | 1/4/4 | +0.0032 | 0.440 |
| d24_range_realized_vol_50 | 0.657 | 0.699 | 0.811 | 0.751 | range_realized_vol_50 | 1/3/1 | +0.0031 | 0.413 |
| d24_ret_kurt_50 | 0.330 | 0.289 | 0.595 | 0.611 | ret_kurt_200 | 4/1/3 | -0.0031 | 0.494 |
| d24_ret_skew_50 | 0.484 | 0.351 | 0.499 | 0.594 | ret_skew_200 | 4/2/2 | +0.0069 | 0.378 |
| d24_ret_kurt_200 | 0.081 | 0.400 | 0.543 | 0.616 | ret_kurt_200 | 5/8/3 | +0.0151 | 0.390 |
| d24_ret_skew_200 | 0.209 | 0.457 | 0.499 | 0.576 | ret_skew_200 | 1/5/7 | -0.0038 | 0.481 |
| d24_max_dd_window_50 | 0.756 | 0.849 | 0.746 | 0.774 | max_dd_window_50 | 9/3/13 | +0.0076 | 0.531 |
| d24_vwap_dev_20 | 0.827 | 0.867 | 0.731 | 0.807 | ema_spread_atr_20 | 12/12/13 | +0.0038 | 0.427 |
| d24_ema_spread_atr_20 | 0.917 | 0.912 | 0.903 | 0.948 | ema_spread_atr_20 | 13/6/15 | -0.0005 | 0.755 |
| d24_ret_autocorr_lag1_50 | 0.155 | 0.084 | 0.139 | 0.160 | btc_ret_14d | 2/1/3 | +0.0147 | 0.368 |
| d24_btc_ret_14d | 0.927 | 0.921 | 0.922 | 0.957 | btc_ret_14d | 6/9/11 | +0.0029 | 0.465 |
| d24_sym_vs_btc_ret_7d | 0.841 | 0.851 | 0.830 | 0.900 | sym_vs_btc_ret_7d | 13/9/12 | +0.0062 | 0.462 |
| d24_regime_momentum_signed_5d | 0.193 | 0.031 | 0.156 | 0.285 | regime_momentum_signed_5d | 12/8/13 | +0.0107 | 0.591 |

## Verdict
- **Top candidate**: `d24_ret_autocorr_lag1_50` (composite score 8.17).
- T3 LR-PF: 3/3 syms PASS at R² < 0.50; T4 IC-PF: 1/1 pooled PASS at |IC| < 0.40; T7 SSC-RISK: 1/1 PASS at < 0.70 single-sym share; T5 ranks (per-sym): [2, 1, 3] (max rank 3); T6 mean AUC lift across 3 syms: +0.0147.
- This candidate is the ONE 24h feature appended as the 15th feature in V3_FEATURE_COLUMNS_TOP_N for /126 EXPLORATION. Per `feedback_v3_engineered_features_dont_stack.md`, single-feature-at-a-time discipline holds; do NOT stack multiple 24h features in one EXPLORATION.

## Look-ahead audit verdict
- T2 audit verdict per symbol: {'BCHUSDT': 'PASS', 'LDOUSDT': 'PASS', 'TRXUSDT': 'PASS'}
- Min lag across all 3 syms: 0.00 hours; median 8.00 hours. All non-negative — causal merge_asof verified.

## Brief Section 2 evidence inventory
- T1_inventory.csv — data depth + non-NaN counts per symbol.
- T2_lookahead_audit.csv — causal merge_asof audit (PASS gate).
- T3_linear_redundancy.csv — joint R² vs 14 incumbents (LR-PF strict < 0.50).
- T4_pairwise_ic.csv — pairwise IC matrix (IC-PF strict < 0.40).
- T5_lgbm_importance.csv — per-symbol 14+1 LightGBM importance ranks.
- T6_walkforward_auc.csv — 5-fold walk-forward AUC lift per candidate.
- T7_ssc_risk.csv — SSC-RISK gate per candidate.
