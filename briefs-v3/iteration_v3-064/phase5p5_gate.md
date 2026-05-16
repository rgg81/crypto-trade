# Phase 5.5 Gate — iter-v3/064

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE = 2025-03-24 IMMUTABLE confirmed. training_months = 24 IMMUTABLE confirmed. IS window = 2023-03-24 to 2025-03-24 (24 months walk-forward). OOS window = 2025-03-24 onward. Universe = BCHUSDT, LDOUSDT, TRXUSDT (UNCHANGED from /051 SYSTEM-LEVEL REVERT).
- Section 1 (Hypothesis): PASS — Single sentence. Specific prediction: ≥+0.10 IS Sharpe AND ≥+0.20 OOS Sharpe vs /060 anchor (IS +0.8325 / OOS +0.1403) primarily via stronger LDO trend-regime signal (adx_14 rank 2/15 at LDO in EDA singleton-importance preview).
- Section 2 (IS-Only Evidence): PASS — Committed script: `analysis/iteration_v3-064/adx_14_singleton_eda.py` at SHA `4a9f9c9`. Five numerical tables present (T1: ADF stationarity, T2: IC vs label, T3: IC vs 14-feature anchor, T4: singleton-importance preview, T5: predicted impact bands). All run on IS data only (open_time < OOS_CUTOFF_MS). No category-matching.
- Section 3 (Proposed Changes): PASS — Enumerated sub-fixes: V3_FEATURE_COLUMNS_TOP_N rewrite (46 → 15); run_baseline_v3.py assertion update; 7 test files updated. 15-feature list declared explicitly with each feature named. 31 REVERTED features listed. BANNED features list present.
- Section 4 (Expected OOS Impact): PASS — Predicted Sharpe delta bands present with anchor values. Falsifier thresholds declared (Gates A.1-E.16). Behavioral-effect predictor present per `feedback_v3_axis_saturation_predictor.md`. Per-symbol wpnl bands for all 3 symbols (Gates D.8-D.13).
- Section 5 (Risk Mitigation): PASS — Risk primitive table present. All 9 primitives listed with status (ENABLED/DISABLED). No risk-primitive changes at /064 (single-axis discipline confirmed).
- Section 6 (Risk Management Design): PASS — ATR multipliers, triple-barrier timeout, cooldown all declared. V3_ATR_MULTIPLIERS_PER_SYMBOL confirmed empty. All 3 symbols at DEFAULT (2.0, 1.0).
- Section 7 (Failure-Mode Prediction): PASS — Four failure modes pre-registered with probabilities (INERT 55%, PROMISING 20%, SUSPICIOUS-OOS-DOMINANT 10%, NEGATIVE 10%, Methodology FAIL <5%). Expected metrics per mode stated. Forward-looking rationale for INERT-most-likely explained.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — Section 8.1 PROMISING-AT-EXPLORATION gates fully enumerated (A.1-E.16). Sections 8.2-8.6 cover INERT, SUSPICIOUS, NEGATIVE, NEGATIVE-SUSPICIOUS, Methodology FAIL paths. Thresholds pre-registered vs /060 anchor before backtest.
- Section 9 (Library Stack): PASS — Python 3.13, LightGBM, pandas, pyarrow, statsmodels declared. adx_14 implementation referenced at `technical_v3.py:71-167`. No new modules required (zero code-change axis). ENSEMBLE_SEEDS[0:3] for EXPLORATION mode explicitly stated.

## Implementation Verification

### V3_FEATURE_COLUMNS_TOP_N (15 entries)

PASS — Implementation in `src/crypto_trade/features_v3/__init__.py` (lines 133-213) has exactly 15 entries:
1. max_dd_window_50
2. ema_spread_atr_20
3. ret_kurt_50
4. ret_skew_200
5. range_realized_vol_50
6. hurst_diff_100_50
7. ret_kurt_200
8. hurst_100
9. btc_ret_14d
10. ret_skew_50
11. vwap_dev_20
12. ret_autocorr_lag1_50
13. sym_vs_btc_ret_7d
14. regime_momentum_signed_5d
15. adx_14

BIT-IDENTICAL to brief Section 3 declared list (order-exact, symmetric_difference = empty set). EDA-implementation parity gate: PASS.

### run_baseline_v3.py assertions

PASS:
- Line 128: `ITERATION_LABEL = "v3-064"` CONFIRMED
- Line 318: `if n != 15` CONFIRMED (was != 46)
- Lines 469-475: `if len(sym_feats) != 15` CONFIRMED for BCH/LDO/TRX (was != 46)
- Lines 380-410: `if "adx_14" not in V3_FEATURE_COLUMNS` PRESENT; 8 /063-NEW REVERTED features absence-checked
- Per-symbol print log (line 498-504): "15-feature universal fallback" CONFIRMED
- Forbidden-list assertions: hurst_drift_50_200, vol_normalized_ret_5d, regime_momentum_signed_3d, efficiency_ratio_50 all still fire (CONFIRMED present at lines 567-620)

### Tests

PASS — 175 tests PASS, 3 SKIPPED (pre-existing parkinson_gk_ratio_20 tests correctly skipped for /064 architecture; unrelated to /064 changes).

Test files verified:
- `tests/features_v3/test_features_for_symbol.py` — 28 tests PASS (all asserting 15-feature state; adx_14 PRESENT; /063 NEW features REVERTED)
- `tests/features_v3/test_fracdiff_d05_universal.py` — 5 tests PASS (fracdiff_d05_close ABSENT; count == 15 confirmed)
- `tests/features_v3/test_hurst_drift_50_200_universal.py` — 5 tests PASS (hurst_drift_50_200 ABSENT; count == 15 confirmed; regime_momentum_signed_3d ABSENT confirmed)
- `tests/features_v3/test_regime_momentum_signed_3d_universal.py` — 5 tests PASS (3d ABSENT; fracdiff ABSENT; hurst_drift ABSENT; adx_14 PRESENT; count == 15)
- `tests/strategies/ml/test_v3_feature_count.py` — 6 tests PASS (count 15; 14 BASELINE_V3 present; adx_14 present; 8 /063-NEW reverted; prohibited absent; no duplicates)

### Pre-flight data freshness

PASS — All 4 symbols lag = 8.0h (within 16h threshold):
- BCHUSDT: 8.0h
- LDOUSDT: 8.0h
- TRXUSDT: 8.0h
- BTCUSDT: 8.0h

Incremental fetch ran (1 kline appended per symbol).

### Track isolation

PASS — grep on `src/crypto_trade/features_v3/` for "from crypto_trade.features " and "from crypto_trade.features_v2" returns only documentation comments (fracdiff_v3.py docstring, funding_v3.py docstring, __init__.py docstring). No actual imports from v1 or v2. CLEAN.

### Linter

PASS — `uv run ruff check run_baseline_v3.py src/crypto_trade/features_v3/` returns "All checks passed!"

### EDA-implementation parity (Critic /063 Rec #2)

PASS — V3_FEATURE_COLUMNS_TOP_N is BIT-IDENTICAL to brief Section 3 stated 15-feature list (set equality AND order equality confirmed via Python assertion). No silent additions. No substitutions. The 31 non-baseline features from /063 are all ABSENT.

### Parquet regeneration

NOT REQUIRED — adx_14 was implemented at /063 and is already present in all 3 symbol parquets at `data/features_v3/{BCHUSDT,LDOUSDT,TRXUSDT}_8h_features.parquet`. Confirmed by brief Section 3 Sub-fix 3 and EDA T1 (column present, non-NaN, stationary in IS).

## Reasons (BLOCK)

None. OVERALL=PASS.

## Summary

Branch: `iteration-v3/064`
HEAD SHA at gate: `35aa43e`
Test count: 175 PASS, 3 SKIP (pre-existing; unrelated)
Feature count: 15 (14 BASELINE_V3 + adx_14)
EDA-impl parity: BIT-IDENTICAL
Data freshness: 8.0h all symbols (PASS)
Linter: CLEAN
Track isolation: CLEAN
