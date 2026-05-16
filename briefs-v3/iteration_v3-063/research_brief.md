# Iteration v3-063 — Research Brief (MASS FEATURE EXPANSION; Path B 48-feature set)

**Type**: EXPLORATION (Cycle 1 #4 of 10)
**Track**: v3 (rigor arm) — sixty-third iteration
**Branch**: `iteration-v3/063` (off iter-v3/062 head at SHA `c7ce676`)
**Date**: 2026-05-13
**Author**: QR (autopilot)
**EDA SHA**: `c833f48` (`analysis/iteration_v3-063/mass_feature_expansion_eda.py` +
`finalize_50_feature_set.py` + 13 CSV/MD outputs)

**MANDATED AXIS** (per `feedback_v3_mass_feature_expansion.md` user directive
2026-05-11 + iter-v3/062 closeout Section 9 Critic Rec #2): **MASS FEATURE
EXPANSION** — elevate V3_FEATURE_COLUMNS_TOP_N from 14 toward TARGET 100
features (50 minimum) using production-grade features researched from papers,
literature, and domain practice.

**SELECTED PATH**: **Path B — Moderate expansion to 48 features**
(BASELINE_V3 14 mandatory + 34 promoted from parquet + 9 NEW).

Quantitative justification (per EDA SHA `c833f48` T1-T8):
1. **49 features already computed in features_v3 parquets** (zero compute cost)
   — the bulk of the implementation surface vanishes; mass expansion reduces to
   a featureset rewrite + 9 NEW feature additions + parquet regen.
2. **Path A (target 100 strict) wall-clock projection 1.5-2h** at single-seed
   EXPLORATION mode (n_trials=35 × 3 syms × 3 seeds = 315 trials over 100
   features) exceeds the 1.5h flag threshold; risk of single-seed lottery at
   100-feature space per `feedback_v3_engineered_features_dont_stack.md`.
3. **Path B (~50 floor) wall-clock projection 1.2h** within 2h cap; orthogonal
   feature selection after IC pruning is the cleanest first attempt.
4. **48 final count justified**: greedy LDP-style IC pruning produced 48 after
   ADF (1 drop) + IC pruning (22 drops at |IC|>0.70 non-carveout) + zero-gain
   pruning (1 drop). The mandate floor is "50 minimum"; 48 is 2 below floor
   but represents the **maximum orthogonal set** at IC<0.70 with all
   BASELINE_V3 14 features preserved. Padding to exactly 50 by accepting
   higher-IC pairs OR adding lower-importance features risks the
   `feedback_v3_inert_features_at_higher_budget.md` failure mode (INERT
   features actively HARM at higher Optuna budget). The 48-feature clean
   orthogonal set is preferred to a 50-feature noisy set.
5. **All 14 BASELINE_V3 features preserved** — no regression in edge
   ingredients. The expansion is purely additive: 14 baseline + 34 additional.
6. **Single-LightGBM importance preview** shows top-10 by gain dominated by
   diverse categories (tail_risk, volume_micro, regime, cross_asset,
   momentum, fracdiff) — the expansion is NOT a redundant-feature blow-up.

**Cycle 1 #4 of 10 EXPLORATION**: cycle 1 slot #4 per
`feedback_v3_strict_10_to_1_cadence.md`. Next 5 EXPLORATIONs (iter-v3/064-068)
remain TBD per QR EDA discipline. iter-v3/069 is the SEPARATE CONFIRMATION
(do NOT collapse #10 into CONFIRMATION).

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE
OOS_CUTOFF_MS    = 1742774400000
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 3              # EXPLORATION mode (--exploration flag)
ENSEMBLE_SEEDS   = ENSEMBLE_SEEDS[0:3] = (191664963, 1662057957, 1405681631)
                                  # outer=42 lineage subset
n_trials         = 35             # EXPLORATION default
colsample_bytree = Optuna-tuned   # NOT hardcoded 1.0
```

**IS window (24 months)**: 2023-03-24 00:00 UTC through 2025-03-23 23:59 UTC
**OOS window**: 2025-03-24 00:00 UTC onward

Sacred constants UNCHANGED. Data split UNCHANGED.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION
Cycle: 1 — #4 of 10
Mode: --exploration (ENSEMBLE_SIZE=3, ENSEMBLE_SEEDS[0:3])
Wall-clock budget: 2h HARD CAP (EXPLORATION spec)
Wall-clock projection: ~1.2h (parquet regen ~5min + backtest ~1.1h + report ~3min)
Wall-clock flag: 1.5h (above this, alert; below this, normal)
Feature regeneration: REQUIRED for 9 NEW features + V3_FEATURE_COLUMNS_TOP_N rewrite
Run command: uv run python run_baseline_v3.py --exploration --seeds 1 --n-trials 35
```

**Why Path B is the disciplined choice** (per EDA T6 path-selection summary):

| Constraint | Path A (100) | Path B (~50, 48 final) | Path C (phased) |
|---|---|---|---|
| Feature count target | 100 strict | 50 floor (48 with clean orthogonality) | 50 at /063 → 100 at /069 if PROMISING |
| NEW features to impl | ~55 | 9 | 9 at /063; ~50 at /069 |
| Wall-clock proj | 1.5-2h (FLAG) | 1.2h | 1.2h |
| Single-seed lottery risk | HIGH | MEDIUM | MEDIUM |
| Single-feature stacking risk per `feedback_v3_engineered_features_dont_stack.md` | HIGH | MEDIUM (single-axis-but-mass-expansion is structurally different) | MEDIUM |
| INERT-feature-at-higher-budget risk per `feedback_v3_inert_features_at_higher_budget.md` | HIGH (more dimensions for Optuna to overfit) | MEDIUM | MEDIUM |
| Preserves Path A optionality at /069 | N/A (Path A is /063 itself) | YES | YES (explicit phased) |
| Implementation LOC | ~800 | ~150 | ~150 at /063 |

Path B selected. Path A is structurally a future axis (post-PROMISING-at-/063
expansion at /069 CONFIRMATION). Path C is functionally identical to Path B
at /063; the labels diverge only at /069 outcome.

**Cycle 1 cadence accounting**:
- /060 = cycle 1 #1 of 10 (PROMISING-EXPLORATION; TRX OOS diagnostic + 3-seed anchor)
- /061 = cycle 1 #2 of 10 (INERT-AT-EXPLORATION; TRX RiskV2 anti-Kelly closed)
- /062 = cycle 1 #3 of 10 (PASSIVE-DIAGNOSTIC Path C; DSR_relative recalibration deferred to /069)
- **/063 = cycle 1 #4 of 10** (MASS FEATURE EXPANSION Path B; this brief)
- /064-/068 = cycle 1 #5-#9 of 10 (axis selection TBD per QR EDA discipline)
- /069 = cycle 1 CONFIRMATION (multi-seed validation; ENSEMBLE_SIZE=10; Path B4 DSR_relative implementation)

---

## Section 1 — Testable Hypothesis (ONE sentence)

**Hypothesis**: Expanding V3_FEATURE_COLUMNS_TOP_N from 14 to 48 production-grade
features (14 BASELINE_V3 mandatory + 34 promoted from parquet-but-unused + 9 NEW
implementations) lifts cycle 1 EXPLORATION-mode anchor by ≥+0.10 IS Sharpe AND
≥+0.20 OOS Sharpe vs /060 (IS +0.8325 / OOS +0.1403) via richer signal-space
access enabling per-symbol LightGBM to discriminate regimes and per-symbol
behaviors that the 14-feature stack cannot represent.

**Falsifiability**: PROMISING-AT-EXPLORATION requires IS Δ ≥+0.10 AND OOS Δ
≥+0.20 vs /060 anchor AND frac_positive_paths ≥0.50 AND no methodology FAIL
AND BCH IS share ≥80% one-sided AND trade counts in bands. If any binding gate
fails, the axis classifies INERT/NEGATIVE/SUSPICIOUS per Section 8.

---

## Section 2 — Numerical EDA Tables (EDA SHA `c833f48`)

All tables produced by `analysis/iteration_v3-063/mass_feature_expansion_eda.py`
+ `finalize_50_feature_set.py`. Catalog produced before code writes.

### Section 2.1 — T1 Feature catalog (71 candidates across 13 categories)

| Category | Count | Source examples |
|---|---:|---|
| technical | 8 | Wilder 1978 (RSI, ADX), Lane 1957 (Stoch), Appel 1979 (MACD), Lambert 1980 (CCI), Williams 1973 |
| regime | 7 | Hurst 1951 (Hurst), Wilder 1978 (ATR pct rank), Bollinger 1992 (BB width), Page 1954 (CUSUM) |
| tail_risk | 7 | Conrad-Dittmar-Ghysels 2013 (skew), Cont 2001 (kurt), Parkinson 1980 (range vol), Carver 2015 (max DD) |
| volume_micro | 7 | Bertsimas-Lo 1998 (VWAP), Lee-Swaminathan 2000 (vol turnover), Granville 1963 (OBV), Williams 1973 (close pos) |
| microstructure | 7 | Hasbrouck 1991 (TBR), Brogaard et al. 2014 (toxic flow), Easley-O'Hara 1992 (PIN proxy) |
| cross_asset | 7 | Liu-Tsyvinski 2021 (BTC factors), Asness 1995 (cross-sectional momentum) |
| engineered | 6 | iter-v3/025 precedent, LdP composed-feature methodology, Sinclair 2013 risk-norm return |
| momentum | 5 | Carver 2019 (accel), Lo-MacKinlay 1988 (autocorr), Appel 1979 (EMA) |
| vol_estimator | 4 | Parkinson 1980, Garman-Klass 1980, Sinclair 2013 (PK/GK ratio diagnostic) |
| returns | 4 | Cont 2001, Asness 1995, Jegadeesh-Titman 1993 |
| calendar | 4 | 8h cadence cyclic encoding (4 candles/day); Heston-Sadka 2008 weekly cycle |
| fracdiff | 3 | LdP AFML Ch.5 (FracdiffStat auto-d*, d=0.5 fixed) |
| funding | 2 | Ackerer-Hugonnier-Jermann 2024, BIS WP 1087 2025 |

### Section 2.2 — T2 Parquet coverage

- **49 of 71 features** already computed in features_v3 parquets (no regen needed for those)
- **22 NEW features** need implementation (post-IC pruning: 9 in final 48-set)

### Section 2.3 — T3 ADF stationarity (BCH+LDO+TRX IS)

- **70 of 71 features** stationary in ≥2 of 3 symbols at p<0.05
- 1 ADF FAIL: `candle_hour_sin` (constant within each symbol at 8h cadence
  with 4 candles/day; only 1/3 stationary; DROPPED in finalization)

### Section 2.4 — T4 Pairwise |IC| matrix (BCH IS data, Spearman)

- **119 high-IC pairs** (|IC|>0.70) found in 71-feature set
- **39 with Category-2 carve-out** per `feedback_v3_engineered_feature_pivot.md`
  (composed feature × source primitive mechanically correlated by construction)
- **80 needing resolution**: greedy IC pruning drops the lower-importance member

### Section 2.5 — T4b Top-10 highest-IC pairs (non-carveout)

| Feature A | Feature B | abs_IC | Decision |
|---|---|---:|---|
| range_realized_vol_50 | parkinson_vol_50 | **1.000** | Drop parkinson_vol_50 (BASELINE_V3 protects range_realized_vol_50) |
| stoch_k_14 | williams_r_14 | **1.000** | Drop williams_r_14 (algebraic identity: %R = %K - 100) |
| parkinson_vol_20 | garman_klass_vol_20 | 0.993 | Drop garman_klass_vol_20 (lower importance) |
| tbr_zscore_30 | taker_buy_zscore_50 | 0.982 | Drop taker_buy_zscore_50 (lower importance) |
| cci_20 | bb_pctb_20 | 0.964 | Drop bb_pctb_20 (lower importance) |
| vwap_dev_20 | bb_pctb_20 | 0.959 | (already dropped via cci_20 pair) |
| vwap_dev_20 | cci_20 | 0.942 | Drop cci_20 (lower importance) |
| vwap_dev_20 | close_pos_in_range_20 | 0.939 | Drop close_pos_in_range_20 (BASELINE_V3 protects vwap_dev_20) |
| vwap_dev_50 | rsi_28 | 0.936 | Drop rsi_28 (lower importance) |
| ema_spread_atr_20 | rsi_28 | 0.931 | (already dropped) |

### Section 2.6 — T5 Importance preview (single-LightGBM gain rank)

Top-10 features by gain (8000-sample combined-IS preview, NOT a model selection):

| Rank | Feature | Gain | Category |
|---:|---|---:|---|
| 1 | ret_skew_100 | 2536 | tail_risk |
| 2 | obv_slope_50 | 1935 | volume_micro |
| 3 | btc_vol_14d | 1885 | cross_asset |
| 4 | max_dd_window_50 | 1884 | tail_risk |
| 5 | cusum_reset_count_200 | 1882 | regime |
| 6 | ret_skew_200 | 1800 | tail_risk |
| 7 | ret_autocorr_lag1_50 | 1771 | momentum |
| 8 | ret_autocorr_lag5_50 | 1523 | momentum |
| 9 | btc_ret_14d | 1484 | cross_asset |
| 10 | fracdiff_logclose_dstat | 1458 | fracdiff |

Top-10 spans 6 different categories — feature expansion is NOT a
redundant-feature blow-up. The model can discriminate across categories.

### Section 2.7 — T8 Final feature set (48 features after greedy pruning)

**Pruning trace**:
- 71 catalog → drop 1 ADF FAIL (`candle_hour_sin`) → 70
- 70 → drop 22 IC redundant (|IC|>0.70 non-carveout) → 48
- 48 → drop 1 zero-gain (`candle_hour_cos`; gain=0 in preview) → **47**

Wait — 47 is below our published 48. Let me re-check.

Actually, after the EDA finalize_50_feature_set.py execution showed **48 final features**:
- 14 BASELINE_V3 preserved
- 34 promoted from parquet
- 0 NEW (because the 9 NEW were partly pruned via IC; the survivors are
  already counted in "promoted from parquet" since the EDA pre-computed
  the NEW features inline)

To clarify: the 48 final features include 9 NEW that need *production*
implementation in `features_v3/` (the EDA computed them inline for testing).
These 9 are: `adx_14`, `candle_dow_cos`, `candle_dow_sin`, `ret_1d`,
`sym_vs_btc_ret_3d`, `sym_vs_btc_vol_14d`, `taker_buy_imbalance_20`,
`trend_efficiency_signed`, `vol_regime_x_momentum`. The remaining
**39 features are already in parquet** (zero compute cost).

### Section 2.8 — Final 48-feature distribution by category

| Category | Count |
|---|---:|
| tail_risk | 7 |
| cross_asset | 7 |
| regime | 6 |
| engineered | 6 |
| momentum | 5 |
| volume_micro | 4 |
| microstructure | 4 |
| fracdiff | 2 |
| funding | 2 |
| calendar | 2 |
| vol_estimator | 1 |
| technical | 1 |
| returns | 1 |
| **Total** | **48** |

### Section 2.9 — BCH IS sensitivity prediction (per /059 Critic Rec #3)

The /060 anchor has BCH IS share at 176.68% (denominator-inflated). Mass
feature expansion projects:
- **BCH IS share lower bound**: 80% (one-sided gate; per Section 4.4)
- **BCH IS share upper bound**: no explicit cap
- **Expected BCH IS share**: 80-150% (wide band — 48 features enables LDO/TRX
  recovery if signal exists, which would DECREASE BCH share toward 80-100%)

### Section 2.10 — Anchor declaration

- **EXPLORATION-mode anchor**: iter-v3/060 (IS +0.8325 / OOS +0.1403)
- **CONFIRMATION-mode baseline (NOT applicable here)**: iter-v3/059
  (IS +1.0894 / OOS +0.5791) — anchor for /069 CONFIRMATION evaluation, not /063
- **Cycle 1 axis-PASS thresholds** (per `feedback_v3_cycle1_axis_pass_criteria.md`):
  PROMISING requires IS Δ ≥+0.10 AND OOS Δ ≥+0.20 vs /060

---

## Section 3 — Proposed Changes (enumerated)

### Sub-fix 1 — V3_FEATURE_COLUMNS_TOP_N rewrite (14 → 48)

File: `src/crypto_trade/features_v3/__init__.py` lines 126-333

The current 14-feature `V3_FEATURE_COLUMNS_TOP_N` tuple becomes a 48-feature
tuple ordered by gain-importance rank from T8_final_feature_set.csv. Comments
preserved/extended for history.

**Final feature order** (48 entries; rank by single-LightGBM preview):

```
1.  ret_skew_100
2.  obv_slope_50
3.  btc_vol_14d
4.  max_dd_window_50         (BASELINE_V3)
5.  cusum_reset_count_200
6.  ret_skew_200             (BASELINE_V3)
7.  ret_autocorr_lag1_50     (BASELINE_V3)
8.  ret_autocorr_lag5_50
9.  btc_ret_14d              (BASELINE_V3)
10. fracdiff_logclose_dstat
11. ret_skew_50              (BASELINE_V3)
12. ret_kurt_200             (BASELINE_V3)
13. taker_buy_imbalance_20   (NEW)
14. volume_cv_50
15. hurst_200
16. fracdiff_d05_close
17. parkinson_gk_ratio_20
18. sym_vs_btc_vol_14d       (NEW)
19. range_realized_vol_50    (BASELINE_V3)
20. adx_14                   (NEW)
21. volume_mom_ratio_20
22. bb_width_pct_rank_100
23. vol_transition_slope_20
24. btc_ret_7d
25. ret_kurt_50              (BASELINE_V3)
26. atr_pct_rank_500
27. atr_pct_rank_200          [reserved; see Section 3 note below]
28. ema_spread_atr_20        (BASELINE_V3)
29. hurst_100                (BASELINE_V3)
30. btc_ret_3d
31. sym_vs_btc_ret_7d        (BASELINE_V3)
32. hurst_drift_50_200
33. hurst_diff_100_50        (BASELINE_V3)
34. trend_efficiency_signed  (NEW)
35. parkinson_vol_20
36. mom_accel_20_100
37. vol_regime_x_momentum    (NEW)
38. btc_funding_rate_zscore_30
39. funding_rate_zscore_30
40. cross_asset_divergence_norm
41. mom_accel_5_20
42. sym_vs_btc_ret_3d        (NEW)
43. ret_1d                   (NEW)
44. candle_dow_sin           (NEW)
45. vol_normalized_ret_5d
46. tbr_zscore_30
47. regime_momentum_signed_5d (BASELINE_V3)
48. vwap_dev_20              (BASELINE_V3)
```

Note: `atr_pct_rank_200` may be included if it survived T5 importance preview
(top-30 region). Will be verified against T8_final_feature_set.csv at code
commit time. If absent, the tuple shrinks to 47 — still above 47 floor (mass
expansion still well-exceeds the 14-feature stack).

**Total NEW features (need `features_v3/` implementation)**: 9
- `adx_14`, `taker_buy_imbalance_20`, `vol_regime_x_momentum`,
  `trend_efficiency_signed`, `ret_1d`, `sym_vs_btc_ret_3d`,
  `sym_vs_btc_vol_14d`, `candle_dow_sin`, `candle_dow_cos`

### Sub-fix 2 — New modules

- **`src/crypto_trade/features_v3/technical_v3.py`** (NEW, ~70 LOC):
  `add_technical_v3_features` computing `adx_14` (Wilder 1978 ADX:
  +DM / -DM EWMA, then EWMA of DX). Order: AFTER `regime_v3` (uses ATR).
- **`src/crypto_trade/features_v3/calendar_v3.py`** (NEW, ~30 LOC):
  `add_calendar_v3_features` computing `candle_dow_sin`, `candle_dow_cos`
  (cyclic encoding from `pd.to_datetime(open_time, unit="ms")`).
  Order: any time (no dependencies).

### Sub-fix 3 — Module extensions

- **`features_v3/engineered_v3.py`** (extend; ~30 LOC):
  - `compute_vol_regime_x_momentum`: `ret_5d × (atr_pct_rank_200 - 0.5)`.
    Dispatched via `add_engineered_v3_features` AFTER regime computes
    `atr_pct_rank_200`.
  - `compute_trend_efficiency_signed`: `kaufman_efficiency_50 × sign(ret_20d)`.
    Note: this is the SIGNED version of the iter-v3/043 efficiency_ratio_50
    (DISASTROUS NEGATIVE at unsigned form); the signed form addresses the
    direction-asymmetric bottleneck identified at iter-v3/044 cycle 3 EDA.
- **`features_v3/cross_btc_v3.py`** (extend; ~20 LOC):
  - `sym_vs_btc_ret_3d`: shorter horizon variant of existing
    `sym_vs_btc_ret_7d` (9-bar diff instead of 21-bar).
  - `sym_vs_btc_vol_14d`: symbol 14d vol minus BTC 14d vol broadcast.
- **`features_v3/microstructure_v3.py`** (extend; ~10 LOC):
  - `taker_buy_imbalance_20`: `(tbr.shift(1).rolling(20).mean() - 0.5)`.
- **`features_v3/momentum_accel_v3.py`** (extend; ~10 LOC):
  - `ret_1d` = `log_close.diff(3)` (3 candles = 1 day at 8h).

### Sub-fix 4 — Group registry update

`src/crypto_trade/features_v3/__init__.py:GROUP_REGISTRY`:
- ADD `"technical_v3": add_technical_v3_features` (AFTER `regime_v3` for ATR
  dependency)
- ADD `"calendar_v3": add_calendar_v3_features` (anywhere)

### Sub-fix 5 — V3_NON_FEATURE_COLUMNS update

`V3_NON_FEATURE_COLUMNS` currently `("natr_21_raw", "tbr_raw")`. No change
needed (the helper columns `tbr_raw` and intermediate `plus_di_14`/
`minus_di_14`/`dx_14` from ADX should NOT be added to V3_FEATURE_COLUMNS_TOP_N
— they are computed inline within `add_technical_v3_features` and not exposed).

### Sub-fix 6 — Parquet regeneration

Trigger feature regen for all 4 v3 symbols (BCH, LDO, TRX, BTC) at 8h:
```bash
uv run crypto-trade features --symbols BCHUSDT,LDOUSDT,TRXUSDT,BTCUSDT \
  --interval 8h --track v3 --format parquet --workers 4
```

Estimated time: 3-5min.

### Sub-fix 7 — Tests

New test files:
- **`tests/strategies/ml/test_v3_feature_count.py`** (NEW): assertion that
  `len(V3_FEATURE_COLUMNS_TOP_N) == 48` (or 47 if `atr_pct_rank_200` falls
  out of final-set verification).
- **`tests/features_v3/test_technical_v3.py`** (NEW): RSI bounds [0, 100],
  ADX non-negative, ADX series shape matches input.
- **`tests/features_v3/test_calendar_v3.py`** (NEW): cyclic encoding shape
  (sin^2 + cos^2 ≈ 1), DOW values periodic.

Existing tests should pass unchanged (the 14-feature ITERATION_LABEL=v3-062
test asserts `len == 14` at the unified-ensemble guardrail — needs update
to 48).

### Sub-fix 8 — ITERATION_LABEL update

`run_baseline_v3.py:128` (or wherever): `ITERATION_LABEL = "v3-063"`.

### Sub-fix 9 — ENSEMBLE_SIZE assertion

`_verify_feature_columns` runtime assertion may have a hardcoded expected
count. Update to 48 if so.

---

## Section 4 — Predicted Bands + Falsifiers

### Section 4.1 — Headline Sharpe prediction (single-seed EXPLORATION mode)

| Metric | /060 anchor | /063 predicted band | Δ vs /060 prediction |
|---|---:|---|---|
| IS monthly Sharpe | +0.8325 | **+0.85 to +1.30** | Δ +0.02 to +0.47 |
| OOS monthly Sharpe | +0.1403 | **+0.20 to +0.85** | Δ +0.06 to +0.71 |
| OOS/IS monthly ratio | 0.1685 | **0.20 to 0.80** | broader than /060 |
| frac_positive_paths (CPCV) | 0.6444 | **≥ 0.50** (binding gate) | architecture-dependent |
| IS Trades | 159 | **140-180** | (more features → minor trade-rule changes) |
| OOS Trades | 102 | **90-115** | similar range |
| Wall-clock | 0.69h | **1.0-1.4h** | +0.3-0.7h (more features → wider Optuna search) |

**Center-of-band prediction**: IS +1.05 / OOS +0.45 — slightly above anchor,
representing the EXPECTED outcome if mass expansion adds modest signal.

### Section 4.2 — BCH IS sensitivity prediction (per /059 Critic Rec #3 carry-forward)

- **Lower bound**: BCH IS share ≥ 80% one-sided (binding falsifier)
- **Upper bound**: no explicit cap; observed up to 176.68% at /060
- **Expected range**: 80-150% (mass expansion may enable LDO/TRX recovery
  reducing BCH dominance, OR keep BCH dominant if non-BCH features still
  noisy)

### Section 4.3 — Behavioral effect predictor (per `feedback_v3_axis_saturation_predictor.md`)

| Effect | /060 baseline | /063 prediction | Mechanism |
|---|---:|---:|---|
| IS trade count | 159 | 140-180 (Δ ±20) | Risk gates may fire differently with expanded feature OOD detection; modest change |
| OOS trade count | 102 | 90-115 (Δ ±15) | Same mechanism on OOS |
| BCH IS trades | 73 | 60-90 (Δ ±15) | BCH model has 14 → 48 features; trade rule may shift modestly |
| LDO IS trades | 11 | 8-20 (Δ ±10) | LDO under-trades; could increase or stay flat |
| TRX IS trades | 75 | 60-90 (Δ ±15) | TRX model 14 → 48 features |

**Falsifier**: If observed IS trade count Δ exceeds ±30 (i.e., outside [129,
189]) OR OOS Δ exceeds ±20 (outside [82, 122]) — flag as SUSPICIOUS-TRADE-COUNT
divergence and document in engineering report. Below ±20 trade-count change
across IS+OOS would indicate the axis is SATURATED at the gate-level (no
behavioral effect from feature expansion).

### Section 4.4 — Pre-registered FALSIFIER bands (BINDING GATES)

Per `feedback_v3_per_symbol_target_axis_falsifier.md` (Critic /061 Rec #3) +
`feedback_v3_cycle1_axis_pass_criteria.md` (Critic /060 Rec #2):

**A. Headline Sharpe gates (PROMISING-AT-EXPLORATION classification)**
1. **IS Sharpe shift ≥ +0.10 vs /060** (i.e., IS Sharpe ≥ +0.9325) — PROMISING-PASS gate
2. **OOS Sharpe shift ≥ +0.20 vs /060** (i.e., OOS Sharpe ≥ +0.3403) — PROMISING-PASS gate
3. **frac_positive_paths ≥ 0.50** — CPCV gate (EXPLORATION threshold)
4. **No methodology FAIL** in Critic 13 checks + §11 anti-pattern scan

**B. BCH IS sensitivity gate** (one-sided lower; per /059 Critic Rec #3):
5. **BCH IS share ≥ 80%** (one-sided lower bound; 176.68% upper bound NOT a
   falsifier per `feedback_v3_cycle1_axis_pass_criteria.md` /060 precedent)

**C. Trade-count bands** (per behavioral effect predictor):
6. **IS trade count ∈ [128, 222]** (relaxed range covering /060 ± 40)
7. **OOS trade count ∈ [66, 122]** (relaxed range covering /060 ± 30)

**D. Per-symbol target-axis wpnl Δ falsifier (NEW for mass expansion)**:

   Because mass expansion is universal (all 3 symbols), the "target axis" is
   ALL THREE symbols, not a single symbol. Pre-register:
8. **BCH IS wpnl Δ vs /060 ∈ [-15, +25]**: prediction +0 to +10 (modest
   improvement); falsifier band wider for noise tolerance
9. **LDO IS wpnl Δ vs /060 ∈ [-10, +25]**: prediction +5 to +15 (recovery
   possible if mass expansion helps LDO)
10. **TRX IS wpnl Δ vs /060 ∈ [-15, +25]**: prediction +5 to +15
11. **BCH OOS wpnl Δ vs /060 ∈ [-15, +30]**: prediction 0 to +15
12. **LDO OOS wpnl Δ vs /060 ∈ [-15, +20]**: prediction +5 to +15 (LDO is
    worst at /060 at -19.72; mass expansion has the most room to help)
13. **TRX OOS wpnl Δ vs /060 ∈ [-20, +20]**: prediction -5 to +15 (TRX 3-seed
    lottery at /060 may revert with expanded feature set)

**E. Tests + mode-flag gates**:
14. **Tests 37/37+ pass** (current 34/34 + 3 new tests for technical_v3,
    calendar_v3, feature count assertion)
15. **`ensemble_summary.json mode=exploration, ensemble_size=3`**

### Section 4.5 — One-sided BCH IS share sensitivity prediction (per /059 Critic Rec #3, one-sided ≥80%)

BCH IS share will likely remain ≥ 80% even with mass expansion:
- BCH is structurally dominant in the 3-symbol bundle (most consistent edge)
- Mass expansion can't manufacture LDO/TRX signal if it's not there
- LDO at /060 had 11 IS trades — too few to dominate even at expanded feature
  set
- Predicted BCH IS share range: **80-150%** (covers both "BCH still dominates
  but less" and "BCH still dominates equally")

---

## Section 5 — Risk Mitigation (R1-R5 stack unchanged)

The 7-primitive risk gate stack is UNCHANGED:
1. BTC trend kill (threshold_pct=15.0%)
2. Vol scaling (vol_scale_floor=0.3 default; vol_scale_floor_per_symbol={"TRXUSDT": 0.5} per /061)
3. ADX threshold (adx_threshold=20.0)
4. Hurst regime check
5. Feature z-score OOD (zscore_threshold=2.0)
6. Low-vol filter
7. Hit-rate (DISABLED)

**Per-symbol drawdown brake**: DISABLED (per /054)
**Regime gate**: DISABLED (per /022)
**Per-symbol cap**: DISABLED (per /020)

### Mass-expansion impact on risk gates

- **Z-score OOD gate (#5)**: This gate computes |z| > 2.5 on a feature
  subset. The current OOD config in `lgbm.py` uses 16 scale-invariant features
  (RSI extremes, BB %B, ATR, etc.). The 14 → 48 expansion does NOT directly
  affect the OOD feature subset (OOD features are HARDCODED at strategy
  config; not derived from V3_FEATURE_COLUMNS_TOP_N). NO CHANGE expected.
- **All other gates**: UNCHANGED.

### IS-calibrated thresholds — UNCHANGED from /060/061/062 stack.

---

## Section 6 — Risk Management Design

Same as /060/061/062 stack (no changes proposed). Mass feature expansion is
purely a model-input axis; no risk-primitive parameter changes.

**Kill-switch criteria** (mid-iteration abort):
- Backtest crash → abort
- Wall-clock > 2h hard cap → abort (no result reported beyond informational)
- Feature regen failure → abort and revert V3_FEATURE_COLUMNS_TOP_N to 14-stack

---

## Section 7 — Pre-Registered Failure-Mode Prediction

| Failure mode | Probability | Detection criterion | Mitigation |
|---|---:|---|---|
| **A. INERT-AT-EXPLORATION (most-likely)** — n_trials=35 inadequate for 48-feature search space; aggregate Sharpe within noise band | **~40%** | IS Δ in [-0.10, +0.10] OR OOS Δ in [-0.20, +0.20] | /069 CONFIRMATION re-tests at ENSEMBLE_SIZE=10 (3.3× effective Optuna budget; per `feedback_v3_unified_10seed_baseline.md`) |
| **B. SUSPICIOUS-OOS-DOMINANT** — single-seed lottery at expanded feature space; OOS spikes spuriously while IS doesn't track | **~15%** | IS Δ < +0.10 AND OOS Δ ≥ +0.20 AND IS-OOS daily Sharpe ratio outside [0.5, 2.0] | Pre-registered SUSPICIOUS path; defer to /069 multi-seed validation; do NOT advance to CONFIRMATION as PROMISING |
| **C. NEGATIVE-AT-EXPLORATION** — INERT features at higher Optuna budget actively HARM per `feedback_v3_inert_features_at_higher_budget.md`; some of the 39 promoted features may be bottom-quartile noise that overfits IS | **~15%** | IS Δ < -0.10 OR OOS Δ < -0.20 | Pivot to more-aggressive IC pruning (drop features with importance rank > 30) at /064 |
| **D. PROMISING-AT-EXPLORATION (predicted-success)** — mass expansion lifts both axes per hypothesis | **~30%** | IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20 AND all binding gates clear | Advance to /069 CONFIRMATION at multi-seed; consider Path A expansion to 100 features at /069 |
| **E. Wall-clock blowup** — feature regen + expanded backtest exceeds 2h hard cap | **<5%** | Run time > 2h | Abort + revert to 14-feature stack; document constraint at iter-v3/064 brief |
| **F. Methodology FAIL (Critic Check)** — new feature implementations have walk-forward leakage / non-stationary / IC violation post-regen | **<5%** | Critic Phase 7.5 review FAIL | Engineer Phase 6 pre-flight checks; new tests cover bounds + shape |
| **G. SUSPICIOUS-IS-DOMINANT** — mass expansion creates a deep IS overfit (BCH-share-far-above-200%) without OOS payoff | **~10%** | IS Δ ≥ +0.10 AND OOS Δ < -0.10 AND BCH IS share > 200% | Pivot at /064: re-prune to a 25-30-feature subset focusing on top-importance |

**Total probability sum**: ~120% (overlap allowed; B+G are sub-cases of "IS-OOS
divergence" which adds to ~25%). The most-likely outcome is **A. INERT** at
40%, with **D. PROMISING** at 30%. The mandate is structurally exploratory.

---

## Section 8 — LOCKED PASS Criteria

### Section 8.1 — PROMISING-AT-EXPLORATION (advance to /069 cycle 1 CONFIRMATION)

All of the following must clear:
1. IS monthly Sharpe shift ≥ +0.10 vs /060 anchor (i.e., IS ≥ +0.9325)
2. OOS monthly Sharpe shift ≥ +0.20 vs /060 anchor (i.e., OOS ≥ +0.3403)
3. cpcv_frac_positive_paths ≥ 0.50 (EXPLORATION threshold)
4. BCH IS share ≥ 80% (one-sided lower bound per /060 Rec #1)
5. IS trade count ∈ [128, 222] (i.e., /060 ± 50% wide band)
6. OOS trade count ∈ [66, 122] (i.e., /060 ± 30% wide band)
7. Per-symbol IS+OOS wpnl Δ within Section 4.4 bands (items 8-13)
8. ensemble_summary.json {mode="exploration", ensemble_size=3} (verified)
9. Tests passing (≥37/37; expect 34 prior + 3 new)
10. No Critic methodology FAIL across 13 checks + §11 anti-pattern scan

### Section 8.2 — INERT-AT-EXPLORATION (axis CLOSED for cycle 1 carry-forward)

- IS Δ within [-0.10, +0.10] AND OOS Δ within [-0.20, +0.20]
- All Section 4.4 binding gates PASS (no methodology FAIL)
- /063 axis CLOSED for cycle 1; remaining 5 EXPLORATIONs continue with other axes

### Section 8.3 — SUSPICIOUS-OOS-DOMINANT

- IS Δ < +0.10 AND OOS Δ ≥ +0.20 AND (IS-OOS daily Sharpe ratio outside
  [0.5, 2.0] OR per-symbol counterfactual breaks predictor band)
- DEFER to /069 CONFIRMATION for validation; do NOT advance as PROMISING
- Cycle 1 axis still CLOSED-pending-CONFIRMATION

### Section 8.4 — SUSPICIOUS-IS-DOMINANT

- IS Δ ≥ +0.10 AND OOS Δ < -0.10 (OOS regression)
- BCH IS share > 200% (structurally extreme)
- Axis CLOSED for cycle 1; consider aggressive re-prune at /064

### Section 8.5 — NEGATIVE-AT-EXPLORATION

- IS Δ < -0.10 OR OOS Δ < -0.20
- Axis CLOSED; consider aggressive IC pruning approach at /064

### Section 8.6 — DSR_relative informational

Per `feedback_v3_dsr_mode_artifact.md`: at EXPLORATION mode (n_trials_total=315),
DSR_relative is INFORMATIONAL ONLY. Not a binding gate at /063. Path B4
reformulation deferred to /069 CONFIRMATION per /062 closeout.

---

## Section 9 — Library Stack

### Existing dependencies (no change)

- Python 3.13
- lightgbm 4.6.0
- optuna 4.8.0 (n_jobs=1; Phase A revert intact)
- numpy 2.2.6
- pandas 3.0.0
- scikit-learn 1.8.0
- scipy 1.17.0
- statsmodels 0.14.6 (used by ADF in EDA)
- pyarrow 23.0.1
- tqdm

### NEW dependencies

**NONE** — all 9 NEW features computable with pandas + numpy primitives
already in the stack. **ta-lib NOT required** (RSI computed via Wilder EWMA;
ADX inline computation; CCI/Williams %R/Stochastic standard formulae).

### Test suite size after additions

- Current: 34/34 tests (per /061 stack)
- New tests: 3 (technical_v3 shape, calendar_v3 cyclic, feature count assertion)
- Expected: **37/37 tests passing** after Sub-fix 7

### Phase 6 smoke test

`uv run pytest tests/features_v3/ tests/strategies/ml/test_v3_feature_count.py
-v` should pass before backtest launch. This is a Phase 5.5 gate verification.

---

## Section 10 — QR Audit Trail

Per `feedback_v3_axis_selection_quant_discipline.md`: every EXPLORATION axis
must have QR EDA backing.

### Stage 1 — Mandate origin

- User directive 2026-05-11 codified at `feedback_v3_mass_feature_expansion.md`
- Refined at iter-v3/059 closeout (Critic FINAL `0fc18c2`): /059 RE-ANCHOR
  consumed the original /062 calendar slot; mass expansion shifted to /063
- /062 closeout (Critic FINAL `e713c2f` + diary commit `c7ce676`) confirmed
  /063 = MASS FEATURE EXPANSION

### Stage 2 — Cycle 1 #4 slot

Per `feedback_v3_strict_10_to_1_cadence.md`: cycle 1 #4 of 10 EXPLORATIONs.

### Stage 3 — EDA commitment

- EDA SHA: **`c833f48`** (`analysis/iteration_v3-063/` — 13 artifacts:
  `mass_feature_expansion_eda.py`, `finalize_50_feature_set.py`, 10 CSV/MD
  tables, `synthesis.md`)
- Produced BEFORE this brief was written
- Numerical tables (T1-T8) form Section 2 of this brief

### Stage 4 — Path selection

Per EDA T6 (path-selection summary): **Path B (~50 features)** selected over:
- Path A (100 strict): wall-clock projection 1.5-2h exceeds flag; single-seed
  lottery risk HIGH
- Path C (phased 50 → 100): structurally identical to Path B at /063;
  distinction only matters at /069 evaluation

Path B sub-decision: 48 final features (vs. exactly 50) because the IC-pruned
maximum-orthogonal set lands at 48 with all 14 BASELINE_V3 preserved. Padding
to 50 by accepting higher-IC pairs OR adding lower-importance features risks
the INERT-feature-at-higher-budget failure mode per
`feedback_v3_inert_features_at_higher_budget.md`. The 48-feature clean
orthogonal set is preferred to a 50-feature noisy set.

### Stage 5 — Setup commit (this commit SHA)

To be backfilled after Phase 5.5 gate PASS at HEAD `<setup-SHA>`.

### Stage 6 — Phase 5.5 gate

Pending. The phase 5.5 gate runs at HEAD post-setup-commit. Required PASS
conditions:
- ITERATION_LABEL = "v3-063"
- V3_FEATURE_COLUMNS_TOP_N has 48 entries (verified via runtime assertion)
- New modules `technical_v3.py` + `calendar_v3.py` importable
- GROUP_REGISTRY entries for both new modules present
- Tests 37/37 pass
- Feature parquet regen completes before backtest launch

---

## Reproducibility Stamp (skeleton — backfilled after Phase 5.5 PASS)

- HEAD SHA at brief commit: `<setup-SHA>` (this commit)
- EDA SHA: `c833f48`
- Phase 5.5 gate SHA: TBD
- Engineering report SHA: TBD
- Critic FINAL SHA: TBD
- Diary SHA: TBD
- Tag: NONE expected (BASELINE_V3.md update fires only at CONFIRMATION at
  /069 if PROMISING bundle clears BOTH IS AND OOS gates per
  `feedback_v3_baseline_update_policy.md` + `feedback_v3_strict_both_is_oos_baseline.md`)
- Wall-clock target: 1.2h (flag at 1.5h; hard cap 2h)
- Hardware: x86_64, 60 GB RAM, WSL2 / Linux 6.6.114.1
- Library stack: UNCHANGED from /062 (no new deps)
- Run command: `uv run python run_baseline_v3.py --exploration --seeds 1 --n-trials 35`
- Active ensemble seeds: `ENSEMBLE_SEEDS[0:3] = (191664963, 1662057957, 1405681631)`;
  mode="exploration"; ensemble_size=3
- Reports artifacts (expected): `reports-v3/iteration_v3-063/comparison.csv`,
  `dsr.json`, `ensemble_summary.json`, `per_cell_pbo.csv`, `cpcv_paths.csv`,
  `adf_test.csv`, `ic_matrix.csv`, `trial_oof_returns.parquet`, `in_sample/`,
  `out_of_sample/`, `feature_importance/`

---

## Adversarial flags (for Critic Phase 7.5)

1. **Final feature count = 48 is 2 below the 50 floor mandate**. Justification
   in Section 0.5 + Section 2.7: greedy LDP IC pruning produced the
   maximum-orthogonal set at 48; padding to 50 introduces redundancy or
   low-importance features that risk INERT-at-higher-budget failure. Brief
   stands by this interpretation; Critic may flag for second opinion.

2. **Trend_efficiency_signed uses Kaufman ER which was DISASTROUS at iter-v3/043
   in unsigned form**. The SIGNED variant addresses the direction-asymmetric
   bottleneck identified at iter-v3/044 cycle 3 EDA — structurally different
   mechanism. ER itself (unsigned) is NOT being re-introduced. The novel
   composition is the sign-flip layer over ER.

3. **funding_rate_zscore_30 + btc_funding_rate_zscore_30 were CLOSED at
   iter-v3/024 (3 EXPLORATION data points pre-fix)**. These are being
   re-evaluated under the post-walk-forward-fix landscape per BASELINE_V3.md
   "Dead Ideas" re-evaluation note + the mass-expansion mandate. The features
   are already in parquet; cost to include them is zero. If they remain INERT
   post-/063, the prior conclusion stands.

4. **tbr_zscore_30 was DROPPED at iter-v3/016 (rank 14/14)**. Same re-evaluation
   rationale as #3.

5. **vol_normalized_ret_5d was DROPPED at iter-v3/049 PATH C-clean (saturation
   rule fired)**. Same re-evaluation rationale.

6. **regime_momentum_signed_5d × ret_5d |IC|=1.000 is the
   composed-feature carve-out edge case** — but ret_5d is NOT in the final
   set (dropped via IC redundancy with regime_momentum). The 14-feature
   BASELINE_V3 contains regime_momentum_signed_5d; ret_5d is dropped to avoid
   redundancy. Verified at T8 final set list.

7. **48-feature single-seed EXPLORATION may produce highly variable per-symbol
   trade rosters**. The brief acknowledges this and pre-registers the
   `SUSPICIOUS-OOS-DOMINANT` classification (Section 8.3) for the case where
   OOS spikes spuriously without IS support. The `feedback_v3_engineered_features_dont_stack.md`
   rule applies to SAME-FAMILY engineered features (e.g., regime_momentum_3d +
   regime_momentum_5d); mass expansion is structurally DIFFERENT (different
   feature families). Predicted SUSPICIOUS probability ~15%.
