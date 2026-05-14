# iter-v3/064 — Research Brief

**Branch**: `iteration-v3/064`
**EDA SHA**: `4a9f9c9`
**Setup commit SHA**: (this commit — LOCKED at brief commit)
**Iteration type**: EXPLORATION (cycle 1 #5 of 10; PHASED MASS-EXPANSION #1)
**Axis**: REVERT V3_FEATURE_COLUMNS_TOP_N to /060 14-feature anchor + ADD `adx_14` = 15 features

---

## Section 0 — Data Split Declaration

**UNCHANGED.** OOS_CUTOFF_DATE = `2025-03-24` (IMMUTABLE; sacred constant per `feedback_no_cheating.md`). Training window = 24 months walk-forward (IMMUTABLE per `feedback_training_window.md`). Symbol universe = BCHUSDT, LDOUSDT, TRXUSDT (3 symbols, UNCHANGED from /051 SYSTEM-LEVEL REVERT).

## Section 0.5 — Iteration Type Declaration

**TYPE**: EXPLORATION.

- **Cycle 1 EXPLORATION slot**: #5 of 10 (post /058 RE-ANCHOR; cycle counting reset per `feedback_v3_mass_feature_expansion.md` original entry).
- **Sub-type**: PHASED MASS-EXPANSION #1 — first phased single-feature addition under amended `feedback_v3_mass_feature_expansion.md` (2026-05-14 amendment after /063 SUSPICIOUS-OOS-DOMINANT + IS-COLLAPSE).
- **Run mode**: `--exploration` (ENSEMBLE_SIZE=3, seeds from outer=42 lineage subset [191664963, 1662057957, 1405681631]).
- **Optuna budget**: `--n-trials 35` per (symbol × walk-forward month × seed). Total trials = 35 × 3 × 3 = 315 (matches /060/061/062/063 EXPLORATION-mode budget).
- **Wall-clock target**: ~1.1h (within 2h EXPLORATION HARD CAP per `feedback_v3_cadence_discipline.md`).

**Cycle 1 catalog status before /064**:

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| #1 | /060 | EXPLORATION-MODE-REFERENCE (anchor) | PROMISING-EXPLORATION |
| #2 | /061 | TRX RiskV2 anti-Kelly (Path B vol_scale_floor) | INERT-AT-EXPLORATION (closed) |
| #3 | /062 | DSR_relative recalibration (Path C passive) | PASSIVE-DIAGNOSTIC (Path B4 deferred to /069) |
| #4 | /063 | MASS FEATURE EXPANSION (Path B 46 features) | SUSPICIOUS-OOS-DOMINANT + IS-COLLAPSE (closed) |
| **#5** | **/064** | **PHASED MASS-EXPANSION #1: REVERT to 14 + ADD adx_14** | TBD |
| #6-#9 | /065-068 | TBD | TBD |
| CONFIRMATION | /069 | Bundle + Path B4 implementation | TBD |

**Why phased single-feature**: Per amended `feedback_v3_mass_feature_expansion.md` (2026-05-14): single-seed n_trials=35 mass expansion (14→46) at /063 produced IS Sharpe collapse from +0.83 to -0.55 (Δ -1.38) — Mode C (`feedback_v3_inert_features_at_higher_budget.md`) activated as predicted. The amended methodology requires either (a) phased single-feature additions at single-seed EXPLORATION, OR (b) full mass expansion at CONFIRMATION-mode multi-seed only. /064 follows path (a).

Per Critic /063 Rec #3: phased expansion is the agreed recovery path; the CYCLE-5 mass-expansion mandate (target 100, minimum 50) REMAINS but proceeds incrementally.

## Section 1 — Testable Hypothesis (ONE sentence)

> Adding `adx_14` (Wilder 1978 Average Directional Index) to the iter-v3/060 14-feature anchor produces ≥+0.10 IS Sharpe AND ≥+0.20 OOS Sharpe vs /060 baseline (IS +0.8325 / OOS +0.1403) primarily via stronger LDO trend-regime signal (where adx_14 was rank 5/46 at /063 and rank 2/15 in the leaner /064 EDA singleton-importance preview).

## Section 2 — Numerical EDA Tables (EDA SHA `4a9f9c9`)

EDA committed at SHA `4a9f9c9` (`analysis/iteration_v3-064/adx_14_singleton_eda.py`). Produces 5 tables. Anchor = iter-v3/060 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.1403; 3-seed lineage subset of /059's unified 10-seed mass). **NOT /063** (axis CLOSED per Critic FINAL `7cbc136`).

### Section 2.1 — T1 adx_14 distribution + ADF stationarity per IS symbol

| symbol  | n_obs | min  | q25  | median | q75  | max   | mean | std  | skew | kurt | adf_p (/063) | stationary_at_p05 |
|---------|------:|-----:|-----:|-------:|-----:|------:|-----:|-----:|-----:|-----:|-------------:|-------------------|
| BCHUSDT | 5700  | 7.53 | 19.26| 25.65  | 34.24| 75.47 | 27.46| 10.67| 0.79 | 0.57 | 1.05e-25     | True              |
| LDOUSDT | 2714  | 9.70 | 18.54| 23.19  | 31.70| 68.99 | 25.95| 10.21| 1.28 | 2.10 | 9.54e-16     | True              |
| TRXUSDT | 5642  | 7.42 | 17.59| 23.35  | 31.30| 72.58 | 25.71| 11.08| 1.15 | 1.43 | 8.46e-22     | True              |

**Reading**: adx_14 distribution is similar across all 3 symbols (mean 25.7–27.5, std ~10–11). Mild right-skew (consistent with extreme trend regimes being rare). ADF p < 1e-15 across all 3 — **rock-solid stationary**. The classic Wilder threshold of 25 marks "trending" regime; median is at this boundary across symbols.

### Section 2.2 — T2 adx_14 vs simplified triple-barrier label IC

| symbol  | n_obs | n_pos | n_zero | n_neg | pearson_IC | spearman_IC | mean_adx_pos | mean_adx_zero | mean_adx_neg |
|---------|------:|------:|-------:|------:|-----------:|------------:|-------------:|--------------:|-------------:|
| BCHUSDT | 1140  | 439   | 220    | 481   | +0.0191    | +0.0162     | 27.68        | 27.68         | 27.23        |
| LDOUSDT | 543   | 204   | 88     | 251   | +0.0436    | -0.0009     | 26.26        | 27.05         | 25.33        |
| TRXUSDT | 1129  | 518   | 236    | 375   | -0.0190    | -0.0343     | 25.69        | 24.86         | 26.24        |

**Reading**: Univariate IC is low (|IC| ≤ 0.044) and mixed-sign. This is **expected for trend-strength indicators**: adx_14 is a regime conditional, not a directional signal — it does NOT predict long vs short, it predicts WHEN trend-following directional features will work. Per `feedback_v3_engineered_feature_pivot.md` and `feedback_v3_lr_pf_methodology.md`, importance rank (not univariate IC) is the appropriate signal-detection metric for regime features.

LDO does show the cleanest monotone signal: mean adx 26.26 on +1 (long-wins) > 25.33 on -1 (short-wins). BCH and TRX are near-flat. LDO IS the symbol where adx_14 importance was highest at /063 (rank 5/46) — consistent.

### Section 2.3 — T3 adx_14 vs 14-feature BASELINE_V3 IC (from /063 IC matrix)

| feature_b                  | pearson_IC_adx14_vs_b | |IC|   | flag |
|----------------------------|----------------------:|-------:|-------|
| range_realized_vol_50      | +0.1621               | 0.1621 | OK    |
| btc_ret_14d                | +0.1294               | 0.1294 | OK    |
| ret_skew_50                | +0.1043               | 0.1043 | OK    |
| ema_spread_atr_20          | +0.0912               | 0.0912 | OK    |
| ret_kurt_50                | +0.0668               | 0.0668 | OK    |
| max_dd_window_50           | +0.0608               | 0.0608 | OK    |
| ret_skew_200               | +0.0530               | 0.0530 | OK    |
| vwap_dev_20                | +0.0414               | 0.0414 | OK    |
| hurst_100                  | +0.0330               | 0.0330 | OK    |
| ret_autocorr_lag1_50       | +0.0245               | 0.0245 | OK    |
| regime_momentum_signed_5d  | +0.0237               | 0.0237 | OK    |
| sym_vs_btc_ret_7d          | +0.0162               | 0.0162 | OK    |
| ret_kurt_200               | +0.0138               | 0.0138 | OK    |
| hurst_diff_100_50          | +0.0030               | 0.0030 | OK    |

**Reading**: max |IC| = 0.162 (with range_realized_vol_50). **Clean orthogonality**. No |IC| > 0.30, let alone > 0.70 — **no Category-2 carve-out required**.

(For completeness: in the /063 full 71-feature IC matrix, adx_14's only |IC| > 0.50 was with bb_width_pct_rank_100 at 0.508. bb_width_pct_rank_100 is NOT in the 14-feature anchor, so it doesn't matter for /064.)

### Section 2.4 — T4 adx_14 singleton-importance preview (15-feature LightGBM)

Diagnostic preview: trained a single LightGBM per symbol on (14 BASELINE_V3 + adx_14) features over IS-only data (simplified triple-barrier label; depth=4, 50 trees, colsample_bytree=1.0 for accurate importance).

| symbol  | n_rows | n_long_labels | adx_14_rank_of_15 | adx_14_gain | top3_features                                                |
|---------|------:|--------------:|------------------:|------------:|-------------------------------------------------------------|
| BCHUSDT | 1876  | 743           | 12                | 145.6       | ret_kurt_200(421), btc_ret_14d(338), ret_autocorr_lag1_50(310) |
| LDOUSDT | 881   | 312           | **2**             | 226.7       | max_dd_window_50(243), **adx_14(227)**, ret_kurt_200(192)     |
| TRXUSDT | 1857  | 799           | 7                 | 186.0       | range_realized_vol_50(553), ret_skew_200(362), ret_skew_50(348) |

**Comparison vs /063 (46-feature stack last-month walk-forward importance)**:

| symbol | /063 rank (of 46) | /063 gain | /064 EDA rank (of 15) | /064 EDA gain |
|--------|------------------:|----------:|----------------------:|--------------:|
| BCH    | 11/46             | 42.3      | 12/15                 | 145.6         |
| LDO    | 5/46              | 161.0     | **2/15**              | **226.7**     |
| TRX    | 25/46             | 19.3      | 7/15                  | 186.0         |

The leaner 15-feature stack shows adx_14 **gain is higher in absolute terms across all 3 symbols** than at /063 (no surprise — fewer features competing for splits). The rank is also higher relative to the smaller field. **LDO rank 2/15 is the strongest signal**: adx_14 is the second-most-important feature on LDO data after max_dd_window_50.

### Section 2.5 — T5 Predicted impact bands

Per `feedback_v3_cycle1_axis_pass_criteria.md` (PROMISING-AT-EXPLORATION = IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20 vs /060):

| metric                          | predicted_lower | predicted_upper | anchor_060 (/060)            | PROMISING target |
|---------------------------------|----------------:|----------------:|------------------------------|------------------|
| IS_monthly_sharpe_delta_vs_060  | -0.20           | +0.30           | +0.8325                       | ≥ +0.9325        |
| OOS_monthly_sharpe_delta_vs_060 | -0.30           | +0.50           | +0.1403                       | ≥ +0.3403        |
| OOS_IS_daily_ratio              | 0.20            | 0.50            | 0.21                          | ≥ 0.5 (stability)|
| BCH_IS_wpnl_delta               | -15             | +15             | BCH IS share 176.68% (/060)   | BCH IS share ≥ 80% |
| BCH_OOS_wpnl_delta              | -15             | +20             | +24.75 OOS wpnl (BCH)         | stable or improved|
| LDO_IS_wpnl_delta               | -5              | +15             | thin at /060                  | lift on trend signal|
| LDO_OOS_wpnl_delta              | -10             | +15             | -6.18 OOS wpnl (LDO)          | turns positive   |
| TRX_IS_wpnl_delta               | -10             | +10             | TRX IS thin at /060           | stable           |
| TRX_OOS_wpnl_delta              | -10             | +10             | +4.16 OOS wpnl (TRX)          | stable           |
| IS_trade_count_delta            | -5              | +15             | ~171 IS trades                | within [128, 222] |
| OOS_trade_count_delta           | -5              | +10             | 94 OOS trades                 | within [66, 122]  |
| frac_positive_paths             | 0.50            | 0.75            | 0.6444 (CPCV-invariant)       | ≥ 0.50           |

### Section 2.6 — Anchor declaration (Section 2.10 equivalent)

**Anchor**: iter-v3/060 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.1403). **NOT iter-v3/063** (axis CLOSED per Critic FINAL `7cbc136`).

iter-v3/060 is the legitimate cycle 1 EXPLORATION-mode baseline (3-seed lineage subset of /059 10-seed CONFIRMATION). Per `feedback_v3_cycle1_axis_pass_criteria.md` Rec #1: cycle 1 EXPLORATIONs use /060 as the EXPLORATION-mode anchor; CONFIRMATION-mode delta vs /059 is evaluated only at /069 CONFIRMATION.

### Section 2.7 — Summary

- adx_14 is rock-solid stationary across all 3 IS symbols.
- Clean orthogonality to the 14-feature anchor (max |IC| = 0.162).
- LDO singleton-importance rank 2/15 (highest signal among 3 symbols).
- Predicted impact: modest single-feature lift; INERT ~55%, PROMISING ~20%.
- Anchor: /060.

## Section 3 — Proposed Changes (enumerated)

### Sub-fix 1 — V3_FEATURE_COLUMNS_TOP_N rewrite (46 → 15)

**One substantive change**. REVERT to 14-feature BASELINE_V3 anchor + ADD `adx_14` = 15 features.

The 14 BASELINE_V3 features (order per BASELINE_V3.md /059 spec):
1. `max_dd_window_50`
2. `ema_spread_atr_20`
3. `ret_kurt_50`
4. `ret_skew_200`
5. `range_realized_vol_50`
6. `hurst_diff_100_50`
7. `ret_kurt_200`
8. `hurst_100`
9. `btc_ret_14d`
10. `ret_skew_50`
11. `vwap_dev_20`
12. `ret_autocorr_lag1_50`
13. `sym_vs_btc_ret_7d`
14. `regime_momentum_signed_5d`

NEW addition at /064:
15. `adx_14` (Wilder 1978 Average Directional Index; trend-strength at 14-period)

**EDA-implementation parity gate** (per Critic /063 Rec #2): V3_FEATURE_COLUMNS_TOP_N is BIT-IDENTICAL to this 15-feature set declared above. No silent additions. No substitutions. The 31 non-baseline features from /063 (ret_skew_100, obv_slope_50, btc_vol_14d, cusum_reset_count_200, ret_autocorr_lag5_50, fracdiff_logclose_dstat, volume_cv_50, hurst_200, fracdiff_d05_close, parkinson_gk_ratio_20, sym_vs_btc_vol_14d, volume_mom_ratio_20, bb_width_pct_rank_100, vol_transition_slope_20, btc_ret_7d, atr_pct_rank_500, atr_pct_rank_200, btc_ret_3d, mom_accel_20_100, trend_efficiency_signed, btc_funding_rate_zscore_30, funding_rate_zscore_30, vol_regime_x_momentum, cross_asset_divergence_norm, mom_accel_5_20, taker_buy_imbalance_20, sym_vs_btc_ret_3d, candle_dow_sin, candle_dow_cos, ret_1d, tbr_zscore_30) are all DROPPED.

### Sub-fix 2 — Code changes (all in one setup commit)

| File | Change |
|---|---|
| `src/crypto_trade/features_v3/__init__.py` | Rewrite V3_FEATURE_COLUMNS_TOP_N tuple from 46 → 15. Update `V3_FEATURES_PER_SYMBOL` docstring to reference 15-feature fallback. Update `features_for_symbol` docstring. |
| `run_baseline_v3.py` | `ITERATION_LABEL` = `"v3-064"`. Update `len(V3_FEATURE_COLUMNS)` assertion from 46 → 15. Replace 9-NEW-features check with adx_14-required + 8-REVERTED-features-absent check. Update 46-feature fallback assertion to 15. |
| `tests/features_v3/test_features_for_symbol.py` | Rewrite suite to assert 15-feature state. Add `test_adx_14_in_universal_list` + `test_iter_063_new_features_reverted`. Drop test names referencing 48. |
| `tests/features_v3/test_hurst_drift_50_200_universal.py` | Test 1 + Test 5: assert hurst_drift_50_200 ABSENT + count == 15 + adx_14 PRESENT. |
| `tests/features_v3/test_fracdiff_d05_universal.py` | Test 1: assert fracdiff_d05_close ABSENT + count == 15. |
| `tests/features_v3/test_regime_momentum_signed_3d_universal.py` | Tests 1 + 5: assert count == 15 + fracdiff_d05_close ABSENT + hurst_drift_50_200 ABSENT + adx_14 PRESENT. |
| `tests/strategies/ml/test_v3_feature_count.py` | Rewrite to assert count == 15 + adx_14 PRESENT + 8 /063-NEW REVERTED + 6 PROHIBITED ABSENT. |

### Sub-fix 3 — Parquet regeneration

NOT required. adx_14 was implemented at /063 and is already in all 3 symbol parquets at `data/features_v3/{BCHUSDT,LDOUSDT,TRXUSDT}_8h_features.parquet`. Verified by EDA T1: column present, non-NaN majority, stationary.

### Sub-fix 4 — ENSEMBLE_SIZE assertion

UNCHANGED. EXPLORATION_ENSEMBLE_SIZE=3, CONFIRMATION_ENSEMBLE_SIZE=10 (per Phase B-3 unified architecture). /064 runs with `--exploration` (ENSEMBLE_SIZE=3).

## Section 4 — Predicted Bands + Falsifiers

### Section 4.1 — Headline Sharpe prediction (single-seed EXPLORATION mode)

| Metric | /060 anchor | Predicted /064 | Predicted Δ band |
|---|---:|---:|---|
| IS monthly Sharpe | +0.8325 | +0.70 to +1.10 | Δ ∈ [-0.20, +0.30] |
| OOS monthly Sharpe | +0.1403 | -0.10 to +0.65 | Δ ∈ [-0.30, +0.50] |
| OOS/IS daily ratio | 0.21 | 0.10 to 0.50 | within [0.20, 0.50] |
| IS trades | ~171 | 165 to 185 | Δ ∈ [-5, +15] |
| OOS trades | ~94 | 90 to 105 | Δ ∈ [-5, +10] |
| frac_positive_paths | 0.6444 | 0.50 to 0.75 | architecture-invariant ≥0.50 |
| BCH IS share | 176.68% | 80%-200% | one-sided ≥ 80% per Critic /060 Rec #1 |

Rationale for band widths: this is a SINGLE FEATURE addition (low-dimensional axis change). Single-feature additions historically produce modest Sharpe shifts at single-seed n_trials=35 EXPLORATION:
- iter-v3/025 (regime_momentum_signed_5d, ENGINEERED): IS +0.50 / OOS +0.84 (PROMISING, large lift due to composed feature)
- iter-v3/019 (funding_rate_zscore_30, off-the-shelf): IS ~0 / OOS +0.39 (PROMISING-INERT)
- iter-v3/023 (same feature at n_trials=35): OOS -1.46 (NEGATIVE)
- iter-v3/015 (tbr_zscore_30, off-the-shelf): IS ~0 / OOS +1.74 (SUSPICIOUS)
- adx_14 is off-the-shelf (trend-strength); historical off-the-shelf single-feature additions cluster near INERT.

### Section 4.2 — BCH IS sensitivity prediction (per /059 Critic Rec #3 carry-forward)

BCH IS share at /060 was 176.68% (3-seed averaging structurally amplified BCH's IS dominance vs LDO+TRX). The one-sided ≥80% gate applies per `feedback_v3_cycle1_axis_pass_criteria.md` Rec #1.

adx_14 is moderate-importance at BCH (rank 12/15 in /064 EDA singleton; rank 11/46 at /063 last-month). It does NOT directly address BCH's IS dominance — it's a regime indicator that may help LDO and TRX find better entries.

**Predicted BCH IS share at /064**: 100% to 200% (one-sided ≥ 80% gate cleared; not narrowed because adx_14 is unlikely to materially alter BCH's IS contribution).

### Section 4.3 — Behavioral effect predictor (per `feedback_v3_axis_saturation_predictor.md`)

**Predicted trade-count change** (IS + OOS):

| Symbol | IS trades /060 | IS trades /064 predicted | OOS trades /060 | OOS trades /064 predicted |
|---|---:|---:|---:|---:|
| BCH | ~80 | 78-88 | ~37 | 35-42 |
| LDO | ~13 | 12-18 (lift possible) | ~13 | 12-18 (lift possible) |
| TRX | ~78 | 75-85 | ~44 | 40-48 |
| **Total** | **~171** | **[165, 191]** | **~94** | **[87, 108]** |

**Behavioral-effect rationale**: adx_14 is a trend-strength regime feature; LightGBM may use it as a regime gate to suppress signals during weak-trend regimes (adx < 25). Net effect on trade count is hard to predict — could be modest reduction (more selective signals) or modest increase (entries unlocked in strong-trend regimes). Predicted band [165, 191] IS and [87, 108] OOS allows for ±15% shift.

**Saturation falsifier**: if trade-count Δ < |5| on EITHER axis (i.e., no behavioral change), the axis is INERT — adx_14 is being ignored at colsample_bytree picks.

### Section 4.4 — Pre-registered FALSIFIER bands (BINDING GATES)

| Gate ID | Gate | Threshold | Action if FAIL |
|---|---|---|---|
| **A.1** | IS Sharpe shift | ≥ -0.20 vs /060 (i.e., IS ≥ +0.63) | FAIL → NEGATIVE / IS-COLLAPSE |
| **A.2** | OOS Sharpe shift | ≥ -0.30 vs /060 (i.e., OOS ≥ -0.16) | FAIL → NEGATIVE / OOS-NEGATIVE |
| **A.3** | frac_positive_paths | ≥ 0.50 | FAIL → methodology FAIL (CPCV degenerate) |
| **A.4** | No methodology FAIL | Critic 13 checks + §11 anti-pattern scan | FAIL → BLOCK |
| **B.5** | BCH IS share | one-sided ≥ 80% | FAIL → BCH collapse warning |
| **C.6** | IS trade count | ∈ [128, 222] | FAIL → trade-rate floor violation |
| **C.7** | OOS trade count | ∈ [66, 122] | FAIL → trade-rate floor violation |
| **D.8** | BCH IS wpnl Δ | within [-15, +15] | FAIL → per-symbol axis-design failure |
| **D.9** | BCH OOS wpnl Δ | within [-15, +20] | FAIL → BCH OOS collapse |
| **D.10** | LDO IS wpnl Δ | within [-5, +15] | FAIL → target-symbol regression |
| **D.11** | LDO OOS wpnl Δ | within [-10, +15] | FAIL → LDO OOS collapse |
| **D.12** | TRX IS wpnl Δ | within [-10, +10] | FAIL → TRX IS regression |
| **D.13** | TRX OOS wpnl Δ | within [-10, +10] | FAIL → TRX OOS regression |
| **E.14** | Tests passing | All v3 feature tests PASS | FAIL → BLOCK |
| **E.15** | ensemble_summary | mode=exploration, size=3 | FAIL → mode-flag wiring bug |
| **E.16** | EDA-impl parity | V3_FEATURE_COLUMNS_TOP_N == 15-feature set declared in Section 3 | FAIL → process violation per Critic /063 Rec #2 |

### Section 4.5 — Anti-stacking check

Per `feedback_v3_engineered_features_dont_stack.md`: adx_14 is OFF-THE-SHELF (not engineered-composed; not same-family with any other feature in the 14-anchor). No stacking concern; single-feature axis legitimate at single-seed EXPLORATION.

## Section 5 — Risk Mitigation

**UNCHANGED stack** (carry-forward from /060 anchor):

| Primitive | Status | Source |
|---|---|---|
| Vol scaling (RiskV2) | ENABLED | `feedback_v3_baseline_update_policy.md` carry-forward |
| ADX threshold (global 20.0) | ENABLED | iter-v3/050 closeout (per-symbol cleared) |
| Hurst regime gate | DISABLED | iter-v3/022 (closed) |
| Feature z-score OOD (|z|>2.0) | ENABLED | iter-v3/011 |
| Low-vol filter | ENABLED | carry-forward |
| Hit-rate gate | DISABLED | OOS-only; not active |
| BTC trend kill (±15%, 14d) | ENABLED | iter-v3/051 reverted to no-block; threshold=15% |
| Primitive 10 (direction-asymmetric kill switch) | DISABLED (block_long_for=(), block_short_for=()) | iter-v3/051 SYSTEM-LEVEL REVERT |
| Primitive 11 (per-symbol drawdown brake) | DISABLED | iter-v3/054 closeout |

No risk-primitive changes at /064 (single-axis discipline).

## Section 6 — Risk Management

**UNCHANGED**. ATR multipliers DEFAULT = (2.0, 1.0) for all 3 symbols (V3_ATR_MULTIPLIERS_PER_SYMBOL = {} empty per /051 SYSTEM-LEVEL REVERT). Triple-barrier labeling at 21-candle timeout (10080 minutes). Cooldown 2 candles post-trade.

## Section 7 — Pre-registered Failure-Mode Prediction

| Mode | Description | Probability | Expected metrics |
|---|---|---:|---|
| **INERT** | Single feature addition produces shifts within ±band; adx_14 used by trees but doesn't materially alter ranking | ~55% | IS Δ ∈ [-0.10, +0.10], OOS Δ ∈ [-0.20, +0.20] |
| **PROMISING** | adx_14 lifts LDO disproportionately (was rank 5/46 at /063; rank 2/15 in /064 EDA singleton) | ~20% | IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20 |
| **SUSPICIOUS-OOS-DOMINANT** | Single-seed lottery: OOS spikes while IS doesn't track | ~10% | IS Δ < +0.10, OOS Δ ≥ +0.20 |
| **NEGATIVE** | adx_14 introduces IS noise without OOS lift (rare for off-the-shelf trend indicator) | ~10% | IS Δ < +0.10 AND OOS Δ < 0 |
| **Methodology FAIL** | EDA-implementation parity violation; CPCV degenerate; mode-flag wiring bug | <5% | Critic 13-check BLOCK |

**Why INERT is most likely (55%)**: adx_14 is OFF-THE-SHELF (not engineered-composed; per `feedback_v3_engineered_features_proven.md` off-the-shelf NEW features have historically clustered near INERT outcomes). Even if adx_14 is used by trees at moderate importance, depth-3-5 LightGBM may not exploit it for net Sharpe lift over an already-strong 14-feature stack.

**Why PROMISING is 20%**: LDO singleton-importance rank 2/15 is the strongest individual-symbol signal in the EDA. If LDO's OOS PnL turns from -6.18 (/060) toward positive, it could lift OOS Sharpe by enough to clear the +0.20 gate. The LDO IS thin-trade-roster (~13 trades) means small lift per trade can produce material Sharpe change.

## Section 8 — LOCKED Acceptance / Path Criteria

Per `feedback_v3_cycle1_axis_pass_criteria.md`:

### Section 8.1 — PROMISING-AT-EXPLORATION (advances to /069 CONFIRMATION as candidate)

ALL of:
- **A.1** IS Sharpe shift ≥ +0.10 vs /060 (IS ≥ +0.9325)
- **A.2** OOS Sharpe shift ≥ +0.20 vs /060 (OOS ≥ +0.3403)
- **A.3** frac_positive_paths ≥ 0.50
- **A.4** No methodology FAIL (Critic 13 checks + §11 anti-pattern scan)
- **B.5** BCH IS share ≥ 80% (one-sided per Critic /060 Rec #1)
- **C.6** IS trade count ∈ [128, 222]
- **C.7** OOS trade count ∈ [66, 122]
- **D.8-D.13** Per-symbol wpnl Δ bands all within range
- **E.14** All 37+ regression tests pass
- **E.15** ensemble_summary.json shows mode=exploration, size=3
- **E.16** EDA-implementation parity gate PASS

### Section 8.2 — INERT-AT-EXPLORATION

- IS Δ within [-0.10, +0.10] OR OOS Δ within [-0.20, +0.20] (noise-band)
- AND no methodology FAIL
- Axis CLOSED for current cycle; not re-evaluated.

### Section 8.3 — SUSPICIOUS-OOS-DOMINANT

- IS Δ < +0.10 (i.e., INSIDE noise band or NEGATIVE)
- AND OOS Δ ≥ +0.20
- Axis CLOSED-PENDING-CONFIRMATION; does NOT advance to /069 as PROMISING.

### Section 8.4 — NEGATIVE

- IS Δ < -0.20 OR OOS Δ < -0.30 (either gate FAIL)
- AND no methodology FAIL
- Axis CLOSED. Adx_14 placed on PARKED list with rationale.

### Section 8.5 — NEGATIVE-SUSPICIOUS-OOS-NEGATIVE (rare)

- IS Δ < -0.20 AND OOS Δ < -0.20
- Axis CLOSED. Strong evidence against adx_14 as off-the-shelf addition.

### Section 8.6 — Methodology FAIL

- Any Critic 13-check BLOCK fires
- Iteration is INVALID; not classifiable as PROMISING/INERT/NEGATIVE.

## Section 9 — Library Stack + Reproducibility

**UNCHANGED**:
- Python 3.13, uv environment, LightGBM (`lightgbm` package), pandas, pyarrow, statsmodels.
- adx_14 implementation at `src/crypto_trade/features_v3/technical_v3.py:71-167` (Wilder ADX; past-only verified per /063 Critic Check 1). No new modules required.
- ENSEMBLE_SEEDS[0:3] = (191664963, 1662057957, 1405681631) — outer=42 lineage subset for EXPLORATION mode.

**Reproducibility stamp**:
- EDA SHA: `4a9f9c9` (`analysis/iteration_v3-064/adx_14_singleton_eda.py`)
- Setup commit SHA: (this commit — LOCKED at brief commit)
- ITERATION_LABEL: `"v3-064"`
- Parquet data: `data/features_v3/{BCHUSDT,LDOUSDT,TRXUSDT}_8h_features.parquet` (adx_14 column present per /063 generation)

## Section 10 — QR Audit Trail

**Why this axis (REVERT + adx_14)**:

1. **Critic /063 Rec #3 + amended `feedback_v3_mass_feature_expansion.md`** directed phased approach after /063 SUSPICIOUS-OOS-DOMINANT + IS-COLLAPSE (Critic FINAL `7cbc136`; diary `937f7d6`). Mass expansion 14→46 at single-seed n_trials=35 produced IS Δ -1.38; methodology amendment requires phased single-feature additions OR full mass expansion at multi-seed CONFIRMATION.

2. **Orchestrator selection of adx_14** per `feedback_v3_axis_selection_quant_discipline.md`:
   - Highest /063 last-month importance at LDO (rank 5/46, gain 161.0)
   - Moderate /063 importance at BCH (rank 11/46) and TRX (rank 25/46)
   - Off-the-shelf Wilder (1978) ADX trend-strength indicator
   - Walk-forward-safe per /063 Critic Check 1 verified past-only at `technical_v3.py:71-167`
   - Already implemented (zero new code; just feature-list update)

3. **EDA SHA `4a9f9c9`** produced 5 tables that quantitatively support adx_14 selection:
   - Stationary across all 3 IS symbols (ADF p < 1e-15)
   - Clean orthogonality (max |IC| = 0.162 vs 14-feature anchor)
   - LDO singleton-importance rank 2/15 (strongest per-symbol signal)
   - Predicted impact bands appropriately conservative for single-feature axis

4. **EDA-implementation parity (per Critic /063 Rec #2)**: V3_FEATURE_COLUMNS_TOP_N rewrite at setup commit is BIT-IDENTICAL to the 15-feature set declared in Section 3 above. No silent additions. Phase 5.5 gate (if run) asserts symmetric-difference equals documented banned-feature set.

5. **REVERT + ADD execution**: 31 non-baseline features from /063 DROPPED; 14 BASELINE_V3 features RETAINED; adx_14 ADDED. Net count: 46 → 15. All affected tests updated to match new state.

**Methodology compliance**:
- `feedback_v3_axis_selection_quant_discipline.md`: EDA committed BEFORE brief (SHA `4a9f9c9` precedes setup commit).
- `feedback_v3_axis_saturation_predictor.md`: Section 4.3 behavioral-effect predictor present with quantitative trade-count band.
- `feedback_v3_per_symbol_target_axis_falsifier.md`: Per-symbol wpnl Δ bands pre-registered for all 3 symbols (Gates D.8-D.13).
- `feedback_v3_cycle1_axis_pass_criteria.md`: PASS thresholds (IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20 vs /060) explicit.
- `feedback_v3_engineered_features_dont_stack.md`: single-feature axis at single-seed EXPLORATION (no stacking).
- `feedback_v3_dsr_mode_artifact.md`: DSR_relative INFORMATIONAL ONLY at /064 EXPLORATION mode.
- Critic /063 Rec #1 (engineering report factual-accuracy gate): future engineering report at /064 will verify walk_forward.py:113 lookahead-fix status PRESENT.
- Critic /063 Rec #2 (EDA-implementation parity gate): documented above.
- Critic /063 Rec #3 (mass-expansion mandate amendment): /064 follows phased path.

**Cannot be retroactively renegotiated**. Established at brief LOCK (setup commit).
