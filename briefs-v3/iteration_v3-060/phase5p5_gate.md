# Phase 5.5 Gate — iter-v3/060

OVERALL: PASS (after re-gate post fix `3fae219`)

## Re-Gate Resolution (2026-05-13)

Initial gate at SHA `b1df6b4` BLOCKED on a single item: ITERATION_LABEL not bumped from "v3-059" to "v3-060". Fix committed at SHA `3fae219`:
- run_baseline_v3.py line 128: `ITERATION_LABEL = "v3-059"` → `ITERATION_LABEL = "v3-060"`
- run_baseline_v3.py docstring header: updated to reference iter-v3/060 brief
- run_baseline_v3.py iteration-history docstring: NEW /060 entry added; /059 entry corrected to note n_jobs=2 REVERT at `31665f6` per Critic /059 Rec #4

Re-gate verification:
- `grep -n "v3-060" run_baseline_v3.py` returns line 128 ITERATION_LABEL value + docstring history entry. PASS.
- All other gate sections retained PASS verdicts from initial gate at `b1df6b4` (no other files changed between gates).

OVERALL=PASS. Phase 6 backtest authorized to launch with `--exploration` flag.

---

## Initial Gate (Historical Record) — OVERALL=BLOCK at `b1df6b4`

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24 UNCHANGED; EXPLORATION_ENSEMBLE_SIZE=3 and CONFIRMATION_ENSEMBLE_SIZE=10 declared; IS 2023-03-24 to 2025-03-23, OOS 2025-03-24 onward
- Section 0.5 (Iteration Type): PASS — TYPE=EXPLORATION-MODE-REFERENCE (cycle 1 #1); references SHA 56f5a30 for mode-flag refactor; explicitly states ENSEMBLE_SIZE=3 for --exploration; Optuna n_jobs=2 → n_jobs=1 revert at 31665f6 acknowledged; /059 CONFIRMATION-mode vs /060 EXPLORATION-mode anchor divergence stated
- Section 1 (Hypothesis): PASS — Single specific hypothesis: under EXPLORATION mode (ENSEMBLE_SIZE=3, ENSEMBLE_SEEDS[0:3]), /028 bundle produces 3-seed EXPLORATION-mode reference baseline; TRX diagnostic findings published; no code change beyond --exploration invocation; testable and specific
- Section 2 (IS-Only Evidence): PASS — Committed EDA at 6ab47b4 (analysis/iteration_v3-060/trx_diagnostic.py); Q1-Q7 tables present with numerical outputs; IS-only data used (OOS metrics only cited from comparison.csv, not from EDA queries); Section 2.10 EXPLORATION-mode reference scope present; synthesis table (Section 2.8) has numerical justification per path decision
- Section 3 (Proposed Changes): BLOCK — Brief Section 3 states "Edit 1: run_baseline_v3.py — ITERATION_LABEL only (already at SHA 2d82079)" but git show 2d82079 confirms that commit only added the research_brief.md file (578 insertions, 0 runner changes). Current runner line 128 reads ITERATION_LABEL = "v3-059". The ITERATION_LABEL has NOT been bumped to "v3-060". Phase 6 would write all reports to reports-v3/iteration_v3-059/ (the previous iteration's directory), corrupting prior results. This is a hard BLOCK.
- Section 4 (Expected OOS Impact): PASS — BANDS present (not point estimates): IS [+0.85, +1.15], OOS [+0.30, +0.85], OOS/IS [0.35, 0.75], trade count [90-110]; BCH OOS ±20%, LDO OOS [-3, -10], TRX OOS [-5, +15]; DSR_relative [0.05, 0.25]; cpcv_frac_positive_paths [0.50, 0.70]; 3-seed variance acknowledged; confidence intervals present; explicit falsifier in Section 4.4 (IS < +0.50 OR OOS < 0.0 OR BCH IS share < 80% OR IS trade count outside [128, 222] OR OOS trade count outside [66, 122]); BCH IS sensitivity projection per Critic Rec #3 in Section 4.2 ([85%, 100%] band, PATH-DIVERGENCE-AT-MODE-FLAG falsifier at <80%); behavioral effect predictor in Section 4.3 ([150, 200] IS, [80, 115] OOS)
- Section 5 (Risk Mitigation): PASS — Same 7-primitive gate stack as /059; Q7 RiskV2 anti-Kelly finding on TRX recorded as iter-v3/061 candidate axis; no /060 changes; per-symbol drawdown brake DISABLED; block_long_for=()
- Section 6 (Risk Management Design): PASS — 8-primitive table present with UNCHANGED status for all gates; thresholds unchanged; Q7 finding cross-referenced; vol-scaling iter-v3/061 candidate noted
- Section 7 (Failure-Mode Prediction): PASS — 3 failure modes pre-registered with probability estimates: 3-seed variance noise floor too high (~25%), BCH IS concentration shift unexpectedly (<5%), backtest runtime failure (<5%); predicted-success path (~65%) with PATH A EXPLORATION-mode-reference established; gates named for each failure mode
- Section 8 (MERGE/NO-MERGE Criteria): PASS — PASS criteria locked with explicit numerical thresholds (IS ≥ +0.50, OOS ≥ 0.0, BCH IS share [80%, 100%], frac_positive_paths ≥ 0.50, mode=="exploration" AND ensemble_size==3); NULL-RESULT-INFRASTRUCTURE criteria locked (IS < +0.50 OR OOS < 0.0 OR BCH IS share < 80%); FAIL methodology criteria locked (any Critic FAIL or Anti-Pattern A1-A13 hit); falsifier unambiguous; DSR_relative gate informational-only per feedback_v3_dsr_mode_artifact.md
- Section 9 (Library Stack): PASS — Full library stack declared (lightgbm 4.6.0, optuna 4.8.0 n_jobs=1, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1); mode-flag refactor at 56f5a30 noted; test suite size 31/31 stated
- Section 10 (QR Audit Trail): PASS — Stage 1-8 present; Stage 6 documents cycle counting; Stage 7 documents Critic Rec #4 wording cleanup; Stage 8 documents mid-setup mode-flag refactor user directive 2026-05-13; EDA SHA, setup SHA, backfill SHA, mode-flag SHA, brief revision SHA all recorded

## EXPLORATION-Mode-Specific Checks

- Section 0.5 references SHA 56f5a30 for mode-flag refactor: PASS
- Brief explicitly states --exploration flag: PASS (Section 0.5 run command + Section 2.8 Path decision)
- Brief explicitly states ENSEMBLE_SIZE=3: PASS (Section 0, Section 0.5, Section 3)
- Predicted impacts use BANDS not point-estimates: PASS (Section 4.1)
- Brief explicitly cites how /060 anchor differs from /059 anchor: PASS (Section 0.5, Section 2.10, Section 4.1 table showing /059 vs /060 columns)

## Code Consistency Checks

- EXPLORATION_ENSEMBLE_SIZE=3 constant: PASS — verified at run_baseline_v3.py line 92
- CONFIRMATION_ENSEMBLE_SIZE=10 constant: PASS — verified at run_baseline_v3.py line 90
- --exploration flag wired to runtime mode: PASS — verified at lines 1902, 1955, 2019-2022, 2086-2087, 2393-2394
- CLI help text correct: PASS — "EXPLORATION mode: uses ENSEMBLE_SIZE=3 (ENSEMBLE_SEEDS[0:3])"
- ensemble_summary.json mode + ensemble_size fields: PASS — lines 2393-2394
- _verify_feature_columns(ensemble_size=ensemble_size_for_run) called: PASS — line 1985
- Test TestExplorationConfirmationModeConstants: PASS — 20/20 tests in tests/strategies/ml/test_ensemble_unified.py

## ITERATION_LABEL Check (CRITICAL BLOCK)

- Runner current value (line 128): ITERATION_LABEL = "v3-059"
- Required value: ITERATION_LABEL = "v3-060"
- Setup commit 2d82079 diff: only added research_brief.md (578 insertions, 0 runner lines changed)
- Mode-flag commit 56f5a30 diff: did not update ITERATION_LABEL
- Brief revision commit 8430516 diff: only updated research_brief.md
- RESULT: ITERATION_LABEL has NOT been bumped to "v3-060"
- CONSEQUENCE: Phase 6 would write reports to reports-v3/iteration_v3-059/ (prior iteration directory), corrupting or overwriting /059 results

## Data Freshness (Pre-flight)

- BCHUSDT 8h: last close_time=1778687999999, stale=0.7h — PASS (< 16h)
- LDOUSDT 8h: last close_time=1778687999999, stale=0.7h — PASS (< 16h)
- TRXUSDT 8h: last close_time=1778687999999, stale=0.7h — PASS (< 16h)
- BTCUSDT 8h: last close_time=1778687999999, stale=1.7h — PASS (< 16h; BTC contagion gate)
- Re-fetch performed: uv run crypto-trade fetch --symbols BCHUSDT,LDOUSDT,TRXUSDT,BTCUSDT --intervals 8h (1 kline per symbol appended)

## Track Isolation Check

- `grep -rn "^from crypto_trade.features " src/crypto_trade/features_v3/`: CLEAN — no actual import violations (comment/docstring mentions only, confirmed by anchoring grep to line-start)

## Linter Check

- `uv run ruff check run_baseline_v3.py`: PASS — All checks passed

## Sacred Constants

- OOS_CUTOFF_DATE: "2025-03-24" — PASS (verified in runner)
- TRAINING_MONTHS: 24 — PASS (verified in runner)
- REQUIRED_GAP: 66 = (21+1) × 3 — PASS
- ENSEMBLE_SEEDS 10-tuple: (191664963, 1662057957, 1405681631, 942484272, 929893137, 33158374, 1465339467, 1273345680, 115579757, 1952249162) — PASS

## Feature Columns Check

- V3_FEATURE_COLUMNS_TOP_N count: 14 — PASS
- Contents match /028 spec: PASS (max_dd_window_50, ema_spread_atr_20, ret_kurt_50, ret_skew_200, range_realized_vol_50, hurst_diff_100_50, ret_kurt_200, hurst_100, btc_ret_14d, ret_skew_50, vwap_dev_20, ret_autocorr_lag1_50, sym_vs_btc_ret_7d, regime_momentum_signed_5d)
- regime_momentum_signed_5d PRESENT — PASS
- No unauthorized additions — PASS

## Reasons (BLOCK)

- **Section 3 (ITERATION_LABEL mismatch)**: Brief Section 3 claims "Edit 1: run_baseline_v3.py — ITERATION_LABEL only (already at SHA 2d82079)" but that SHA only added research_brief.md (no runner changes). Current runner line 128 reads `ITERATION_LABEL = "v3-059"`. Phase 6 must NOT launch until this is fixed. The fix is a one-line change: `ITERATION_LABEL = "v3-060"` in run_baseline_v3.py, committed as `fix(iter-v3/060): bump ITERATION_LABEL to v3-060`. QR must make this fix (or authorize QE to make it as a pure mechanical correction per Section 3 statement that it is "only" an ITERATION_LABEL bump — the fix itself is unambiguous).

## Required Fix Before Re-Gate

Change run_baseline_v3.py line 128 from:
  `ITERATION_LABEL = "v3-059"`
to:
  `ITERATION_LABEL = "v3-060"`

Commit as: `fix(iter-v3/060): bump ITERATION_LABEL to v3-060`

Then re-run Phase 5.5 gate. All other sections PASS; the re-gate should be a fast verification pass on this single fix.

## Summary

10/10 brief sections structurally PASS. One hard BLOCK: ITERATION_LABEL not bumped in runner. All other pre-flight checks (data freshness, track isolation, linter, sacred constants, feature columns, mode-flag wiring, test suite) PASS. Fix is one line; re-gate after fix expected OVERALL=PASS.
