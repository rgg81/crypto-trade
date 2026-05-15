# Phase 5.5 Gate — iter-v3/070

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE = 2025-03-24 IMMUTABLE; training_months = 24 IMMUTABLE; ENSEMBLE_SIZE = 10 (CONFIRMATION); ENSEMBLE_SEEDS 10-tuple per BASELINE_V3.md
- Section 0.5 (Iteration Type): PASS — TYPE = CYCLE 1 CONFIRMATION (NOT EXPLORATION); mode = default (no --exploration); n_trials = 35 per cell; wall-clock target ~3.6h
- Section 1 (Hypothesis): PASS — ONE sentence; specific hypothesis naming bundle components (/065 SL widening + /062 Path B4); numerical gate ≥ +1.0894 IS AND ≥ +0.5791 OOS vs /059 anchor; dsr_relative_B4 ≥ 0.95 binding
- Section 2 (IS-Only Evidence): PASS — EDA SHA `fe219c1` committed; 5 tables (T0-T4) in analysis/iteration_v3-070/; T0 anchor-byte gate verified (Section 2.1 byte-exact vs /059 comparison.csv); Section 2.6 IC carve-out documented; Section 2.7 anchor declared (/059 unified 10-seed)
- Section 3 (Proposed Changes): PASS — Sub-fixes 1-12 enumerated; DEFAULT_ATR_MULTIPLIERS (2.0, 1.0) → (2.0, 1.5); Path B4 spec with code path + traceback (T3); NEW runtime assertion `_verify_timeout_consistency()`; REVERT V3_MODELS 4→3 sym; REQUIRED_GAP 88→66; ITERATION_LABEL bump; pre-flight assertion updates; existing test updates
- Section 4 (Expected OOS Impact): PASS — Sharpe bands per IS/OOS; falsifier table with 15 gates (A.1-E.15); behavioral predictor with per-symbol WR Δ bands; BCH IS share sensitivity analysis; anti-stacking check; ratio sanity check
- Section 5 (Risk Mitigation): PASS — Risk gate stack enumerated (carry-forward unchanged); orthogonality to bundle axis documented
- Section 6 (Risk Management Design): PASS — ATR labeling change documented (TP=2.0×, SL=1.5× for all 3 symbols); live trading translation; Path B4 methodology-only orthogonality documented
- Section 7 (Failure-Mode Prediction): PASS — 5-mode probability table (PASS 25%, INERT 35%, SUSPICIOUS-OOS-DOMINANT 15%, SUSPICIOUS-IS-DOMINANT 10%, NEGATIVE 15%); calibrated rationale for each mode; per-mode expected metric ranges
- Section 8 (MERGE/NO-MERGE Criteria): PASS — LOCKED numerical thresholds pre-registered; 8 path classifications (8.1-8.8); BOTH-must-improve discipline per `feedback_v3_strict_both_is_oos_baseline.md`; BASELINE_V3.md update policy at /070
- Section 9 (Library Stack): PASS — Library versions listed (Python 3.13, lightgbm 4.6.0, optuna 4.8.0, scipy 1.17.0 for Path B4 skew/kurtosis); integration test mandate documented; end-to-end smoke test spec; ANCHOR-BYTE GATE runtime assertion spec; reproducibility stamp
- Section 10 (QR Audit Trail): PASS — Cycle 1 closeout rationale; bundle composition rationale; Critic /069 Rec #1/#2/#3 addressed; cycle 1 → cycle 2 transition documented

## Implementation Verification (Setup commit `aab9347`)

### Sacred Constants
- OOS_CUTOFF_DATE = 2025-03-24: PASS (unchanged)
- training_months = 24: PASS (unchanged)
- ENSEMBLE_SIZE = 10: PASS (CONFIRMATION mode default)
- ENSEMBLE_SEEDS 10-tuple: PASS (unchanged from /059)

### Code Changes Verified
- ITERATION_LABEL = "v3-070": PASS (run_baseline_v3.py line 128)
- DEFAULT_ATR_MULTIPLIERS = (2.0, 1.5): PASS (features_v3/__init__.py line 222)
- V3_MODELS = 3 entries (BCH+LDO+TRX; NO ADA): PASS (run_baseline_v3.py lines 142-147)
- REQUIRED_GAP = 66 = (21+1)*3: PASS (validation_v3.py; reverts /069's 88)
- BacktestConfig.timeout_minutes = 10080: PASS (line 1407, unchanged)
- LightGbmStrategy.label_timeout_minutes = 10080: PASS (line 1455, unchanged)
- NEW `_verify_timeout_consistency()` runtime assertion: PASS (inserted between `_verify_label_leakage_gap` and `_verify_track_isolation`)
- Runtime assertion invoked in `_verify_feature_columns()` via `_verify_timeout_consistency(_p13_cfg_check, _p13_lgbm)`: PASS
- Path B4 implemented at run_baseline_v3.py (dsr_relative_b4 block after legacy dsr_relative): PASS
- `_write_dsr_json` extended with 4 new params (dsr_relative_b4, daily_sharpe_oos_b4_at_sqrt252, cpcv_q75_annualized_b4, n_daily_obs_oos): PASS
- dsr.json call updated to pass new B4 fields: PASS
- Pre-flight assertions updated: DEFAULT_ATR_MULTIPLIERS expects (2.0, 1.5); per-symbol assertion expects (2.0, 1.5); label-leakage gap expects 66: PASS
- REVERT /069 ADA-specific assertions: PASS (assertions replaced with 3-sym (2.0, 1.5) equivalents)

### Track Isolation
- grep -rP "^from crypto_trade\.features " src/crypto_trade/features_v3/: EMPTY — PASS

### Tests
- tests/features_v3/test_atr_multipliers_for_symbol.py: updated (2.0, 1.0) → (2.0, 1.5) throughout: PASS (7/7 ATR tests pass)
- tests/features_v3/test_features_for_symbol.py: test_all_symbols_atr_default_iter_v3_066 → test_all_symbols_atr_default_iter_v3_070 with (2.0, 1.5): PASS
- tests/features_v3/test_fracdiff_d05_universal.py: test_v3_models_at_iter_v3_069 → test_v3_models_at_iter_v3_070 (3-sym assertion): PASS
- tests/strategies/ml/test_dsr_relative_b4.py: NEW — 10 integration tests, all PASS
- Full test suite: 527 PASS + 3 pre-existing failures (test_validation_v3.py::TestPBOFromCPCV — pre-dating /070, caused by PBOResult.n_splits_evaluated field change; NOT related to /070 changes; last touch commit `1e431a5` = iter-v3/001)

### Linter
- `uv run ruff check` (modified files): ALL PASS
- `uv run ruff format` (modified files): 2 files reformatted, 4 unchanged

### Data Freshness
- BCHUSDT: close_time=2026-05-14 15:59 UTC, lag=8.1h — FRESH (< 16h threshold)
- LDOUSDT: close_time=2026-05-14 15:59 UTC, lag=8.1h — FRESH
- TRXUSDT: close_time=2026-05-14 15:59 UTC, lag=8.1h — FRESH
- BTCUSDT: close_time=2026-05-14 15:59 UTC, lag=8.1h — FRESH

### Mode-Flag Wiring
- No `--exploration` flag → ENSEMBLE_SIZE=10 CONFIRMATION mode: PASS
- ensemble_summary.json will emit mode="confirmation", ensemble_size=10: PASS (code verified)

### Section 2.1 T0 Anchor-Byte Gate
- monthly_sharpe_in_sample = +1.0894: verified vs /059 comparison.csv
- monthly_sharpe_out_of_sample = +0.5791: verified vs /059 comparison.csv
- Source file:line citations in brief Section 2.1 match actual /059 report values: PASS

### Section 3 Sub-fix Count
All 12 sub-fixes implemented:
1. DEFAULT_ATR_MULTIPLIERS = (2.0, 1.5): DONE
2. Path B4 implementation (dsr_relative_b4 block + _write_dsr_json extension): DONE
3. NEW test_dsr_relative_b4.py (10 integration tests): DONE
4. End-to-end smoke test spec in Section 9.3 (to be verified at Phase 6): DOCUMENTED
5. NEW `_verify_timeout_consistency()` runtime assertion: DONE
6. REVERT V3_MODELS to 3-sym + REQUIRED_GAP to 66: DONE
7. ITERATION_LABEL = "v3-070": DONE
8. Pre-flight assertion updates (DEFAULT expects (2.0, 1.5); per-symbol expects (2.0, 1.5); gap=66): DONE
9. Existing test updates (test_atr_multipliers_for_symbol.py, test_features_for_symbol.py, test_fracdiff_d05_universal.py): DONE
10. Parquet regeneration: NOT required (ATR multiplier change is label-time; no feature columns changed)
11. V3_FEATURE_COLUMNS: UNCHANGED (14 features per /059 anchor)
12. Run command = `uv run python run_baseline_v3.py --clean-oof`: VERIFIED

### Section 2.6 IC Violation Documentation
- vwap_dev_20 × regime_momentum_signed_5d IC = 0.7797 documented
- Category 2 composed-feature carve-out per `feedback_v3_engineered_feature_pivot.md` applied
- Importance evidence: vwap_dev_20 LDO importance 249.67 rank 1 (>30); regime_momentum_signed_5d 122.0 rank 12 (>30)
- NO feature change at /070: PASS

### Critic /069 Recommendations Addressed
- Rec #1 (anchor-byte correctness gate enforcement): Sub-fix 5 `_verify_timeout_consistency()` implemented: PASS
- Rec #2 (universe expansion follow-up at multi-seed): DEFERRED to cycle 2; /070 reverts to 3-sym: PASS
- Rec #3 (inherited IC violation address): Section 2.6 Category 2 carve-out documented: PASS

## Reasons

None. All 10 sections PASS. Implementation complete at commit `aab9347`.
