# Phase 5.5 Gate — iter-v3/068

OVERALL: PASS

Implementation commit: `0e9eb30`
Branch: `iteration-v3/068`

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24 IMMUTABLE; training_months=24 IMMUTABLE; 3-symbol universe BCHUSDT/LDOUSDT/TRXUSDT UNCHANGED from /051 REVERT.
- Section 1 (Hypothesis): PASS — ONE sentence, specific mechanism (DURATION widening of label forward-scan window from 21→42 candles), measurable prediction (IS Δ [-0.10,+0.10] OOS Δ [-0.15,+0.15]), INERT-band centered hypothesis explicitly stated.
- Section 2 (IS-Only Evidence): PASS — EDA committed at `c16d53c` (`analysis/iteration_v3-068/labeling_timeout_eda.py`). T0-T6 tables produced from IS-only data (trades.csv, features parquets). T0 anchor values verified against source: BCH OOS +1.9078, LDO OOS -19.7208 (brief shows -19.7208; comparison.csv shows -19.7208 MATCH), TRX OOS +23.3119, OOS trades 102. NO category-matching; concrete numerical tables present.
- Section 3 (Proposed Changes): PASS — Three coupled call sites enumerated (BacktestConfig.timeout_minutes, common_kwargs.label_timeout_minutes, LightGbmStrategy.label_timeout_minutes all set to 20160); inference_threshold_floor REVERTED to 0.0; REQUIRED_GAP formula update documented; PER_CELL_GAP update documented. Single substantive axis.
- Section 4 (Expected OOS Impact): PASS — IS Δ band [-0.10,+0.10], OOS Δ band [-0.15,+0.15] with confidence intervals. Explicit falsifier: NEGATIVE if IS Δ < -0.20 OR OOS Δ < -0.30; PROMISING if IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20. Section 8 locked numerical thresholds pre-registered.
- Section 5 (Risk Mitigation): PASS — All 11 risk primitives enumerated with ENABLED/DISABLED status and source iteration. labeling_timeout_minutes change explicitly listed as only CHANGED row. Per-symbol vol_scale_floor {"TRXUSDT": 0.5} preserved (orthogonal axis).
- Section 6 (Risk Management Design): PASS — 8+ primitive table with fire-rate predictions (not applicable for TRAIN-TIME only axis; correctly noted as structural consequence). Embargo coupling disclosed as Section 2.7 T6 structural side effect. Cooldown/fee UNCHANGED documented.
- Section 7 (Failure-Mode Prediction): PASS — 4-mode probability table (INERT 50%, PROMISING 15%, SUSPICIOUS-OOS 10%, NEGATIVE 25%) with expected metrics per mode. Why each mode is likely reasoned from EDA findings (LDO insensitivity at T3, /066+/067 INERT precedent, Rule 3 calibration). NEGATIVE-EMBARGO-COUPLED sub-mode added (Path C specific).
- Section 8 (MERGE/NO-MERGE Criteria): PASS — Locked numerical gates at Section 8.1-8.6. PROMISING requires IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20 vs /060 anchor. INERT, SUSPICIOUS-OOS-DOMINANT, NEGATIVE, and NEGATIVE-EMBARGO-COUPLED criteria enumerated. Pre-registered before Phase 6.
- Section 9 (Library Stack): PASS — Python 3.13, LightGBM, pandas, pyarrow, statsmodels enumerated. No new libraries. ENSEMBLE_SEEDS[0:3] outer=42 lineage subset for EXPLORATION mode documented. Compute paths from label_timeout_minutes through walk_forward.compute_embargo_candles traced.

## Implementation Verification

### Sacred Constants
- OOS_CUTOFF_DATE = "2025-03-24": UNCHANGED (line 81)
- TRAINING_MONTHS = 24: UNCHANGED (line 82)
- 5 inner seeds per EXPLORATION mode (ENSEMBLE_SEEDS[0:3]): UNCHANGED

### Code Changes Verified
- ITERATION_LABEL: "v3-067" → "v3-068" (line 128)
- BacktestConfig.timeout_minutes: 10080 → 20160 (line 1380 area)
- LightGbmStrategy.label_timeout_minutes: 10080 → 20160 (line 1398 area)
- inference_threshold_floor=0.60 REMOVED from LightGbmStrategy call (revert /067)
- _verify_feature_columns: /067 assertion (floor=0.60) replaced with /068 assertion (floor=0.0 + label_timeout_minutes=20160)
- _verify_label_leakage_gap: timeout_minutes 10080→20160, timeout_candles 21→42
- PER_CELL_GAP: 22 → 43
- CPCV comment: (21+1)*3=66 → (42+1)*3=129

### REQUIRED_GAP Update
- validation_v3.py REQUIRED_GAP: `(21+1)*3 = 66` → `(42+1)*3 = 129`
- Formula correct: embargo_candles = 20160//480+1 = 43; cross-cell gap = 43*3 = 129
- _verify_label_leakage_gap() runtime assertion will catch any mismatch at run start

### T0 Anchor Values (verified against reports-v3/iteration_v3-060/comparison.csv)
- BCH OOS weighted_pnl: +1.9078 MATCH
- LDO OOS weighted_pnl: -19.7208 MATCH (brief shows -19.7208 = -19.7208 per comparison.csv col 5 row LDOUSDT)
- TRX OOS weighted_pnl: +23.3119 MATCH
- OOS trades: 102 MATCH
- IS monthly_sharpe: +0.8325 MATCH
- OOS monthly_sharpe: +0.1403 MATCH

### V3_FEATURE_COLUMNS_TOP_N Count
- Count: 14 (UNCHANGED; NON-FEATURE axis per Critic /064 Rec #4 mandate)
- inference_threshold_floor REVERTED to 0.0 (default; /067 INERT axis closed)

### Mode-Flag Wiring
- --exploration: ENSEMBLE_SIZE=3 (EXPLORATION_ENSEMBLE_SIZE) PASS
- --confirmation (default): ENSEMBLE_SIZE=10 (CONFIRMATION_ENSEMBLE_SIZE) PASS
- Mode assertion in _verify_feature_columns(ensemble_size=ensemble_size_for_run): PASS

### Data Freshness
- Staleness guard: _verify_data_freshness() checks all 3 v3 symbols + BTCUSDT for >16h lag (unchanged from /067)
- No stale data gate bypass introduced

### Track Isolation
- grep -rP "^from crypto_trade\.features " src/crypto_trade/features_v3/: EMPTY (PASS)
- grep -rP "^from crypto_trade\.features_v2" src/crypto_trade/features_v3/: EMPTY (PASS)

### Tests
- tests/strategies/ml/test_label_timeout_minutes.py: NEW (5 tests); all 5 PASS
  - test_label_timeout_minutes_default_preserved: PASS
  - test_label_timeout_minutes_iter068_value_20160: PASS
  - test_compute_embargo_candles_iter068_value_43: PASS
  - test_compute_embargo_candles_iter060_anchor_value_22: PASS
  - test_compute_embargo_candles_doubles_on_timeout_doubling: PASS
- tests/strategies/ml/test_cpcv_embargo_assert.py: UPDATED (TIMEOUT_CANDLES 21→42, N_SYMBOLS 4→3, CORRECT_GAP 88→129, REQUIRED_GAP==88 assertion → 129); all 7 PASS
- tests/strategies/ml/test_v3_feature_count.py: UPDATED (stale /064 count=15+adx_14 present assertions corrected to count=14+adx_14 absent per /065+ revert); all 6 PASS
- tests/strategies/ml/test_inference_threshold_floor.py: UNCHANGED; all 3 PASS (LightGbmStrategy mechanism intact; /068 simply passes default floor=0.0)
- tests/test_lookahead_embargo.py: UNCHANGED; all 10 PASS
- Total relevant: 32 tests PASS

### Lint + Format
- uv run ruff check [changed files]: ALL CHECKS PASSED
- uv run ruff format --check [changed files]: 5 FILES ALREADY FORMATTED

## Blocking Concerns
None.

## Parquet Regeneration Required
No. label_timeout_minutes operates at TRAIN-TIME label generation; no feature columns changed. Existing parquets at data/features_v3/ are valid for Phase 6.

## Phase 6 Clearance
Implementation commit `0e9eb30` on branch `iteration-v3/068`. Safe to launch backtest with `uv run python run_baseline_v3.py --exploration --n-trials 35 --skip-features`.
