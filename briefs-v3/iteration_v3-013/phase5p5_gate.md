# Phase 5.5 Gate — iter-v3/013

OVERALL: PASS

## Per-Section Status
- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24 and training_months=24 declared IMMUTABLE; ENSEMBLE_SIZE=1, colsample_bytree=1.0, n_trials=10 set by --exploration. IS window and OOS window named in absolute dates via OOS_CUTOFF_MS=1742774400000.
- Section 0.5 (Iteration Type): PASS — TYPE: EXPLORATION declared; cadence EXPLORATION #6 of 10; single-axis=universe (drop MKR 4-symbol→3-symbol BCH+LDO+TRX); wall-clock budget <30 min / 2h hard cap; explicit "NEVER updates BASELINE_V3.md"; MANDATORY per `feedback_mkr_threshold_compression.md` FIRED at iter-v3/012 (5th consecutive MKR OOS-negative).
- Section 1 (Hypothesis): PASS — one sentence; testable claim (IS Sharpe ≥+0.40 vs iter-v3/012's +0.81); specific mechanism (MKR structural −25.75% OOS drag and −23.21% IS drag); Falsifier 1 at IS Sharpe <+0.10.
- Section 2 (IS-Only Evidence): PASS — committed script `analysis/iteration_v3-013/drop_mkr_demo.py` at SHA 5217490 (BEFORE this brief per git log); outputs `expected_drop_mkr_metrics.csv` and `synthesis.md` verified present; counterfactual aggregates with IS/OOS per-symbol breakdown (§2.2); behavioral-effect predictor with saturation falsifier IS trades <240 per `feedback_axis_saturation_predictor.md` (§2.3).
- Section 3 (Proposed Changes): PASS — symbols CHANGED (drop MKRUSDT, retain BCH+LDO+TRX); labeling UNCHANGED; 13 features UNCHANGED (inherited from iter-v3/009); all 7 risk gates UNCHANGED; sub-fix decomposition 7 items with 15-verifier reconciliation table (§3.6); inheritance plan §3.8; REQUIRED_GAP formula propagation documented (88→66 = (21+1)×3).
- Section 4 (Expected OOS Impact): PASS — predicted IS Sharpe range [+0.30, +1.20] with median +0.65 and CI reasoning; 3 metric falsifiers + 1 process falsifier locked in §4.3; 4-pathway catalog framing in §4.4 (PROMISING / PROMISING-INERT / NEGATIVE / BLOCK).
- Section 5 (Risk Mitigation): PASS — 4 cadence-discipline structural safeguards; 4 methodology-pipeline safeguards; 3 universe-axis-specific risks with REQUIRED_GAP propagation fail-fast pattern.
- Section 6 (Risk Management Design): PASS — 7-primitive table with fire-rate predictions and regime coverage; gate orthogonality for universe shrinkage documented; combined kill rate 80–90% inherited.
- Section 7 (Failure-Mode Prediction): PASS — 6 pre-registered predictions: P1/P2/P3 process-level (V3_MODELS propagation, REQUIRED_GAP mismatch, saturation falsifier); P4/P5/P6 model-level (PROMISING 40%, PROMISING-INERT 30%, NEGATIVE 20%); calibrated against iter-v3/010+011+012 history.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — EXPLORATION pathways only (no MERGE pathway); 11 EXPLORATION-PROMISING criteria locked before backtest including criterion 11 (behavioral-effect verifier IS trades <240); BLOCK conditions enumerated; explicit "NEVER updates BASELINE_V3.md".
- Section 9 (Library Stack): PASS — no new external deps; 8 packages listed with versions/licenses; fallback for pyarrow documented; reproducibility stamp spec included.

## Cadence Compliance
- TYPE=EXPLORATION: PASS
- Single-axis variation (universe only): PASS — V3_MODELS + REQUIRED_GAP + ITERATION_LABEL only; no features/labeling/gate changes
- --seeds 1 invocation: PASS — §3.5 sub-fix #7 specifies `--exploration --seeds 1 --n-trials 10`
- Wall-clock budget ≤2h: PASS — target <30 min, hard cap 2h, Falsifier 3 at >30 min
- Behavioral-effect predictor present: PASS — §2.3 saturation falsifier IS trades <240 per `feedback_axis_saturation_predictor.md`; also locked as EXPLORATION criterion #11 in §8

## Reasons (if BLOCK)
n/a — OVERALL=PASS
