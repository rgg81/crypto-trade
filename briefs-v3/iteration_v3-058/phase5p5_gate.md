# Phase 5.5 Gate — iter-v3/058

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24, outer_seeds=2, ENSEMBLE_SIZE=5, n_trials=35; IS/OOS windows stated in absolute dates; sacred constants UNCHANGED.
- Section 0.5 (Iteration Type Declaration): PASS — RE-ANCHOR special category declared; cycle 4 cadence RESET to ZERO; cycle 1 post-/058 structure defined; wall-clock 6h hard cap stated.
- Section 1 (Hypothesis): PASS — Single hypothesis: /028 BASELINE_V3.md bundle under post-fix walk-forward (commit `e149e9d`) produces unbiased Sharpe anchor for cycle 1+. Mechanism described (lookahead source, ~22-candle embargo). Not a new axis — INTEGRITY CORRECTION only.
- Section 2 (IS-Only Numerical Evidence): PASS with RE-ANCHOR EXEMPTION — No new EDA required per orchestrator directive. Section 2 cites BASELINE_V3.md /028 bundle spec directly + walk-forward fix memory rule + fix commit `e149e9d` (42/42 regression tests pass). Category: methodology correction, not signal discovery. Evidence standard satisfied for RE-ANCHOR type.
- Section 3 (Proposed Changes): PASS — Enumerated: (1) REVERT parkinson_gk_ratio_20 → ret_skew_50 in V3_FEATURE_COLUMNS_TOP_N; (2) ITERATION_LABEL "v3-058"; (3) _verify_feature_columns assertions flipped; (4) test_features_for_symbol.py reverted; (5) test_parkinson_gk_ratio_20_past_only.py Tests 3-5 skipped. Defensive §5 verifies unchanged architecture. No labeling/symbol/risk-gate changes.
- Section 4 (Expected OOS Impact): PASS — Prediction bands locked: IS [+0.35, +0.50], OOS [+0.30, +0.50]; 5 outcome paths pre-classified with probabilities; behavioral predictor: IS trade Δ -3% to -7% (170-185); falsifier: |IS trade Δ| > 30 fires diagnostic.
- Section 5 (Risk Mitigation): PASS — 7 risk mitigations stated; post-fix walk-forward validated by 11/11 regression tests; drawdown brake DISABLED unchanged; no universe/labeling/risk-gate change; --clean-oof guardrail active.
- Section 6 (Risk Management Design): PASS — 7-primitive gate stack inherited from /028 (BTC trend, vol scaling, ADX 20.0, Hurst regime, z-score OOD 2.0, low-vol, hit-rate disabled); all unchanged. RE-ANCHOR exemption applies (no NEW risk primitive; stack validation is carry-forward from /028).
- Section 7 (Failure-Mode Prediction): PASS — Three failure modes pre-registered: PATH RE-ANCHOR-MAJOR-DEFLATE/COLLAPSE (10-25% combined), PATH RE-ANCHOR-NORMAL (50-60%), PATH RE-ANCHOR-INVARIANT (5-10%); forward-looking and non-renegotiable.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — Mandatory BASELINE_V3.md update regardless of direction; 5 diary outcome tiers (clean/deflated/critical-concern/collapse/invariant) with locked numerical thresholds; critical gate = Pareto Gate 10 (both seeds OOS > 0); path adjudication locked pre-run.
- Section 9 (Library Stack): PASS — Python 3.13, lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1; no new deps.
- Section 10 (QR Audit Trail): PASS — 7-stage audit trail; orchestrator-mandated path documented; citation chain to BASELINE_V3.md + fix commits; cycle 4 cadence RESET statement; Critic protocol awareness (enhanced Boot Steps 9-11 + Check 13 + §11 catalog at SHA `414368a`).
- Section 11 (Catalog Row Pre-Commit): PASS — RE-ANCHOR catalog row template pre-committed; outcome classification non-renegotiable.
- Section 12 (Cycle Consequences): PASS — Three outcome scenarios documented (RE-ANCHOR-NORMAL, RE-ANCHOR-DEFLATE/COLLAPSE, RE-ANCHOR-INVARIANT) with cycle 1 implications.

## ONE-VARIABLE RULE

RE-ANCHOR is a REVERT (parkinson_gk_ratio_20 OUT → ret_skew_50 IN). This is a 1-for-1
restoration to the /028 BASELINE_V3.md composition. No new axis variation. Acceptable per
/055/056 REVERT precedent: reverts are restorations, not new axes. ONE-VARIABLE rule: PASS.

## Foundation Audit Pre-Check (Critic Boot Step 9)

**walk_forward.py fix verification:**
`grep -n "train_end_ms = test_start_ms - embargo_ms"` in
`src/crypto_trade/strategies/ml/walk_forward.py` → line 113 (CONFIRMED).
`compute_embargo_candles` helper at line 10 (CONFIRMED).
`generate_monthly_splits` requires `label_timeout_minutes` + `interval_minutes` params (CONFIRMED).

**lgbm.py fix verification:**
`compute_embargo_candles` imported and used for `cv_gap` (CONFIRMED from commit `e149e9d`).

**Regression coverage:**
`tests/test_lookahead_embargo.py` — 11 tests including:
  - test_basic / test_rounds_down / test_exact_multiple / test_invalid_inputs (TestEmbargoFormula)
  - test_train_end_precedes_test_start_by_embargo (TestTrainTestEmbargo)
  - test_labels_are_invariant_to_master_data_extent (canonical bug property — PASS)
  - test_demonstrates_bug_without_embargo (demonstrates pre-fix behavior — PASS)
  - test_cv_gap_uses_shared_formula_single_symbol / multi_symbol (TestCvGap)
  - test_time_series_split_with_gap_excludes_correct_rows (TestCvGap)
  - test_walk_forward_embargo_matches_cv_gap_formula (TestFormulaIsSharedAcrossBoundaries)
ALL 11/11 PASS at setup commit SHA `7a46e05`.

## Anti-Pattern A1 Grep (Critic Boot Step 11 pre-check)

Zero unexplained matches for `train_end_ms = test_start_ms` (without `- embargo_ms`) in
active `src/` code. The only occurrence of `train_end_ms =` in walk_forward.py is line 113:
`train_end_ms = test_start_ms - embargo_ms` (CORRECT — embargo applied).
No other `train_end_ms = test_start_ms` patterns found in `src/`. A1: CLEAN.

## Track Isolation Check

`grep -r "from crypto_trade.features " src/crypto_trade/features_v3/` → empty (PASS).
`grep -r "from crypto_trade.features_v2" src/crypto_trade/features_v3/` → empty except docstring
comments in fracdiff_v3.py and funding_v3.py (not import statements). Track isolation: PASS.

## Regression Test Confirmation

Total at setup commit `7a46e05`:
- tests/test_lookahead_embargo.py: **11/11 PASS**
- tests/features_v3/ (all): **83 passed, 3 skipped** (skipped = parkinson_gk_ratio_20 membership tests 3/4/5 — correct; compute tests 1/2 ACTIVE)
- tests/test_lgbm.py: **100 passed, 0 skipped**
- **TOTAL: 194 passed, 3 skipped, 0 failed**

## Parquet Regeneration Status

NOT REQUIRED. ret_skew_50 column already present in v3 feature parquets (computed since
/001-/006). parkinson_gk_ratio_20 column also present in parquets (compute function active
via add_price_efficient_vol_v3_features). No new feature group added; no regen needed.

## Setup Commit SHA

`7a46e05` — feat(iter-v3/058): REVERT /057 A4 SWAP (ret_skew_50 RESTORED, parkinson_gk_ratio_20 REVERTED) + RE-ANCHOR setup

## Spec Verification

Runner spec: `uv run python run_baseline_v3.py --seeds 2 --n-trials 35 --clean-oof`
- ENSEMBLE_SIZE=5 (hardcoded inner)
- outer_seeds=2 (42, 123)
- n_trials=35 (CONFIRMATION default per feedback_v3_confirmation_n_trials_35.md)
- --clean-oof (OOF parquet staleness guardrail)
- ITERATION_LABEL="v3-058" (verified in runner)
- V3_FEATURE_COLUMNS_TOP_N = 14 features matching /028 BASELINE_V3.md spec exactly
- V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT)
- REQUIRED_GAP = 66 = (21+1)×3
- OOS_CUTOFF_DATE = "2025-03-24" (IMMUTABLE)
- TRAINING_MONTHS = 24 (IMMUTABLE)

All PASS. Proceeding to Phase 6 backtest launch.
