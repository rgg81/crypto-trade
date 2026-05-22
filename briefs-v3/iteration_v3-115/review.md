# Phase 7.5 Critic Review — iter-v3/115 — FINAL (single round — no clarifications requested)

OVERALL: EXPLORATION-NEGATIVE — IS monthly Sharpe +0.3172 fires the pre-registered NEGATIVE criterion (IS < +0.7325); look-ahead audit clean, implementation matches brief, the NEGATIVE is a genuine attributable property of the horizon-exit labeling axis.

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle-6 EXPLORATION slot #6 of 10). Per the EXPLORATION protocol, Checks 1, 2, 4, 5, 6, 8 are verdict-scoring; Check 3 is informational.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS

The make-or-break check. The `fixed_horizon` label is forward-looking by construction (correct and intentional), so the audit reduces to whether the 21-candle forward label window is properly embargo-purged at the train/test boundary. It is, verified at source on three surfaces.

(1) **Label construction** (`labeling.py:349-423`): under `label_mode="fixed_horizon"` the per-entry scan iterates from `pos+1`, breaks when `close_time > deadline` where `deadline = entry_close_time + timeout_ms` (`timeout_ms` from `label_timeout_minutes=10080`), and labels `sign(fwd_return_pct)`. The forward window is exactly the `label_timeout_minutes` horizon — the same horizon the walk-forward embargo is computed from. No horizon-vs-embargo mismatch.

(2) **Train/test embargo** (`walk_forward.py:113`): `train_end_ms = test_start_ms - embargo_ms`, `embargo = (10080//480 + 1) = 22 candles`. Confirmed at the IS/OOS boundary in run.log: test month 2025-04 → `Train window: 2023-04-01 → 2025-03-24`, training ending exactly at the OOS cutoff. The 22-candle embargo means no training row's `fixed_horizon` label window straddles into the test fold.

(3) **OOS +0.94 is genuine regime exposure, not a leak.** `out_of_sample/monthly_pnl.csv` shows a genuinely MIXED OOS book — 5 of 14 months negative. A look-ahead leak inflates OOS PnL uniformly; instead the OOS Sharpe comes from 2 regime-favorable months (2025-05 +20.7%, 2025-08 +24.7%) against real losing months. Combined with the verified embargo, the OOS +0.94 is the /105 IS-collapse/OOS-spike regime artifact the brief pre-registered (Section 7 Mode 2), not a leaked-future artifact.

### Check 2 — Embargo Width: PASS

Label horizon = 21 candles (`10080 / 480`). Required gap = `(21+1) × 3 = 66`. Actual `REQUIRED_GAP = 66` (`validation_v3.py:76`, run.log line 26). The intra-Optuna CV gap is verified at every fold (`gap=184h / 22 rows`; `cv_gap = 22 × 3 = 66` cross-cell). Byte-identical to /059, correctly sized for the 21-candle `fixed_horizon` horizon (which equals the v3 triple-barrier timeout — the embargo-invariance rationale the brief gives for hand-fixing N=21 is correct). `_verify_timeout_consistency` PASS.

### Check 3 — Multiple-Testing Correction: PASS (informational for EXPLORATION)

Per TYPE=EXPLORATION, DSR/PSR are informational; only PBO is meaningful at the 3-seed/35-trial budget (`feedback_v3_dsr_mode_artifact.md`). PBO = 0.1426 < 0.4 — passes. `dsr.json` carries `dsr_relative=0.9593`, `dsr_relative_b4=1.0` — EXPLORATION-mode structural artifacts, informational only. `n_trials=315`, `n_eff=16`. (Minor: the engineering report Key Metrics block reports `dsr 0.000` without surfacing `dsr_relative` — a reporting incompleteness, not a defect.)

### Check 4 — IC Correlation: PASS (non-applicable)

Zero feature families added. `V3_FEATURE_COLUMNS` unchanged at the 14-feature /059-canonical stack. No new-vs-existing pair to test. The pre-existing /059-canonical pairs above 0.70 (`regime_momentum_signed_5d` vs `vwap_dev_20`) are inherited, covered by the `feedback_v3_engineered_feature_pivot.md` carve-out, not introduced by /115.

### Check 5 — ADF Stationarity: PASS

`adf_test.csv` at the IS-window-end month 2025-03: all 42 feature-symbol pairs `p < 0.05`, `stationary=True`. The 395 `stationary=False` rows are early-month insufficient-sample artifacts. Features unchanged from /059.

### Check 6 — Pareto Dominance: PASS (non-applicable)

EXPLORATION mode produces a single deterministic roster; `pareto_front.csv` not produced (correct). The Pareto check is deferred to the iter-v3/120 CONFIRMATION.

### Check 7 — Reproducibility: PASS

Commit SHA `2b99a1bd6e2bd655ac6812806abe5bd075746083` stamped. The runner uses an explicit 14-element `feature_columns` list, never `None`. The 3-seed ensemble seeds are literal in `ensemble_summary.json`. Trade spot-checks re-computed clean (OOS BCH SHORT net 4.0489% / weighted 1.4171; OOS BCH LONG weighted 5.7732; OOS TRX SHORT weighted −1.9284 — correct loss sign). PnL arithmetic, direction sign, fee deduction, weight_factor all correct.

### Check 8 — Hypothesis-Implementation Alignment: PASS

Every brief change maps to code; no scope creep; the implementation tests the registered hypothesis.

- **Change 1 (label):** `label_mode="fixed_horizon"` in `_build_v3_model` common_kwargs; flows to `label_trades(label_mode=...)`. Verified.
- **Change 2 (execution):** `_atr_tp, _atr_sl = 100.0, 100.0`. The barriers-non-binding requirement is INDEPENDENTLY CONFIRMED: `out_of_sample/trades.csv` has 52/53 `timeout` + 1 `end_of_data`, ZERO barrier exits; `in_sample/trades.csv` has ZERO barrier exits. Coherent horizon-exit execution genuinely landed.
- **Change 3 (label_mode accretion guards):** both guard sites updated to `"fixed_horizon"`; config-accretion check PASS.
- **Change 4 (`ITERATION_LABEL`):** `"v3-115"`.
- **Change 5 (/114 LDO kill-switch revert):** `regime_gate_symbols=()`, `enable_ldo_realvol_gate=False`, `enable_regime_gate=False` — the /059-canonical risk stack restored. The /114 LDO realvol gate does NOT run through the /115 backtest; no co-varying confound (the iter-v3/110 stale-knob failure mode is averted). Corroborated: /072's LDO catastrophe did NOT recur (/115 LDO OOS +31.04% net PnL / 54.5% WR).
- **Change 6 (pre-flight guard):** the guard at `run_baseline_v3.py:854-869` now asserts `regime_gate_symbols == ()` and `enable_ldo_realvol_gate == False`; the runner passed pre-flight.
- **Integration test:** `test_fixed_horizon_label_mode.py` is a genuine adversarial end-to-end test (injects a +50% spike AND a −45% crash inside the 21-candle window, asserts `timeout` resolution).
- **Provenance discipline** (`feedback_v3_brief_parameter_provenance.md`, the first iteration after /114's Check-1 FAIL): the brief cites exactly one design parameter — horizon N=21 — and DECLARES it hand-chosen, justified by embargo-invariance (N=21 = the v3 triple-barrier timeout). There is no IS-tuned scalar, no sweep, no threshold laundered as an optimization output, no false-provenance claim. The /114 failure mode is structurally absent: nothing is tuned. Provenance is clean.

Two cosmetic stale-string defects noted (NOT verdict-affecting, NOT brief violations): `run_baseline_v3.py:2889` banner print still reads `label_mode=triple_barrier; V3_FEATURE_COLUMNS=22` (run.log line 34 echoes it) — a display string; the actual config is verified `fixed_horizon`/14-feature at run.log lines 3/20/21/24-26. And `MODEL_SPECS` at lines 197-199 still carry the `v3-113-` model-name prefix — cosmetic; the `ITERATION_LABEL` driving report paths is correctly `v3-115`. Recorded for process hygiene.

## Recommendations to QR

EXPLORATION-NEGATIVE — verdict final. Three items for the iter-v3/120 CONFIRMATION QR and the closeout diary:

1. **The horizon-exit labeling architecture is closed for cycle 6 and must not be re-bundled.** The T3 ORACLE counterfactual predicted the geometry penalty and the production backtest confirmed it: IS collapsed to +0.3172 (Δ −0.52 vs the /060 anchor). The asymmetric +2/−1 ATR price barrier is itself a Sharpe-generating device; a symmetric 21-candle time exit discards it. This is the second falsification of a label-estimand change in the /072 → /105 → /115 lineage — the axis is structurally spent. The iter-v3/120 CONFIRMATION must NOT carry `label_mode="fixed_horizon"` as a bundle ingredient.

2. **Correct the runner banner-print and MODEL_SPECS stale strings at the next setup commit.** `run_baseline_v3.py:2889` (`label_mode=triple_barrier; V3_FEATURE_COLUMNS=22`) and the `v3-113-` MODEL_SPECS prefix are cosmetic but make run.log self-contradictory (line 34 says `triple_barrier`, line 21 says `fixed_horizon`). Add these to the next iteration's setup-commit cleanup so the log is internally consistent.

3. **The engineering report's per-symbol attribution conflates two distinct metrics.** The report's "Per-Symbol OOS Attribution" table lists `pct_of_total_pnl` values but labels them `concentration_pct`, while `comparison.csv`'s per_symbol block reports genuinely different `concentration_pct` values. Not verdict-affecting (NEGATIVE is locked on the IS leg), but the closeout diary should attribute the result on the correctly-named metric.

## Clarifications Requested from QR — NONE

Every check resolved on unambiguous source evidence. The look-ahead audit is clean (22-candle embargo correctly sized for the 21-candle `fixed_horizon` horizon, verified at the IS/OOS boundary; OOS book genuinely mixed = regime artifact not leak). The implementation matches the brief on all 6 changes with zero scope creep, the /114 kill-switch is reverted clean, and provenance is clean. The verdict follows mechanically from the pre-registered Section 8 first-match-wins taxonomy: Criterion 1 fires on the IS leg (IS +0.3172 < +0.7325). Round 2 skipped.
