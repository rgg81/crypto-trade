# Phase 5.5 Gate — iter-v3/115

OVERALL: PASS

Iteration type: EXPLORATION (cycle-6 slot #6 of 10)
Cadence check: PASS — wall-clock budget 2h; run spec `--exploration --n-trials 35`, ENSEMBLE_SIZE=3
single-seed (outer=42 lineage); 5 prior cycle-6 EXPLORATIONs (#1–#5 at /110–/114) confirmed in
exploration catalog.

## Per-Section Status

- Section 0 (Data Split / Provenance): PASS — OOS_CUTOFF_DATE=2025-03-24 and training_months=24
  confirmed unchanged; horizon N=21 DECLARED hand-chosen (embargo-invariance rationale, not IS
  performance); no IS-tuned scalar; Section 0 is also the provenance declaration required by
  feedback_v3_brief_parameter_provenance.md — provenance is clean.
- Section 0.5 (Iteration Type): PASS — TYPE=EXPLORATION declared; run spec complete and consistent
  with cadence rules.
- Section 1 (Hypothesis): PASS — one sentence, specific mechanism (coherent horizon-exit architecture
  replacing triple-barrier; predicted non-positive OOS effect; T3 counterfactual cited as basis).
- Section 2 (IS-Only Evidence): PASS — 3 committed scripts + 6 result tables (T1–T6) at EDA SHA
  d871b22 (`analysis(iter-v3/115): coherent horizon-exit labeling gating EDA`); IS-only invariant
  confirmed (all scripts assert `close_time < OOS_CUTOFF_MS = 1742774400000`; no OOS-window file
  touched); pre-registered GO rule fixed before scripts ran; verdict = NO-GO does NOT block
  (per the hard-ban regime every EXPLORATION runs a backtest regardless of EDA verdict). Tables T1
  (label balance), T2 (execution consistency), T3 (counterfactual book — the decisive gate), T4
  (feature IC), T5 (permutation null), T6 (GO/NO-GO) all present and numerically complete.
- Section 3 (Proposed Changes): PASS — ONE axis (labeling architecture); enumerated knobs in config
  diff table; symbols/features/risk stack/model all declared UNCHANGED; no cluster-importance check
  needed (zero features added).
- Section 3.5 (Implementation Scope): PASS — see verification detail below.
- Section 4 (Expected OOS Impact): PASS — IS point estimate +0.30 with 80% interval [−0.40, +0.85];
  OOS point estimate +0.05 with 80% interval [−0.55, +0.55]; falsifier (OOS < +0.3403) and
  supplemental SUSPICIOUS gate (OOS/IS > 3.0) both pre-registered and concrete.
- Section 5 (Risk Mitigation): PASS — two axis-specific risks (longer hold duration, /072 LDO
  catastrophe) with named mitigations; correct acknowledgement that no new IS-calibrated threshold
  is introduced.
- Section 6 (Risk Management Design): PASS — 7-primitive table present; all gates declared
  /059-identical; fire-rates inherited; behavioural-effect predictor present (IS roster expected to
  change materially, ~25–30% candles re-labelled; inertia falsifier IS-roster-Δ < 8% pre-registered).
- Section 7 (Failure-Mode Prediction): PASS — 4 modes with probabilities (~60% geometry-does-not-
  transfer, ~25% IS-collapse/OOS-spike SUSPICIOUS, ~10% implementation bug, ~5% residual upside);
  mechanisms and metric signatures pre-registered; honest modal outcome is NEGATIVE.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — 4-category disjunctive taxonomy (NEGATIVE, SUSPICIOUS-
  OOS-DOMINANT, INERT, PROMISING) with concrete numerical thresholds anchored on the /060
  EXPLORATION-mode reference (IS +0.8325 / OOS +0.1403); locked before Phase 6.
- Section 9 (Library Stack): PASS — pinned stack declared (lightgbm 4.6.0, optuna 4.8.0, etc.);
  no new library; in-tree validation_v3.py for CPCV/PBO/PSR; integration test mandate acknowledged
  (end-to-end smoke test for label+execution pairing).
- Section 10 (QR Audit Trail): PASS — axis selection documented; dead-path disclosure for meta-
  labeling (/108 EDA closed, AUC 0.561) and fixed-horizon-label-only (/072 NEGATIVE); distinction
  from /072 argued on Critic-recommended basis; provenance discipline confirmed.

## Section 3.5 Implementation Scope Verification

The brief specifies 6 changes in Section 3.5 (Changes 1–4 were PASS in gate `2ee9119`; Changes 5–6
are the additions that resolve the prior BLOCK). All 6 are verified below.

**Change 1** (`label_mode="fixed_horizon"` in common_kwargs at ~line 1978): PASS — confirmed at
run_baseline_v3.py:1978. The labeling.py `fixed_horizon` branch exists at lines 349/411–423; no
labeling.py change needed. `neutral_threshold_pct=None` (2-class label) is correct default.

**Change 2** (`atr_tp_multiplier=100.0`, `atr_sl_multiplier=100.0` in common_kwargs): PASS — confirmed
at run_baseline_v3.py:1955–1956. Setting both to 100.0 overrides ATR-derived barriers to non-binding
(~370%+ on IS NATR median ~3.7%). Engineering report must confirm IS exit-reason mix ≥ 99% `timeout`.
`BacktestConfig.stop_loss_pct=4.0`/`take_profit_pct=8.0` are unused fallbacks when ATR signals
present. `timeout_minutes=10080` and `label_timeout_minutes=10080` unchanged —
`_verify_timeout_consistency` continues to pass.

**Change 3** (two guard-site updates for `label_mode`): PASS — confirmed at run_baseline_v3.py:1090
(`_canonical_v059` list entry `("label_mode", _acc_inner.label_mode, "triple_barrier")`) and
run_baseline_v3.py:1186 (`expected_label_mode = "triple_barrier"`). Both must be updated to
`"fixed_horizon"`. Comment prose must be rewritten to avoid contradicting the new state.

**Change 4** (`ITERATION_LABEL="v3-115"` at line 131): PASS — confirmed at run_baseline_v3.py:131
(currently `"v3-114"`).

**Change 5** (revert /114 LDO kill-switch state to /059-canonical): PASS — line references verified
against actual runner code. The four fields named in the brief's table are confirmed at their stated
locations:
- run_baseline_v3.py:2020 `regime_gate_symbols=("LDOUSDT",)` — CONFIRMED (current /114 state).
- run_baseline_v3.py:2026 `enable_ldo_realvol_gate=True` — CONFIRMED (current /114 state).
- run_baseline_v3.py:2027 `ldo_realvol_zscore_floor=0.30` — CONFIRMED.
- run_baseline_v3.py:2028 `ldo_realvol_lookback_bars=90` — CONFIRMED.
  The intended revert (`regime_gate_symbols=()`, `enable_ldo_realvol_gate=False`) matches the
  /059-canonical state and is consistent with Sections 3 and 6. `enable_regime_gate=False` at
  line 2018 is already /059-canonical and must NOT change — the brief correctly identifies this.
  The 13-knob `_canonical_v059` accretion guard does NOT cover these fields (confirmed), so Change 5
  is not self-enforcing; Change 6 is mandatory as the enforcement mechanism.

**Change 6** (update /114 pre-flight guard to assert reverted state): PASS — the code block to
replace (lines 847–869: comment block at 847–854, two `if` blocks at 855–869) is confirmed
verbatim in the actual runner. The replacement code in the brief asserts `regime_gate_symbols == ()`
and `enable_ldo_realvol_gate == False` — the logical inverse of the current guard, which would
crash on the reverted Change-5 state. Without Change 6, the runner crashes on pre-flight after
Change 5 (line 855 fires `RuntimeError` when `regime_gate_symbols != ("LDOUSDT",)`). Without
Change 5, the runner crashes with Change 6 in place (the new guard fires on the live
`enable_ldo_realvol_gate=True` state). The brief correctly states "Change 5 and Change 6 MUST land
together." The alternative of deleting the guard entirely is also declared acceptable.

## REQUIRED_GAP Reasoning Verification

PASS (unchanged from gate `2ee9119`). Horizon N=21 candles is identical to
`label_timeout_minutes = 10080 min / 480 min-per-candle`. `compute_embargo_candles(10080, 480)` =
10080 // 480 + 1 = 21 + 1 = 22 candles. REQUIRED_GAP = embargo_candles × n_symbols = 22 × 3 = 66.
Byte-identical to /059. REQUIRED_GAP defined at validation_v3.py:76 as `(21 + 1) * 3 = 66` —
confirmed at source.

## Provenance Discipline Check (feedback_v3_brief_parameter_provenance.md)

PASS (unchanged from gate `2ee9119`). The brief cites exactly one design parameter — horizon N=21.
DECLARED hand-chosen in Section 0. No IS sweep, no threshold selection, no hardcoded constant with
false sweep provenance. No OOS-window file access in EDA scripts. The /114 failure mode is
structurally impossible here: nothing is tuned.

## NO-GO EDA Does Not Block

PASS (unchanged from gate `2ee9119`). EDA verdict is NO-GO (g3 FAIL: horizon-exit execution Sharpe
worse than triple-barrier on all 3 symbols, Δ −0.37 to −1.11). Per the hard-ban regime, an EDA
NO-GO does NOT block Phase 6. The iteration runs a backtest. The NO-GO sets the modal prediction
(Section 4, Section 7 Mode 1). This is correctly handled in the brief.

## /114 Kill-Switch Revert Gap — RESOLVED

The prior gate `2ee9119` BLOCKED on one gap: Section 3.5 did not enumerate the /114 LDO realvol
kill-switch revert. The QR added Changes 5 and 6 at commit `9fd11fa`. Both changes are verified
above — line references are accurate, the crash-prevention logic is sound, and the reverted state
matches the declared /059-canonical design in Sections 3 and 6. The gap is CLOSED.
