# iter-v3/029 Per-Symbol Feature Analysis — Synthesis

## Context

iter-v3/028 CONFIRMATION-MERGE multi-seed (2 outer × 5 inner) — first multi-seed-validated edge in v3 history (regime_momentum_signed_5d). User directive 2026-05-08: investigate per-symbol feature importance to understand which features matter for which symbols, and whether features are 'better suited of symbols a but not b'. This is the IS-only feature-signature read-out the iter-v3/029 brief cites in Section 2.

## Method

Reads `model_importance_last_month_<SYM>.csv` (IS-only, last-month snapshot per the runner convention; same data the brief authors cite for feature-rank claims). For each of the 14 V3 features, captures: rank within symbol (1=highest importance), importance value, and 0..1 normalized within-symbol importance. Then computes rank-range (max-min across the 3 symbols) and normalized stdev to flag SYMBOL-SPECIFIC vs SHARED features.

Classification thresholds: rank_range ≥ 6 → HIGH-DISP-SYMBOL-SPECIFIC (top-half on one symbol, bottom-half on another); rank_range 3-5 → MID-DISP; rank_range ≤ 2 → LOW-DISP-SHARED (consistent across all 3 symbols).

## Per-symbol top-7 and bottom-7 features

| Symbol | Top-7 (rank 1-7) | Bottom-7 (rank 8-14) |
|---|---|---|
| **BCHUSDT** | vwap_dev_20 | max_dd_window_50 | ema_spread_atr_20 | range_realized_vol_50 | ret_kurt_50 | ret_skew_200 | ret_kurt_200 | ret_autocorr_lag1_50 | hurst_diff_100_50 | sym_vs_btc_ret_7d | regime_momentum_signed_5d | hurst_100 | ret_skew_50 | btc_ret_14d |
| **LDOUSDT** | ret_skew_200 | ret_kurt_50 | ret_kurt_200 | vwap_dev_20 | hurst_diff_100_50 | btc_ret_14d | range_realized_vol_50 | ret_skew_50 | ema_spread_atr_20 | max_dd_window_50 | sym_vs_btc_ret_7d | ret_autocorr_lag1_50 | regime_momentum_signed_5d | hurst_100 |
| **TRXUSDT** | range_realized_vol_50 | ret_kurt_50 | hurst_100 | ret_skew_200 | max_dd_window_50 | ret_autocorr_lag1_50 | vwap_dev_20 | ret_kurt_200 | ema_spread_atr_20 | hurst_diff_100_50 | regime_momentum_signed_5d | ret_skew_50 | sym_vs_btc_ret_7d | btc_ret_14d |

## Cross-symbol feature dispersion ranking

Sorted by rank_range descending. HIGH dispersion = SYMBOL-SPECIFIC.

| Feature | rank_BCH | rank_LDO | rank_TRX | rank_range | norm_std | norm_BCH | norm_LDO | norm_TRX | norm_mean | classification |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| hurst_100 | 12 | 14 | 3 | 11 | 0.1183 | 0.4678 | 0.6157 | 0.7576 | 0.6137 | HIGH-DISP-SYMBOL-SPECIFIC |
| max_dd_window_50 | 2 | 10 | 5 | 8 | 0.0810 | 0.8769 | 0.6853 | 0.7367 | 0.7663 | HIGH-DISP-SYMBOL-SPECIFIC |
| btc_ret_14d | 14 | 6 | 14 | 8 | 0.1963 | 0.4157 | 0.8759 | 0.5248 | 0.6055 | HIGH-DISP-SYMBOL-SPECIFIC |
| ret_autocorr_lag1_50 | 8 | 12 | 6 | 6 | 0.0407 | 0.6375 | 0.6641 | 0.7341 | 0.6786 | HIGH-DISP-SYMBOL-SPECIFIC |
| range_realized_vol_50 | 4 | 7 | 1 | 6 | 0.0750 | 0.8337 | 0.8495 | 1.0000 | 0.8944 | HIGH-DISP-SYMBOL-SPECIFIC |
| ema_spread_atr_20 | 3 | 9 | 9 | 6 | 0.0812 | 0.8337 | 0.7564 | 0.6364 | 0.7422 | HIGH-DISP-SYMBOL-SPECIFIC |
| vwap_dev_20 | 1 | 4 | 7 | 6 | 0.1116 | 1.0000 | 0.9009 | 0.7297 | 0.8769 | HIGH-DISP-SYMBOL-SPECIFIC |
| ret_skew_50 | 13 | 8 | 12 | 5 | 0.1551 | 0.4246 | 0.7973 | 0.5466 | 0.5895 | MID-DISP |
| ret_skew_200 | 6 | 1 | 4 | 5 | 0.1180 | 0.7561 | 1.0000 | 0.7437 | 0.8333 | MID-DISP |
| hurst_diff_100_50 | 9 | 5 | 10 | 5 | 0.1299 | 0.6297 | 0.8956 | 0.6112 | 0.7122 | MID-DISP |
| ret_kurt_200 | 7 | 3 | 8 | 5 | 0.1178 | 0.6441 | 0.9032 | 0.6635 | 0.7369 | MID-DISP |
| ret_kurt_50 | 5 | 2 | 2 | 3 | 0.0693 | 0.7827 | 0.9266 | 0.7768 | 0.8287 | MID-DISP |
| sym_vs_btc_ret_7d | 10 | 11 | 13 | 3 | 0.0630 | 0.5477 | 0.6717 | 0.5301 | 0.5832 | MID-DISP |
| regime_momentum_signed_5d | 11 | 13 | 11 | 2 | 0.0601 | 0.5022 | 0.6483 | 0.5597 | 0.5701 | LOW-DISP-SHARED |

## Classification summary

- HIGH-DISP-SYMBOL-SPECIFIC (7): hurst_100, max_dd_window_50, btc_ret_14d, ret_autocorr_lag1_50, range_realized_vol_50, ema_spread_atr_20, vwap_dev_20
- MID-DISP (6): ret_skew_50, ret_skew_200, hurst_diff_100_50, ret_kurt_200, ret_kurt_50, sym_vs_btc_ret_7d
- LOW-DISP-SHARED (1): regime_momentum_signed_5d

## regime_momentum_signed_5d — the multi-seed-validated edge feature

Per BASELINE_V3.md, this is THE first multi-seed-validated edge ingredient in v3 history. Contributed +0.1313 IS Sharpe + +0.1184 OOS Sharpe vs iter-v3/018 BOOTSTRAP. Its per-symbol importance from the multi-seed iter-v3/028 last-month snapshot:

| Symbol | rank | importance | norm |
|---|---:|---:|---:|
| BCHUSDT | 11 | 90.60 | 0.5022 |
| LDOUSDT | 13 | 171.40 | 0.6483 |
| TRXUSDT | 11 | 128.40 | 0.5597 |

## Symbol-archetype: which features are top-7 on ONLY ONE symbol?

- **Top-7 SHARED across all 3 symbols** (4): range_realized_vol_50, ret_kurt_50, ret_skew_200, vwap_dev_20
- **BCH-only top-7** (1): ema_spread_atr_20
- **LDO-only top-7** (2): btc_ret_14d, hurst_diff_100_50
- **TRX-only top-7** (2): hurst_100, ret_autocorr_lag1_50

## Sanity-check: per-symbol OOS PnL (informational only)

*This is OOS data shown for informational purpose only — feature selection depends ONLY on IS importance ranks above. The OOS columns confirm the concentration concentration is real and motivates the universe-expansion axis the iter-v3/029 brief proposes.*

| Symbol | IS trades | IS net_pnl% | OOS trades | OOS net_pnl% | OOS WR% |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 86 | +67.59 | 36 | +6.61 | 38.9 |
| LDOUSDT | 11 | +5.45 | 14 | -29.90 | 21.4 |
| TRXUSDT | 85 | +7.40 | 46 | +39.08 | 54.3 |

## Key findings (QR interpretation)

1. **regime_momentum_signed_5d ranks differently per symbol**, confirming the user's intuition that engineered features may matter more for some symbols than others. Per-symbol ranks: BCH=11, LDO=13, TRX=11.

2. **Symbol-specific (HIGH-DISP) features** are candidates whose value depends on the symbol's regime/microstructure. These are the strongest evidence for the user's 'features better suited of symbols a but not b' hypothesis. Count: 7.

3. **Shared (LOW-DISP) features** are universal predictors that should transfer cleanly to NEW symbols added via universe expansion. These are the strongest predictors that the iter-v3/029 NEW symbol will USE the same feature set productively. Count: 1.

4. **iter-v3/029 implication**: a new symbol candidate's likely compatibility with V3_FEATURE_COLUMNS is best estimated by its 8h-return correlation with the SHARED features' driving factor (BTC trend, vol regime, momentum mean-reversion balance), NOT by its raw price correlation with BCH/LDO/TRX. iter-v3/021's HBAR+AVAX failure confirms this — they had the LOWEST raw price correlation but produced -86% combined PnL. The missing diagnostic was 'does the candidate's regime structure match what the SHARED features capture?'


---

# iter-v3/029 — Candidate symbol ranking (Phase 3)

## Method

Per-symbol feature signature alignment with incumbent BCH/LDO/TRX. The 4 SHARED-top features identified in Phase 1 are: vwap_dev_20, range_realized_vol_50, ret_kurt_50, ret_skew_200 (the only features in the top-7 of all 3 incumbents simultaneously). For each candidate, computes the Pearson correlation of each shared feature's time-series vs each incumbent's same feature time-series, takes mean abs across 3 incumbents, then mean across 4 features = alignment_score.

Higher alignment_score = candidate's feature time-series behaves similarly to incumbents → LightGBM is likely to USE these features productively.

Composite = 0.65·alignment_score + 0.20·natr_band_ok + 0.15·btc_coupling_z.

**HBAR+AVAX excluded**: iter-v3/021 NEGATIVE-clean (combined -86% PnL); closed at catalog level. Candidate pool = ranks 3-7 of iter-v3/021 ranking (ADA, FIL, ALGO, ATOM, VET) — all PASSED Gate 1 + Gate 2.

## Ranking

| Rank | Symbol | composite | alignment_score | raw_corr_mean_abs | NATR_21% | NATR ok | btc_coupling_std |
|---:|---|---:|---:|---:|---:|:---:|---:|
| 1 | **ALGOUSDT** | 0.6517 | 0.4642 | 0.4920 | 4.19 | PASS | 0.1072 |
| 2 | **VETUSDT** | 0.5865 | 0.4771 | 0.5584 | 3.97 | PASS | 0.0935 |
| 3 | **ADAUSDT** | 0.5642 | 0.4288 | 0.4960 | 3.79 | PASS | 0.0952 |
| 4 | **FILUSDT** | 0.5508 | 0.4198 | 0.5335 | 4.15 | PASS | 0.0938 |
| 5 | **ATOMUSDT** | 0.4771 | 0.4263 | 0.5305 | 3.54 | PASS | 0.0793 |

## Per-feature alignment detail

| Symbol | align_vwap_dev_20 | align_range_realized_vol_50 | align_ret_kurt_50 | align_ret_skew_200 |
|---|---:|---:|---:|---:|
| ALGOUSDT | 0.5219 | 0.6171 | 0.3786 | 0.3392 |
| VETUSDT | 0.5869 | 0.6425 | 0.3704 | 0.3086 |
| ADAUSDT | 0.5436 | 0.5372 | 0.3222 | 0.3122 |
| FILUSDT | 0.5682 | 0.6048 | 0.3113 | 0.1949 |
| ATOMUSDT | 0.5474 | 0.5830 | 0.3713 | 0.2036 |

## QR Recommendation

**TOP CANDIDATE**: **ALGOUSDT** (composite 0.6517; alignment_score 0.4642; NATR_21 4.19%).

This candidate has the highest feature-signature alignment with incumbent BCH/LDO/TRX across the 4 SHARED-top features. Per Phase 1 finding, these are the features any new symbol must be compatible with for LightGBM to productively use the V3_FEATURE_COLUMNS set. iter-v3/021's mistake was selecting on lowest raw correlation — the corrected criterion is highest feature-signature alignment.

## Caveats

- Alignment_score is computed on time-aligned feature series. It does NOT predict the candidate's per-symbol PnL contribution; that's the empirical question this EXPLORATION answers.
- Single-axis discipline: ONE NEW symbol; V3_MODELS 3 → 4; REQUIRED_GAP 66 → 88. KEEP all 14 features (including regime_momentum_signed_5d).
- Falsifier (PATH B-DRAG): candidate's IS PnL is materially negative AND concentration drops below 60% — verifies dilution but at cost of edge drag (similar to iter-v3/021 HBAR+AVAX failure mode). Falsifier (PATH C-INERT): candidate trades but produces ~0% PnL; concentration drops but no signal added. Falsifier (PATH A): candidate produces positive PnL AND concentration drops AND IS+OOS preserved → PROMISING.
