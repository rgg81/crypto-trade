# Phase 6.0 Critic Pre-Flight — iter-v1/030

OVERALL: PASS

## Pre-Flight Checks

### Check A — Brief look-ahead audit: PASS

Brief Sections 1-2 cite IS-only data per analysis/iteration_v1-030/*.csv (committed `9f77760`). Section 1.5 explicitly frames v3/017 as INFORMATIONAL prior (NEGATIVE PATH C precedent, not parameter source). Oracle EDA in Sections 1.1-1.4 references baseline IS trade roster for failure-mode prediction — STATELESS oracle veto carve-out applies per `feedback_v1_oracle_eda_trade_attribution.md` (M2 is post-Optuna trade-stream filter, not a feature-family substrate). LM Master `lgbm_advisor.md` priors derived from IS sample counts (cumulative M1-pos A=206, C=117, D=99, E=75) — no OOS leak into Phase 4.5 recommendations. M2 labels are derived ex-post inside training window only (`metalabeling.py:23-29` docstring + `_train_m2_for_month` uses `split.train_end_ms` boundary verified line 518). NO subtle look-ahead detected at brief level.

### Check B — Dispatch defect static scan (THE /024 + /027 LESSONS): PASS

The /030 elif at `run_baseline_v1.py:3280` is properly guarded: `iteration_label == "v1-030" AND set(symbols) == set(V1_BASELINE_UNIVERSE)`. Assertion at line 3294 re-confirms universe; line 3297 asserts `len(active_feature_columns) == 43`. F-AXIS #1 HARD-ASSERT at line 3408 (`sys.exit(2)`) uses real-instance attributes `t.open_time` against `OOS_CUTOFF_MS` — NOT `r.model_name` (the /027 defect avoided). F-AXIS #5 Model D LOAD-BEARING at line 3435 uses WARNING (file=sys.stderr) NOT crash — preserves /027 lesson explicitly. m2_passed annotation logic at line 3511-3535 uses `.apply(lambda row: ...)` with type coercion `int(row["open_time"])`; NaN handling explicit via `float("nan")`. M2 SKIP-rate per-cell logged via `M2_TRAINED=True/False` print statements in `metalabeling.py:654-677` (no crash on legitimate skip per Q8 item 5).

### Check C — M2 architecture correctness: PASS

3-separate M2 (Models A/C/D) confirmed: `run_meta_model` invoked at lines 3310 (A), 3330 (C), 3350 (D); `run_model` (plain LightGbm, NO M2) invoked at line 3372 for Model E (DOT). M2 feature vector = 45 cols verified: `include_m1_direction=True` hardcoded at `run_baseline_v1.py:642` inside `run_meta_model`; `MetaLabelingStrategy.__init__` lines 391-394 build `_m2_feature_cols = list(feature_columns) + ["m1_confidence", "m1_direction"]` → 43+1+1=45. No auto-discovery: `if not feature_columns: raise ValueError` at metalabeling.py:332. M2 hyperparameter bounds match LM Master §2 EXACTLY at lines 134-149: n_estimators [50,200], max_depth [2,4], num_leaves [7,31], learning_rate [0.02,0.10] log, min_child_samples [8,30], reg_alpha/reg_lambda [0.01,5] log, colsample_bytree [0.4,0.8]. `scale_pos_weight` EXPLICIT (line 146: `"scale_pos_weight": spw_explicit` with `spw_explicit = float(n_neg)/float(n_pos)` at line 122) — NOT `is_unbalance=True` for v1_030 profile. TimeSeriesSplit fold-skip at line 178: `if int((m2_labels[val_idx] == 1).sum()) < min_pos_per_fold: continue` (default 3) — LM Master §2 stratification fallback present.

### Check D — n_trials_m2 = 18 (per LM Master §2.3 mandate): PASS

`V1_ITER030_N_TRIALS_M2: int = 18` declared at `run_baseline_v1.py:326`. Passed explicitly as `n_trials_m2=V1_ITER030_N_TRIALS_M2` at lines 3318 (A), 3338 (C), 3358 (D). `MetaLabelingStrategy.__init__` accepts `n_trials_m2: int | None = None` (line 301) and stores as `self._n_trials_m2 = n_trials_m2 if n_trials_m2 is not None else n_trials` (line 347). Threaded into `_train_m2_binary` call at metalabeling.py:646. NOT the default 10 (v3/017 backwards-compat path) — explicitly 18.

### Check E — Test suite mandate (per /027 lesson): PASS

`tests/test_iteration_v1_030.py` exists with 13 test classes covering all mandated items:
- `TestIter030M2Dispatch` (3 tests; M2 dispatch architecture + E exclusion)
- `TestIter030M2FeatureVector` (4 tests; 45-col verification + m1_direction)
- `TestIter030M2LabelGeneration` (4 tests; ex-post derivation, in-training-window only)
- `TestIter030M2SampleSizeFloor` (3 tests; len<10 + degenerate label guards)
- `TestIter030M2HyperparameterBounds` (4 tests; LM Master §2 bounds + n_trials=18 constant)
- `TestIter030M2ThresholdPinned` (2 tests; 0.5 verbatim in metalabeling.get_signal)
- `TestIter030FAxis1RealInstance` (5 tests; REAL TradeResult.open_time/symbol/exit_reason)
- `TestIter030FAxis5ModelDTP` (4 tests; floor=3, real TP-exit roster, no-TP regression)
- `TestIter030M2Reproducibility` (2 tests; seeded determinism)
- `TestIter030M2PassedColumn` (2 tests; 1.0 for A/C/D, NaN for E)
- `TestIter030ScalePosWeight` (3 tests; explicit n_neg/n_pos + absence of is_unbalance in v1_030)
- `TestIter030FoldSkip` (3 tests; min_pos_per_fold=3 default + val_idx label-check)
- `TestIter030FoundationEmbargoRegression` (2 tests; walk_forward.py:113 + M2 train_end_ms reference)

Tests use `_make_trade()` helper that instantiates REAL `TradeResult` objects (line 33-53) — the /027 lesson hardened. F-AXIS #5 test at line 429 directly verifies the assertion path with real `TradeResult(exit_reason="take_profit", open_time, symbol)`. `tests/test_lookahead_embargo.py` 4 regression tests confirmed present at lines 120, 171, 248, 277 (all 4 expected names).

### Check F — Anti-pattern static scan: PASS

A1 `train_end_ms = test_start_ms` without subtraction — CLEAN. Single match at `walk_forward.py:113` carries `- embargo_ms` subtraction; line 22 in docstring states the invariant. A2 forward-window std (`returns[:].std()`) — ZERO matches in src/crypto_trade/strategies/ml. A3 `fit_transform(combined)` before split — ZERO matches in src/. A5 master-data-extent invariance — regression test name `test_labels_are_invariant_to_master_data_extent` confirmed at test_lookahead_embargo.py:120. M2 labels derived ex-post in training window only — verified `metalabeling.py:591-617` (label_trades called on `train_indices_kept` subset; M1's `m1_pred_classes` derived from `m1_proba_train` on train window). A13 read-before-write — m2_passed annotation reads `report_dir / sub_dir / "trades.csv"` (line 3518) AFTER `_post_dispatch_fi_strategies` ran (line 3547) which itself is after the backtest dispatch returned (line 3454). Order: dispatch → trades.csv write → m2_passed annotation → feature_importance. CLEAN. No silent fallbacks: M2 None returns explicit `print` with `M2_TRAINED=False month=...` per LM Master §9 Q8 item 6 mandate at metalabeling.py:654-658.

### Check G — Axis Family Validation: PASS

Brief Section 0.6 declares `meta-labeling` family explicitly at line 67. NEW NINTH family designation (UNUSED entire v1 history — verified against prior 5 EXPLORATIONs in catalog table: feature-family/2, per-cohort-specialization/2, model-arch/1). Brief Section 3.8 (lines 420-430) lists 5 negative carve-outs (NOT feature-family, NOT model-arch, NOT labeling, NOT per-cohort-specialization, NOT risk-primitive). Rotation status VALID by dual criteria (family novelty + prior-5-diversity). Phase 5.5 gate already confirmed at `04fef02`. Actual src/ change scope aligns: new `run_meta_model()` function (line 542) wraps `MetaLabelingStrategy` (M2); no M1 architecture changes; no V1_FEATURE_COLUMNS_PRUNED mutation; no risk gate changes.

### Check H — M2 wall-clock risk: PASS

Brief Section 3.6 uses 5-step label-rate scaling per `feedback_v1_label_rate_wall_clock_scaling.md`: step 1 (precedent /016 50min M1), step 2 (precedent M1 label count ~12/month), step 3 (/030 M1 BIT-IDENTICAL = same count), step 4 (scaling factor 1.0), step 5 (M2 overhead estimate 3-6 min). Total band 53-96 min modal 80 min — INSIDE LM Master §8 estimate of 65-95 min modal 80 min. 2h hard cap declared at brief line 398; kill-switch armed at >1.6h per /029 protocol mirror declared at brief line 413. NO CONFIRMATION-spec escalation hazard (ENSEMBLE_SIZE=3 + n_trials_m1=18 vs /029's failed CONFIRMATION-spec 10/35).

---

## PRE-FLIGHT AUTHORIZATION

Phase 6 backtest launch AUTHORIZED. Required launch invocation:

```bash
PYTHONUNBUFFERED=1 uv run python run_baseline_v1.py \
  --exploration \
  --iteration 30 \
  --n-trials 18 \
  --ensemble-size 3 \
  --bounds-profile v1_pruned \
  --feature-columns-pruned \
  > logs/v1_iter030.log 2>&1 &
```

Verify the runner emits these /030 startup lines:
- `[iter-v1/030] META-LABELING dispatch: 3 M2 classifiers (A/C/D), Model E EXCLUDED ... n_trials_m2=18, bounds_m2=v1_030, M2_threshold=0.5 PINNED, M2_expected_cells=159 (min_pass=80)`
- 4 `MODEL X [M2-META]` or `MODEL X` block headers in order (A BTC/ETH, C LINK+R1, D LTC+R1 → meta-labeled; E DOT+R1 → plain)
- At least 1 `[M2] M2_TRAINED=True month=...` line in run.log per (A, C, D) per month dispatched

Mandatory post-completion validation (orchestrator):
- F-AXIS #1: at least 80 of 159 expected `M2_TRAINED=True` lines in run.log (grep parse)
- F-AXIS #2: OOS total trades ≥ 90 (runner's HARD ASSERT at line 3408 enforces; sys.exit(2) on breach)
- F-AXIS #5: Model D OOS TP-exit count ≥ 3 (runner's WARNING at line 3435; verdict-capping in Phase 7)
- comparison.csv `m2_passed` column populated with 1.0 (A/C/D rows) and NaN (E rows)
- Wall-clock < 2h hard cap; abort at 1.6h kill-switch trigger

---

## Outstanding Informational Notes

1. **LM Master §3 STRONG recommendation (UNIFIED-M2) NOT ADOPTED**. QR adopts PARTIAL — drops Model E only. If /030 fires INERT or NEGATIVE, UNIFIED-M2 remains the deferred fallback per Section 3.4 §3 + Section 4 Path Forward. NOT a Phase 6.0 blocker (single-axis discipline justification documented at brief line 339-344).

2. **n_trials_m2=18 vs LM Master §2.3 ADOPTED VERBATIM**. The brief adopts but the LM advisor itself flagged MEDIUM-LOW directional confidence (track 3/9 = 33%). If the M2 modal NEGATIVE-OVER-FILTER 27% fires (per Section 0.5 QR-recalibrated priors), Phase 7.5 will record v3/017 mirror closure. Forward-looking; not a Phase 6.0 blocker.

3. **F-AXIS #4 n_eff_m2 informational only**. Per brief Section 2 F-AXIS #4 explicit "Informational, not blocking" — Phase 6.0 acknowledges this; n_eff_m2 will be parsed from run.log in Phase 7.4 attribution.

4. **M2 fire-rate parquet `data/v1_iter_v1-030_m2_fire_rate.parquet` NEW telemetry**. Brief Section 5 + Section 10.1 declare this as NEW per-cell telemetry but no test verifies it. NOT a Phase 6.0 blocker — informational forensic substrate; absence at Phase 7 would be Phase 7.4 attribution gap, not Phase 7 verdict cap.

5. **/030 modal verdict per QR priors (Section 0.5)**: NEGATIVE-OVER-FILTER 27%. Combined NEG tail 41% > combined PROMISING tail 35%. LM Master §1 priors converge. Phase 7.5 should expect modal NEGATIVE-OVER-FILTER outcome (v3/017 mirror). If PROMISING fires, treat as positive surprise per LM Master §6 honest uncertainty.

OVERALL=PASS. Phase 6 backtest launch AUTHORIZED.
