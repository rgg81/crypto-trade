# Phase 5.5 Gate — iter-v3/031

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24 immutable; IS/OOS windows stated in absolute dates.
- Section 0.5 (Type Declaration): PASS — EXPLORATION cadence #3 of 10; MKR-threshold reference (feedback_v3_mkr_threshold_compression.md, 9-of-9 > 5 threshold); PROMISING-MECHANICAL subtype reference (feedback_v3_promising_mechanical_subtype.md); iter-v3/013 precedent named.
- Section 1 (Hypothesis): PASS — one sentence; single axis (drop LDO → removes drag → preserves BCH+TRX+ALGO from iter-v3/029); specific OOS Sharpe prediction bands [+1.85, +2.10] median +1.95.
- Section 2 (IS-Only Evidence): PASS — 9-iteration LDO trajectory table from committed engineering reports/Critic FINALs (IS-only per-symbol artifacts); BCH+TRX+ALGO independence proven by iter-v3/030 bit-identity confirmation; mechanical-lift arithmetic; behavioral-effect predictor with saturation falsifier; committed analysis artifacts at SHA 36aaacd (iter-v3/030 EDA, which is the most recent IS-only evidence source for LDO structural mismatch). No new EDA script required per iter-v3/013 MECHANICAL-DROP precedent.
- Section 3 (Proposed Changes): PASS — 5 sub-fixes enumerated: (1) DROP LDO from V3_MODELS, (2) REQUIRED_GAP 88→66, (3) clear LDO from V3_FEATURES_PER_SYMBOL, (4) ITERATION_LABEL update, (5) comment/message update in _verify_label_leakage_gap; each has verifier command.
- Section 4 (Expected OOS Impact): PASS — Sharpe delta with confidence interval [+1.85, +2.10] median +1.95; explicit falsifier "if OOS Sharpe < +1.50, hypothesis rejected"; PROMISING-MECHANICAL classification pre-registered (NOT PROMISING-clean).
- Section 5 (Risk Mitigation): PASS — concentration risk (TRX 50%→60-65%) acknowledged as outstanding constraint; cadence risks (budget overrun, cycle-cadence, single-axis discipline) mitigated; methodology hygiene (OOS contamination, V3_FEATURES_PER_SYMBOL cleanup, MKRUSDT exclusion check) addressed.
- Section 6 (Risk Management Design): PASS — 7-primitive gate table present; all gates UNCHANGED; fire-rate impact noted (LDO-specific firings removed; BCH+TRX+ALGO unchanged).
- Section 7 (Failure-Mode Prediction): PASS — 2 failure modes predicted with mechanisms; REQUIRED_GAP change identified as primary risk (gap narrowing from 88→66 shifts CPCV fold boundaries); NEGATIVE-SUSPICIOUS-OOS pattern named; per_cell_pbo.csv check specified.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — 10 pre-registered criteria; OOS Sharpe ≥ +1.85 PROMISING-MECHANICAL floor; OOS Sharpe ≥ +1.50 hard falsifier; BCH+TRX+ALGO bit-identity ±5% criterion; PROMISING-MECHANICAL classification and non-compoundable nature locked.
- Section 9 (Library Stack): PASS — identical to iter-v3/030; no new dependencies; mlfinpy/pypbo unavailability noted with pure-Python fallback reference.

## Reasons (if BLOCK)
N/A — OVERALL PASS.

## Gate Notes

1. **Section 2 — no new EDA script**: The iter-v3/013 MECHANICAL-DROP precedent established that a symbol-trajectory table from committed engineering reports is sufficient IS-only evidence for a drag-removal EXPLORATION. The most recent IS-data artifact is `analysis/iteration_v3-030/ldo_feature_subset_analysis.py` (SHA `36aaacd`) which confirmed LDO's structural mismatch. No additional EDA script is required. PASS with precedent citation.

2. **PROMISING-MECHANICAL pre-registration locked**: Section 4 and Section 8 both pre-register the expected verdict as PROMISING-MECHANICAL (NOT PROMISING-clean). This lock is binding — the QR cannot upgrade to PROMISING-clean post-result per `feedback_v3_promising_mechanical_subtype.md`. The Critic will verify this pre-registration at Phase 7.5.

3. **REQUIRED_GAP 88→66**: The change from 4-symbol to 3-symbol formula consequence is correct. `(21+1)*3 = 66`. The `combinatorial_purged_cv` assertion (`expected_gap=REQUIRED_GAP`) will verify at runtime. Engineer must confirm the constant update in `validation_v3.py` before running.

4. **V3_FEATURES_PER_SYMBOL cleanup**: Removing the LDO entry leaves the dict empty `{}`. The `features_for_symbol()` helper returns `V3_FEATURE_COLUMNS_TOP_N` for any symbol (including any hypothetical future LDO call), which is the correct fallback behavior. Architecture is preserved for future per-symbol use.

5. **V3_FEATURE_COLUMNS = 14 unchanged**: `regime_momentum_signed_5d` must remain. `_verify_feature_columns()` runtime assertion will catch any regression.
