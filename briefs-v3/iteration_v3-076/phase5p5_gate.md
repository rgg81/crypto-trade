# Phase 5.5 Gate — iter-v3/076

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24, IS/OOS windows named in absolute dates; start_time unchanged.
- Section 0.5 (Iteration Type): PASS — TYPE=EXPLORATION, cycle 2 #6 of 10, ENSEMBLE_SIZE=3 (--exploration), outer=42 lineage [191664963, 1662057957, 1405681631], n_trials=35, wall-clock budget ≤1.0h.
- Section 1 (Hypothesis): PASS — single testable sentence: adding `range_efficiency_50` (unsigned Kaufman path efficiency, SIGN-INVARIANT) lifts IS Sharpe by discriminating IS bear/chop drag WITHOUT loading the IS-up/OOS-down tension that structural /075 trap demonstrates.
- Section 2 (IS-Only Numerical Evidence): PASS — committed EDA SHA `40b6e66`; outputs T0-T7 + synthesis.md all IS-only or calendar-label; no OOS PnL / OOS Sharpe used; T2 AUC 0.657 (SHORT AUC 0.685); T3 |regime-sign corr| 0.010 (< 0.35 ceiling); T6 per-symbol BCH 0.697 / TRX 0.555; T4 holding-time-effect predictor (~0); T5 behavioral-effect predictor (5-60 IS trades); T7 max |IC| 0.206 (< 0.70); selection function `_pick_feature(t2,t3)` IS-only + calendar-label; EDA re-runs clean.
- Section 3 (Proposed Changes): PASS — exactly ONE primary axis (range_efficiency_50 as 15th feature) plus ONE mandatory revert (Primitive 12 OFF); single-axis discipline explicitly asserted; no same-family stacking; labeling/symbols/walk-forward harness unchanged.
- Section 4 (Expected OOS Impact): PASS — IS Δ band [0.00, +0.45] centred ~+0.15; OOS Δ band [-0.15, +0.20] centred ~0; frac_positive_paths ≈0.6444±0.05; IS falsifier at Δ<-0.10; OOS falsifier at Δ<-0.20; importance falsifier rank 15/15 all 3 symbols; holding-time falsifier >+1.0 candle; behavioral-effect falsifier bit-identical roster; OOS/IS ratio SUSPICIOUS gate >3.0 pre-registered (Section 4.5).
- Section 5 (Risk Mitigation): PASS — past-only discipline (50-bar rolling + shift(1)); IS-only + a-priori parameter selection (no OOS tuning per Section 10.1); output bounded [0,1]; max |IC| 0.206 (orthogonal); trade-rate preserved by construction; failure-stop falsifiers enumerated; new test file re-asserts past-only adversarially.
- Section 6 (Risk Management Design): PASS — 10-row primitive table; Primitive 12 explicitly REVERTED to OFF; Primitives 1-5 ON/unchanged at baseline fire-rate; Primitives 8/9/10/11 OFF with audit trail; regime coverage analysis notes discrimination moved INTO the model (not a post-gate classifier).
- Section 7 (Failure-Mode Prediction): PASS — INERT 40% / PROMISING 30% / NEGATIVE 22% / NULL-RESULT 5% / SUSPICIOUS 3% with mechanism reasoning; discriminating signals enumerated (Sharpe deltas, importance rank, roster diff, duration, OOS/IS ratio); process predictions P1-P3 stated.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — LOCKED disjunctive classifier in order SUSPICIOUS→NULL-RESULT→NEGATIVE→PROMISING→INERT; PROMISING requires all four conjuncts (IS Δ≥+0.10, OOS Δ≥+0.20, frac_pos≥0.50, no Critic FAIL); SUSPICIOUS defined with ratio gate >3.0 + sub-mode + holding-time violation; NULL-RESULT defined as bit-identical IS roster; INERT defined residually; all deltas anchored to /060 (IS +0.8325 / OOS +0.1403); no MERGE possible at EXPLORATION (correctly noted).
- Section 9 (Library Stack): PASS — numpy/pandas/lightgbm/optuna/scipy/statsmodels/pyarrow versions listed; mlfinlab/pypbo/fracdiff not invoked (feature is pure-numpy); walk-forward embargo unchanged; integration-test rationale given for feature axis.
- Section 10 (QR Audit Trail): PASS — 10.1 per-parameter disclosure (PARAMETER 1: `_pick_feature` IS-only AUC + calendar IS/OOS label, no OOS metric; PARAMETER 2: a-priori 50-bar window); grep for OOS metrics returns zero executable matches; 10.2 re-evaluation justification present and substantive (4 points: rule-sanctioned, different universe, different role, honest naming); 10.3 orchestrator framing + why-not-alternatives; 10.4 reproducibility stamp (EDA/brief/setup SHAs).

## Code-Readiness Verification

1. ITERATION_LABEL: `"v3-076"` — PASS (line 128, `run_baseline_v3.py`).
2. Primitive 12 revert in `_build_v3_model`: `enable_regime_size_scalar=False`, `regime_size_scalar_symbols=()` — PASS (lines 1655-1656).
3. V3_FEATURE_COLUMNS_TOP_N: 15 features including `range_efficiency_50` as 15th entry — PASS (`features_v3/__init__.py` line 190).
4. `add_engineered_v3_features` dispatches `compute_range_efficiency_50` — PASS (`engineered_v3.py` line 926); `"compute_range_efficiency_50"` in `__all__` (line 938).
5. `_verify_feature_columns` count assertion: `!= 15` — PASS (line 321); `range_efficiency_50 in V3_FEATURE_COLUMNS` assertion: PASS (lines 383-390); per-symbol count checks `!= 15` — PASS (lines 488-511); Primitive-12-revert assertion `enable_regime_size_scalar is False` + `regime_size_scalar_symbols == ()` — PASS (lines 616-634).
6. `efficiency_ratio_50` literal-name ban: INTACT — `if "efficiency_ratio_50" in V3_FEATURE_COLUMNS: raise RuntimeError(...)` (lines 344-353); comment updated to note `range_efficiency_50` is a separately-named re-evaluation that does NOT satisfy or violate the ban. The ban is NOT weakened.
7. Test files: `tests/strategies/ml/test_v3_feature_count.py` count assertion 15, `range_efficiency_50` in expected set, `efficiency_ratio_50` stays in prohibited set — PASS. `tests/features_v3/test_range_efficiency_50.py` present with 6 tests (unit range, past-only, warmup zero, clean-trend-high/chop-low, sign-invariant, dispatch integration) — PASS.
8. `uv run pytest tests/features_v3/ tests/strategies/ml/ -q`: **345 passed, 3 skipped** — PASS.
9. `uv run ruff check run_baseline_v3.py src/crypto_trade/features_v3/`: **All checks passed** — PASS.
10. EDA re-run `uv run python analysis/iteration_v3-076/axis_selection_eda.py`: clean execution, T0-T7 reproduced — PASS.

## efficiency_ratio_50 Ban Confirmation

The literal-name ban `efficiency_ratio_50 MUST NOT be present` is INTACT as a `raise RuntimeError` pre-flight assertion in `_verify_feature_columns` (lines 344-353) and as a prohibited entry in `test_v3_feature_count.py`. The new feature `range_efficiency_50` has a DISTINCT name and appears in neither the banned list in the runner nor the `_PROHIBITED_FEATURES` frozenset in the test. The ban comment has been updated (in the setup commit `79a62b0`) to explicitly note that `range_efficiency_50` is a separately-named re-evaluation and does NOT satisfy or violate the ban on `efficiency_ratio_50`.

## Adjacent Fix: test_pbo_in_range (commit 9285505)

Three stale tests in `tests/test_validation_v3.py` (`TestPBOFromCPCV::test_pbo_in_range`, `test_pbo_all_positive_is_low`, `test_pbo_single_path`) were comparing the `PBOResult` NamedTuple return of `pbo_from_cpcv` to floats — a `TypeError` caused by the API drift introduced at iter-v3/070. Fixed: tests now access `.pbo` (None for S=1 / 1-D input) and `.frac_positive_paths` correctly. All 27 tests in `test_validation_v3.py` pass. Committed separately as `fix(validation_v3): ...` (SHA `9285505`). This fix is NOT part of the /076 gate verdict.
