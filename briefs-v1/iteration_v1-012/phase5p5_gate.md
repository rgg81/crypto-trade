# Phase 5.5 Gate — iter-v1/012

OVERALL: PASS

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle-2, position 7/10; wall-clock cap ≤2h)

## Axis Family + Rotation Status
FAMILY: methodology-substrate-test (NEW 8th catalog family — first usage)
ROTATION_STATUS: VALID
- Prior 5 EXPLORATION families (from exploration_catalog.md): iter-v1/007=feature-family, iter-v1/008=methodology, iter-v1/009=feature-family, iter-v1/010=risk-primitive, iter-v1/011=risk-primitive
- Composition: 2/5 risk-primitive + 2/5 feature-family + 1/5 methodology — no family at 3+/5 saturation threshold
- methodology-substrate-test is structurally orthogonal to all 7 prior families; rotation VALID per Section 0.6 rationale

## HIGH-RISK Declaration
HIGH-RISK: NO (NORMAL-RISK declared in Section 2.5)
- Rationale verified: /012 does NOT change the training-objective domain (same training rows, labels, weights, feature columns, loss function, R5 mechanism as /011). Only RNG initialization (ENSEMBLE_SEEDS window offset 0→3) changes. No HIGH-RISK mitigation required.

## LM Master Response Verification
- briefs-v1/iteration_v1-012/lgbm_advisor.md exists: PASS
- lgbm_advisor.md structure: 7 sections (Context Read, Hypothesis Validation Framing, Probability Calibration, Mechanism Analysis, Predicted IS Metrics, Predicted OOS Metrics, /013-/014 Pre-Stage, Honest Confidence). Advisory closes with "Brief is sound. No hyperparameter or feature changes recommended for /012 — pure RNG-init isolation is the experiment."
- LM Master advisory format: NOT numbered-recommendation format; advisory provides calibration/prediction framing rather than discrete numbered recs. Brief Section 3.4 explicitly addresses the three anticipated advisory positions: (1) keep config bit-identical [pre-adopted], (2) parallel seed probes [rejected with ≤2h rationale], (3) calibrate F7 thresholds on /010↔/011 prior [pre-adopted]. These exhaust the advisory's actionable guidance.
- Brief Section 3.5 addresses 3 Critic /011 process recs explicitly (Rec #1 BASIN-INHERITANCE subtype, Rec #2 F6 committed artifact, Rec #3 engineering report mandatory): PASS

## Cadence Check
- Wall-clock budget declared: ≤2h (Section 0.5; confirmed EXPLORATION); predicted 75-90 min per /011 reference: PASS
- EXPLORATION, not CONFIRMATION — cadence constraint N/A for this check
- Cycle-2 EXPLORATION count post-/012: 7 of 10 required before CONFIRMATION at /015 earliest

## Per-Section Status
- Section 0 (Data Split): PASS — Section 0.1 anchors at `v0.v1-baseline-corrected` (commit f8bc12c); BASELINE_V1.md IS Sharpe +0.2829 / OOS +0.6637; OOS_CUTOFF_DATE=2025-03-24 and training_months=24 are sacred constants unchanged
- Section 0.5 (Iteration Type): PASS — EXPLORATION declared explicitly; cycle-2 position 7/10
- Section 0.6 (Architecture-Family Justification): PASS — family=methodology-substrate-test (8th catalog family); prior 5 families enumerated; rotation VALID with explicit rationale; distinction from methodology family (/008) articulated; distinction from hyperparameter-region (/005) articulated
- Section 1 (Hypothesis): PASS — 3-way pre-registered hypothesis with specific numerical conditions per outcome (F7 LTC IS overlap >70% → Outcome A SUBSTRATE-LOCKED, <30% → Outcome B SEED-LOCKED, [30%,70%] → Outcome C PARTIAL); specific enough to be falsifiable
- Section 2 (IS-Only Evidence): PASS — committed script: analysis/iteration_v1-012/f6_roster_overlap.py (commit 360650f); reference artifact: reports-v1/iteration_v1-011/f6_roster_overlap.csv (same commit). Lighter than typical EXPLORATION with explicit justification (substrate finding empirically established at /011; F6/F7 thresholds derived from /010↔/011 93.27% LTC IS overlap measurement). Sections 2.1-2.4 provide IS-only numerical tables with inverse-causal reasoning. No EDA on OOS data claimed.
- Section 2.5 (HIGH-RISK Axis Declaration): PASS — NORMAL-RISK declared with explicit rationale; comparison to HIGH-RISK categories (risk-primitive constraint changes, universe substitution, label-mode change, feature-set replacement, bar-interval change) makes clear /012 falls in none of these
- Section 3 (Proposed Changes): PASS — Section 3.1 specifies ONLY TWO changes (run_baseline_v1.py additive ensemble_seeds_offset, no src/ changes); Section 3.2 provides canonical runner invocation; Section 3.3 predicts wall-clock; Section 3.4 addresses LM Master advisory; Section 3.5 adopts 3 Critic /011 process recs with explicit implementation
- Section 4 (Expected OOS Impact / Falsifiers): PASS — F1-F7 with explicit numerical conditions; F7 is substrate-test specific with pre-registered 3-cell classification; each falsifier fire condition documented. Note: brief uses "Section 4" for Falsifiers F1-F7 and "Section 5" for predicted outcomes — both map to the gate's "Expected OOS Impact + Falsifier" requirement
- Section 5 (Risk Mitigation): PASS — Section 5 provides predicted outcomes per 3-way pre-registration with probability assignments (60/25/15 for A/B/C) and explicit reasoning chains; Section 6 provides the falsification matrix; R5-BINARY-KILL config is BIT-IDENTICAL to /011 so no new risk-primitive changes require mitigation
- Section 6 (Risk Management Design): PASS — 8-primitive risk management infrastructure is inherited unchanged from /011 (R5-BINARY-KILL wiring confirmed present in src/crypto_trade/backtest.py via grep). Brief Section 7 (mechanism diagram) makes explicit the risk gate pipeline. NORMAL-RISK axis with no risk gate changes; full redesign not required.
- Section 7 (Failure-Mode Prediction): PASS — Brief Section 6 ("What Could Falsify") pre-registers all measurable F1×F3×F7 failure-mode cells including the off-table outcome cell (F1>+0.30 AND F7<30% would be an anomaly requiring QE seed-determinism audit). Section 7 (mechanism diagram) provides the structural prediction for how basin gravity operates. Forward-looking, verified against Section 8 verdict matrix.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — Section 8.1 fully pre-registers the verdict-class for all measurable F1×F3×F7 cells with deterministic assignment; Section 8.2 adds substrate-test diagnostic outcome assignment; Section 8.3 explicitly states NO-MERGE for both EXPLORATION-NEGATIVE and EXPLORATION-PROMISING; Section 8.4 notes NORMAL-RISK means no HIGH-RISK tripwire applies
- Section 9 (Library Stack): PASS — explicit version pins: pandas==2.3.3, numpy==2.3.4, lightgbm==4.6.0, optuna==4.5.0, statsmodels==0.14.4; f6_roster_overlap.py uses stdlib only; no new libraries required

## Phase 6 Setup Verification (v1 Code Wiring)

All 4 wiring items verified as present and correct:

1. `--ensemble-seeds-offset` CLI flag: CONFIRMED at run_baseline_v1.py lines 793-800; `_derive_ensemble_seeds(size, offset)` at lines 118-143; propagated through `run_model()` kwarg at line 163 → _derive_ensemble_seeds call at line 243; threaded to all 4 models via `_r5_kwargs` dict at lines 960-966
2. F6 roster-overlap join script: CONFIRMED at analysis/iteration_v1-012/f6_roster_overlap.py (commit 360650f); reference artifact reports-v1/iteration_v1-011/f6_roster_overlap.csv present
3. R5-BINARY-KILL wiring in backtest.py: CONFIRMED at src/crypto_trade/backtest.py lines 428-437 (entry-gate kill_low filter) and 559+ (reporting); inherited from /011 commit b788d4f
4. comparison.csv R5-BINARY-KILL row appender: CONFIRMED at src/crypto_trade/strategies/ml/reporting_v1.py line 1325 `append_r5_binary_kill_rows_to_comparison`; imported at run_baseline_v1.py line 83; called at backtest.py line 672

Lint: `uv run ruff check run_baseline_v1.py analysis/iteration_v1-012/f6_roster_overlap.py src/crypto_trade/strategies/ml/reporting_v1.py src/crypto_trade/backtest.py` — ALL CHECKS PASSED

Tests: 128 v1-specific tests passed (test_reporting_v1.py: 55, test_iteration_v1_011_r5_binary_kill.py + test_iteration_v1_010_r5.py + test_runner_cli_v1.py + test_v1_pruned_features.py: 73); no new src/ code was added for /012 so no new tests required

No src/ changes needed for /012. All wiring is inherited from /011 (b788d4f) + offset flag added at QR commit 360650f.

## One Variable at a Time
PASS — exactly one dimension changes vs /011: ENSEMBLE_SEEDS window offset 0→3. R5-BINARY-KILL config BIT-IDENTICAL. Feature columns unchanged. Symbols unchanged. training_months unchanged. OOS_CUTOFF_DATE unchanged. Axis isolation is mechanically clean.

## Sacred Constants
PASS — OOS_CUTOFF_DATE=2025-03-24 and training_months=24 confirmed unchanged; 5-seed CONFIRMATION roster (42,123,456,789,1001) is the ENSEMBLE_SEEDS prefix; /012 uses offset=3+size=3 → [789,1001,2002] which is inside the 10-element CONFIRMATION roster

## Reasons
None. All sections PASS. Gate proceeds to Phase 6.0 Critic pre-flight.
