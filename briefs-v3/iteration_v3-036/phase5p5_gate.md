# Phase 5.5 Gate — iter-v3/036

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24 declared
  unchanged; IS window 2023-03-24 through 2025-03-23; OOS window 2025-03-24 onward; all
  sacred constants present and immutable.
- Section 1 (Hypothesis): PASS — Single specific sentence: vol_adj_autocorr applied
  selectively to TRXUSDT via V3_FEATURES_PER_SYMBOL["TRXUSDT"] provides TRX-specific
  persistence-normalized-by-volatility signal (obscured by cross-symbol noise in
  iter-v3/026 universal application) with feature importance ≥ 30 as confirmatory gate.
- Section 2 (IS-Only Evidence): PASS — Tables produced from committed report CSVs at
  `reports-v3/iteration_v3-026/comparison.csv` (universal failure evidence) and
  `reports-v3/iteration_v3-035/out_of_sample/per_symbol.csv` (anchor attribution).
  No new EDA script required: iter-v3/026 universal failure is archival evidence;
  iter-v3/035 per-symbol OOS provides TRX contribution baseline. Per-symbol
  architecture precedent documented (iter-v3/035 BCH-only fracdiff validated the
  methodology). Behavioral effect predictor present: ±5-15% TRX trade change; 0 delta
  for BCH/LDO/ALGO. Falsifier: 0 TRX IS trade change = feature INERT.
- Section 3 (Proposed Changes): PASS — 5 enumerated sub-fixes: (1) add TRXUSDT entry
  to V3_FEATURES_PER_SYMBOL, (2) re-add vol_adj_autocorr dispatch in engineered_v3.py,
  (3) update _verify_feature_columns in run_baseline_v3.py, (4) update ITERATION_LABEL,
  (5) update adversarial test suite. Each sub-fix is specific with file paths.
- Section 4 (Expected OOS Impact): PASS — IS band [-0.20, +0.20] median 0.0; OOS band
  [+2.40, +3.10] median +2.75 anchored to iter-v3/035 +2.8521. Explicit OOS falsifier
  stated (OOS Sharpe < +2.0 rejects hypothesis). 4-path taxonomy documented (PROMISING,
  PROMISING-INERT, NULL-RESULT, NEGATIVE).
- Section 5 (Risk Mitigation): PASS — R1/R2/R3 explicitly stated unchanged. Per-symbol
  feature heterogeneity risk addressed (BCH=15 fracdiff, TRX=15 vol_adj, LDO/ALGO=14).
  vol_adj_autocorr parquet-generation-for-all-symbols pattern documented as safe
  (same pattern as fracdiff_d05_close). BCH/TRX extension features stated as DISJOINT.
- Section 6 (Risk Management Design): PASS — 7-primitive gate table present with fire
  rates (IS/OOS columns inherited from iter-v3/035 baseline) and "None" change column
  for all 7 gates (BTC trend, hit rate, ADX, Hurst, drawdown brake, OOD, liquidity floor).
- Section 7 (Failure-Mode Prediction): PASS — Two failure modes pre-registered with
  specifics: (1) NULL-RESULT (vol_adj_autocorr INERT for TRX — universal failure was
  genuine, not contamination artifact); (2) PROMISING-INERT (importance 15-29 + OOS
  below anchor, consistent with Category 2 stacking constraint localized to TRX).
  Gates to watch specified (TRX IS wpnl collapse, TRX OOS concentration > 80%).
  Behavioral effect predictor explicitly included per `feedback_v3_axis_saturation_predictor.md`.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — EXPLORATION criteria locked before backtest.
  PROMISING: vol_adj_autocorr importance ≥ 30 AND TRX trade count changed AND BCH/LDO/ALGO
  unchanged AND OOS Sharpe ≥ +2.40. PROMISING-INERT: importance [5-29] with trade delta.
  NULL-RESULT: importance < 5 AND TRX trade count = 0. NEGATIVE: OOS < +2.0 OR IS
  regression > 0.20 OR contamination (BCH/LDO/ALGO ±5 trades) OR TRX OOS conc > 80%.
  All thresholds locked numerically before backtest — no post-hoc rationalization.
- Section 9 (Library Stack): PASS — vol_adj_autocorr uses only numpy (already available);
  fracdiff PyPI package unavailable (statsmodels conflict documented — not needed here);
  all library versions pinned (lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0,
  scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1); no new
  dependencies declared.

## One-Variable Check

Single-axis variation: TRXUSDT entry added to V3_FEATURES_PER_SYMBOL. V3_FEATURE_COLUMNS_TOP_N
(universal list) UNCHANGED at 14 features. BCHUSDT entry UNCHANGED. This is a single
parameter change (TRX feature set: 14 → 15 with vol_adj_autocorr). PASS — single-variable
discipline satisfied.

## Track Isolation Check

vol_adj_autocorr uses only `ret_autocorr_lag1_50` and `range_realized_vol_50` (both in-scope
v3 primitives already computed by tail_risk_v3 and momentum_accel_v3 groups). No imports from
`crypto_trade.features` (v1) or `crypto_trade.features_v2`. PASS.

## Sacred Constants Check

OOS_CUTOFF_DATE=2025-03-24 UNCHANGED. training_months=24 UNCHANGED. ENSEMBLE_SIZE=5 inner
seeds UNCHANGED (--exploration uses size=1 per standard EXPLORATION protocol). PASS.
