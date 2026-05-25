# Phase 6.0 Critic Pre-Flight — iter-v1/011

OVERALL: PASS

## Pre-Flight Checks

### Check 1 (mini) — Brief Look-Ahead Audit: PASS

Brief Section 1 (Hypothesis) and Section 3.1/10.1 describe the R5-BINARY-KILL primitive as a STATELESS entry filter reading `vol_natr_14` from the per-symbol feature parquet, looked up by `(sym, ot)` where `ot` is the OPEN time of the candle being evaluated. `vol_natr_14` is a standard rolling-N NATR computation (pandas_ta-equivalent) over past closed candles — past-only by construction; verified as a load-bearing v1 baseline feature listed in `baseline_feature_columns.py:163` and `live/models.py:259`. Lookup at `backtest.py:431` retrieves the value INDEXED BY the same `open_time` row in the parquet — no forward-window scan, no off-by-one toward the future. Brief Section 0.4 ("R5-BINARY-KILL is purely deterministic given NATR_14 feature parquet") is structurally honest. No look-ahead found in the proposed axis.

### Check 13 (mini) — Anti-Pattern Static Scan: PASS

Scanned QE's src/ diff at `b788d4f` against the §11 catalog (A1-A13). Concrete results:

- **A1** (`train_end_ms = test_start_ms` w/o subtraction): zero matches in active code; only matches are the documented subtraction at `walk_forward.py:113` (`train_end_ms = test_start_ms - embargo_ms`) and analogous v3 cross-sectional code at `cross_sectional.py:974,1325,1345`. PASS.
- **A2** (labeling-window σ_t look-ahead): v1 labeling uses fixed-fraction triple-barrier (atr_tp/atr_sl + timeout); no σ_t computation. N/A — no risk surface for /011.
- **A3** (fit_transform on combined train+test): zero matches of `fit_transform|StandardScaler|MinMaxScaler|combined` in `backtest.py`. No scaler is touched by the /011 diff. PASS.
- **A7** (OOF parquet append-without-clearing): `run_baseline_v1.py:884` carries `OOF_PARQUET_PATH.unlink(missing_ok=True)` as the A7 guard before training. PASS.
- **A8** (stateful gate deadlock): R5-BINARY-KILL is STATELESS by design — no persistent fields, no state transitions, fires per-bar from data-deterministic NATR lookup. Brief Section 3.1, 6.1-6.4 documents the stateless property explicitly. No deadlock surface. PASS.
- **A9** (forming-candle in training): `fetcher.py:38` carries the `if k.close_time < now_ms` guard, unchanged by /011. PASS.
- **A10** (confidence threshold tuned on test): R5-BINARY-KILL is NOT an Optuna hyperparameter; threshold is a config float fixed at 2.0 before Optuna runs. PASS.
- **A12** (DSR/PSR wrong-granularity): /011 introduces NO methodology-axis fields to dsr.json/comparison.csv beyond the 2 new fire-rate rows that are simple proportions (no Sharpe input). N/A.
- **A13** (CPCV path read-before-write): /011 adds 2 fire-rate rows to comparison.csv (written by `append_r5_binary_kill_rows_to_comparison` at `reporting_v1.py:1325`). The function is called AFTER `append_r5_rows_to_comparison` (legacy /010 rows) and AFTER comparison.csv exists from prior reporting. Verified at `run_baseline_v1.py:648` — invocation site is after standard comparison flow. No read-before-write surface. PASS.

A14 (dead-feed guard): `backtest.py:227-239` carries the inherited /010 A14 guard (`ValueError` when >10% of `vol_natr_14` rows are within 0.001 of the mean). Active in the `if config.risk_r5_vol_target_enabled or config.risk_r5_kill_low_natr_enabled:` block (line 212), which now includes the /011 binary-kill enable path. PASS.

### Foundation Regression: PASS

`walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` (the iter-v3/058 fix). Compute helper `compute_embargo_candles(label_timeout_minutes, interval_minutes)` returns `timeout_minutes // interval_minutes + 1` at `walk_forward.py:38` — single source of truth used in both walk-forward boundary AND lgbm CV gap. `validation_v1.py:58` carries `REQUIRED_GAP = (21 + 1) * 5 = 110` for v1's 5-symbol universe. `tests/test_lookahead_embargo.py` contains all 4 mandated regression tests. QE's commits at `b788d4f` touch ONLY backtest_models.py, backtest.py, reporting_v1.py, run_baseline_v1.py, and the new test file — no foundation regression.

### Cadence + Axis Sanity: PASS

- `phase5p5_gate.md` OVERALL=PASS confirmed. All 13 sections PASS or PASS-with-explicit-note.
- Brief Section 0.6 declares axis family `risk-primitive` (binary-kill subtype). Subtype distinction (binary-kill vs proportional-scaling) is structurally orthogonal per brief Section 0.6 rationale (state-discontinuous vs smooth multiplicative).
- Rotation status VALID. Prior 5 EXPLORATIONs from catalog ledger: /006 universe, /007 feature-family, /008 methodology, /009 feature-family, /010 risk-primitive. /011 = risk-primitive = 2nd consecutive risk-primitive but only 1-of-5 with same family. The skill's "all 5 same family" rule does NOT fire. Rotation discipline preserved.
- Cycle-2 cadence: /011 = EXPLORATION #6 of 10 since baseline. CONFIRMATION unreachable until /015. Cap ≤2h declared.

### Falsifier Presence: PASS

Brief Section 4 carries six falsifiers (F1-F6) with explicit numerical conditions:
- F1 (PRIMARY): `(/011 OOS monthly Sharpe) - (BASELINE_V1 OOS monthly Sharpe +0.6637) < -0.05` → NEGATIVE; catastrophic at Δ < -0.20.
- F2: portfolio OOS R5-BINARY-KILL fire rate ∉ [10%, 60%] → NEGATIVE-mis-calibrated.
- F3 (sign-symmetric per /010 Critic Rec #1): IS Δ < -0.10 OR IS Δ ∈ (+0.05, +0.30] OR IS Δ > +0.30.
- F4: DEGENERATE_PREDICTOR detector fire → NEGATIVE-data-integrity.
- F5: DSR computability (n_eff_per_cell_median ≥ 4) → NEGATIVE-methodology-regression.
- F6 (NEW per /010 Lesson #2): OOS roster-overlap with BASELINE < 61% → NEGATIVE-basin-shift.

Brief Section 8 pre-registers six verdict classes with explicit numerical gates; sign-symmetric on F3.

## /011-Specific Pre-Flight Mini-Checks

### Embargo Discipline (NATR lookup past-only)
PASS. Lookup is `r5_natr_lookup.get((sym, ot), float("nan"))` at `backtest.py:431` — the (sym, ot) tuple is for the CANDLE BEING EVALUATED (its own open_time), not the next candle. `vol_natr_14` in the parquet at that row was computed from past N candles via pandas_ta rolling-window NATR. No forward scan.

### A14 Dead-Feed Guard Active for /011 Path
PASS. The A14 guard at `backtest.py:227-239` is gated by `config.risk_r5_vol_target_enabled or config.risk_r5_kill_low_natr_enabled` (line 212) — meaning the dead-feed pre-screen now fires for BOTH /010 and /011 enable paths. /011 inherits the same per-symbol vol_natr_14 constancy check.

### R5 ↔ R1/R2/R3 Ordering
PASS-WITH-CLARIFICATION. Verified call ordering in `backtest.py`:

```
get_signal (lgbm.py)
  ├─ confidence threshold gate (returns NO_SIGNAL if below)
  └─ R3 OOD Mahalanobis gate (lgbm.py:731-763; returns NO_SIGNAL if OOD)
                ↓
if signal.direction != 0 and signal.weight > 0:
  ├─ R5-BINARY-KILL (backtest.py:430-444; STATELESS entry skip)
  ├─ R1 cooldown (backtest.py:445-449; cooldown_until)
  ├─ vt_scale (line 451-452)
  ├─ R2 drawdown brake (line 454-463)
  ├─ R5 legacy proportional vol-target (line 465-481; DISABLED for /011)
  └─ create_order (line 482-489)
```

Brief Section 6.3 claim "R3 ... operates BEFORE prediction. R5-BINARY-KILL operates AFTER prediction" is supported: R3 OOD fires INSIDE `get_signal` (before R5-BINARY-KILL would ever see the signal); R3-vetoed signals never reach the R5 counters. The pre-flight dispatch's concern "if R5 fires after R3, Optuna may shift R3 behavior to compensate" is mechanically defused because R3 cutoff is a data-deterministic 70th-percentile of training-window Mahalanobis distances (`lgbm.py:168 ood_cutoff_pct=0.70` hardcoded, `lgbm.py:611` `np.quantile(distances, 0.70)`) — NOT an Optuna hyperparameter. Optuna cannot shift R3 behavior between trials. R3/R5 firing rates are statistically independent at the cell level.

### Edge Case at NATR_14 = 2.0% Exact
PASS. Strict `<` at `backtest.py:436`:
```
if not math.isnan(_natr_kill) and _natr_kill < float(config.risk_r5_kill_low_natr_min_pct):
```
Exact 2.0% → comparison evaluates False → entry PROCEEDS, not skipped. Test class confirmed at `test_iteration_v1_011_r5_binary_kill.py:114 test_at_threshold_is_not_killed`.

### D-RPRT-001 Fix Verified
PASS. `reporting_v1.py:1325-1387 append_r5_binary_kill_rows_to_comparison` writes both rows with IS rate in column [1] (`in_sample`) and OOS rate in column [2] (`out_of_sample`). Lines 1366-1369 + 1372-1375 emit `[metric_name, r5_kill_fire_rate_is, r5_kill_fire_rate_oos, _ratio(oos, is)]` — values match the column-label semantics. Tests `test_column_labeling_correct`, `test_d_rprt_001_fix_not_inverted` confirm.

### Axis Isolation Guarantee (LM Master Rec #2 Deferred)
PASS. `bounds_profile` resolution at `run_baseline_v1.py:833-838` is unchanged — gated only by `--pruned-features` flag (cycle-2 default `v1_pruned`). No `feature_fraction=1.0` pin introduced for /011. The brief Section 3.6 explicit DEFER of LM Master Hyperparameter Rec #2 is honored at the src/ level. /011 stays directly comparable to /010 on bounds-profile axis.

### Brief Section 3.6 Amend Completeness
PASS. All 9 LM Master Phase 4.5 items addressed (verified against `lgbm_advisor.md` lines 13-83):
- Hyper Rec #1 (n_trials/ENSEMBLE_SIZE/seed UNCHANGED): ADOPTED.
- Hyper Rec #2 (feature_fraction=1.0 pin): DEFERRED to /012 with rationale.
- Hyper Rec #3 (no min_data_in_leaf adjustment): ADOPTED.
- Feature Rec #1 (no feature changes): ADOPTED.
- Saturation Risk #1 (cross-roster magnitude divergence interpretation): ADOPTED into Section 5.1.
- Saturation Risk #2 (F6 overlap 70-78% expected): NOTED into Section 4 F6.
- Saturation Risk #3 (per-symbol concentration asymmetric vs /010): NOTED into Section 7 FM5.
- Basin-shift revision (entry-filter 20-30%): ADOPTED into Sections 5.1 + 7.
- Modal verdict distribution: DOCUMENTED in Section 8.

## Summary

Foundation intact. Anti-Pattern Catalog A1-A13 scan clean. R5-BINARY-KILL implementation matches brief spec: STATELESS, strict `<` comparison, NaN-safe via `math.isnan`, IS/OOS counter partitioning by OOS_CUTOFF_MS, evaluated BEFORE cooldown/vt_scale/R2/legacy-R5. Entry-gate ordering correct; R3 firing rate is NOT Optuna-tunable so no confounding with R5. D-RPRT-001 fix correctly applied. Axis isolation preserved. LM Master Phase 4.5 retro-amend complete.

Backtest may launch. Phase 6 proceeds.
