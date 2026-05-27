# Phase 5.5 Gate — iter-v1/027

OVERALL: PASS

## Iteration Type (from Brief Section 0.5)
TYPE: CONFIRMATION — cycle-3 closing; 10/10 EXPLORATION precedents complete (/016-/025); /026 sanity slot (not EXPLORATION).

## (v1 only) Axis Family + Rotation Status
FAMILY: per-cohort-specialization (REPEAT — CONFIRMATION bundles /018 LINK + /019 ETH+gate)
ROTATION_STATUS: VALID — CONFIRMATIONs are exempt from Axis Rotation Discipline per v1 skill §"Iteration Cadence Discipline" Rule 4. Prior 5 EXPLORATION families verified from catalog: /022 per-cohort-specialization-LTC, /023 feature-family, /024 model-arch, /025 feature-family, /021 methodology-pivot — 5 distinct families, no monoculture.

## (v1 only) HIGH-RISK Declaration
HIGH-RISK: NO
Declaration at Section 2.5: NORMAL-RISK. Rationale: CONFIRMATION's multi-seed mandate (--seeds 2 × ENSEMBLE_SIZE=5 = 10 paths/cell) is the OPPOSITE of single-seed lottery exposure; HIGH-RISK classification attaches to single-seed EXPLORATION Optuna domain changes, not CONFIRMATION multi-seed runs. Cumulative ≥1σ negative count = 5 (tripped multi-seed mandate PRIOR to /027; multi-seed is mandatory, not opt-in).

## (v1 only) LM Master Response Verification
- briefs-v1/iteration_v1-027/lgbm_advisor.md exists: PASS (HEAD 73663a8; 9 numbered sections)
- Brief Section 3.4 addresses each LM Master recommendation: PASS
  - §1 Multi-seed regression magnitudes: ADOPTED (C' +0.78 / G +0.52 modal; F-AXIS #3 bands updated)
  - §2 Cross-correlation at multi-seed: ADOPTED (pool×LINK dissolves; C×E stays; Section 11 C×E de-concentration MANDATORY)
  - §3 Bundle composition stability: ADOPTED (specialist_stability.csv added to Section 10.5)
  - §4 DSR borderline: ADOPTED (F-AXIS #4 calibration note added; DSR modal +0.45 < 0.50 threshold acknowledged)
  - §5 F-AXIS #1 dispatch hard-asserts MANDATE: ADOPTED (3 runtime asserts in Section 3.1; replacement_filter_audit.csv in Section 10.5)
  - §6 Verdict priors recalibrated 30/35/25/6/4: ADOPTED (Section 5 replaced; modal shifts to INERT 35%)
  - §7 Structural ceiling at +0.50 (LTC drag + C×E concentration): ADOPTED (Section 1 and 11 amended)
  - §8 --seeds 2 budget defensible: ADOPTED (validates Section 3.2 CLI invocation unchanged)
  - §9 /028+ D-specialist MANDATORY regardless of verdict: ADOPTED (Section 11.1/11.2/11.3 all converge on unconditional D-specialist priority)

## Cadence Check (v1/v3)
- Wall-clock budget declared: 6h HARD CAP (CONFIRMATION standard); Section 3.6 documents [4.5h, 5.5h] modal with parallel dispatch / [5.9h, 6.5h] fallback at --seeds 1; kill threshold 6.5h: PASS
- CONFIRMATION: EXPLORATION precedents since last CONFIRMATION: 10 (/016-/025; /026 is SANITY slot not counted as EXPLORATION): PASS (≥10 required)
- CONFIRMATION: Section 3 lists imported variations from prior EXPLORATIONs: PASS
  - Model C' (LINK specialist) from /018 PROMISING-INERT favorable (+0.98 OOS)
  - Model G (ETH+gate specialist) from /019 PROMISING (+0.70 OOS)
  - REPLACEMENT SEMANTICS (not additive) per /025 brief §11.6 LOCKED + /026 GREEN-WITH-FIX

## Per-Section Status
- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE = 2025-03-24 confirmed; training_months = 24 confirmed; IS window described; OOS window described
- Section 0.5 (Iteration Type): PASS — TYPE: CONFIRMATION declared; cycle-3 closing; 10/10 EXPLORATION precedents complete; 11th iteration (/016-/027: 10 EXPLORATION + /026 sanity + /027 CONFIRMATION)
- Section 0.6 (Architecture-Family Justification): PASS — family per-cohort-specialization REPEAT; CONFIRMATION exempt from rotation; prior 5 EXPLORATION families verified; one-sentence rationale present
- Section 1 (Hypothesis): PASS — specific, quantified: H1 multi-seed mean OOS Sharpe Δ vs anchor +0.6637 ∈ [+0.10, +0.40]; NO-MERGE pre-committed per H2; falsification logic enumerated for each verdict cell; LM Master §7 structural ceiling adopted
- Section 2 (IS-Only Evidence): PASS — committed analysis scripts present (analysis/iteration_v1-026/bundle_replacement_validation.csv, analysis/iteration_v1-026/replacement_pool_correlation.csv); cycle-3 ledger 10/10 with concrete OOS Sharpe numbers; per-specialist standalone results from /018 + /019 comparison.csv; multi-seed regression priors from /018 + /019 LM Master Phase 7.4; /026 single-seed reference bundle table
- Section 2.5 (HIGH-RISK Axis Declaration): PASS — NORMAL-RISK declared; rationale present; cumulative HIGH-RISK tracker 8/8 EXPLORATION history listed; multi-seed mandate trigger documented (≥1σ NEG count = 5)
- Section 3 (Proposed Changes): PASS — 5-model bundle enumerated with cohort / source / risk gates / ATR / origin EXPLORATION; replacement semantics defined; implementation pseudocode (run_model calls × 5, BTC-trend gate application, replacement filter); CLI invocation; pinned values; LM Master responses (Section 3.4 complete); wall-clock estimate (Section 3.6) — NOTE: Section 3.3 declares "40 cols" for V1_FEATURE_COLUMNS_PRUNED but current constant has 43 cols (includes funding /023 + OI /025 NEGATIVE variants). Brief explicitly states "NOT 42, NOT 43; OI and funding EXCLUDED from /027 substrate per /025 + /023 NEGATIVE verdicts." QE must implement a 40-col subset (strip funding_rate_zscore_30, funding_rate_zscore_90, oi_delta_30_z90 from the 43-col constant) — this is unambiguous in intent; implementation derivable from brief. PASS-WITH-NOTE (not a BLOCK; brief provides sufficient specificity).
- Section 4 (Expected OOS Impact): PASS — F1-F8 + F-AXIS-MECHANISM #1-5 all present; absolute OOS Sharpe band [+0.40, +0.75]; Δ bands per verdict cell; IS Sharpe band; F3 IS-CAT auto-reject lever; trade count band; per-specialist bands (C' [+0.50, +0.80]; G [+0.30, +0.50]); cross-correlation predictions; DSR/PBO/PSR bands; MaxDD band; wall-clock band
- Section 5 (Risk Mitigation): PASS — predicted verdict distribution present (30/35/25/6/4 per LM Master recalibration); rationale per cell
- Section 6 (Risk Management Design): PASS — 6 failure modes documented (multi-seed regression; cross-correlation drift; MaxDD blowout; F-AXIS #1 dispatch error; wall-clock cap breach; LTC drag dominance); each with built-in mitigation
- Section 7 (Failure-Mode Prediction): PASS — 13 pre-registered predictions with bands; forward-looking (binding at Phase 7 per brief §"Binding predictions for Phase 7 evaluation"); verdict cell predictions aligned to F-axis bands
- Section 8 (MERGE/NO-MERGE Criteria): PASS — NO-MERGE PRE-COMMITTED at brief authoring; explicit reasoning (target band structurally below +1.0 IS/OOS floors; IS modal far below +1.0); BASELINE_V1.md UNCHANGED declared; outcome routing table (PROMISING-METHODOLOGY / INERT / NEGATIVE / NEGATIVE-BELOW-BAND / BLOCK all map to NO-MERGE); tag v0.v1-027 noted for diary only
- Section 9 (Library Stack): PASS — declared: mlfinlab==1.4, pypbo, lightgbm, optuna, numpy/pandas/scikit-learn; no new dependencies; existing imports documented (risk_v2 BTC-trend gate; validation_v1 DSR/PSR; optimization Optuna; walk_forward fixed embargo)

## CONFIRMATION-Specific Additional Checks
- EXPLORATION precedents since last CONFIRMATION: 10 (/016-/025). PASS.
- Section 3 lists EXPLORATION variations imported: PASS. C' from /018; G from /019. REPLACEMENT (not additive) semantics declared. /026 cross-correlation sanity precondition PASS documented.
- NO-MERGE pre-committed with locked numerical justification: PASS. Absolute band [+0.40, +0.75] structurally below +1.0 IS/OOS merge floors. Not rationalized post-hoc.
- Prior 10 EXPLORATIONs include ≥2 PROMISING: PASS. /018 PROMISING-INERT favorable (+0.98); /019 PROMISING (+0.70).

## Implementation Note for QE (Section 3.3 disambiguation)
Brief §3.3 explicitly states 40 cols for /027 substrate (BASELINE-FROZEN, excluding funding /023 + OI /025 NEGATIVE-variant features). Current V1_FEATURE_COLUMNS_PRUNED has 43 cols. QE MUST define a local 40-col subset in the runner dispatch branch by dropping: funding_rate_zscore_30, funding_rate_zscore_90, oi_delta_30_z90. This is unambiguous in brief intent; implement as:
```python
_V1_ITER027_FEATURE_COLUMNS_40: tuple[str, ...] = tuple(
    c for c in V1_FEATURE_COLUMNS_PRUNED
    if c not in {"funding_rate_zscore_30", "funding_rate_zscore_90", "oi_delta_30_z90"}
)
assert len(_V1_ITER027_FEATURE_COLUMNS_40) == 40, f"Expected 40, got {len(_V1_ITER027_FEATURE_COLUMNS_40)}"
```
Pass list(_V1_ITER027_FEATURE_COLUMNS_40) as feature_columns= to all 5 run_model() calls.

## Reasons
No BLOCKs. All 9 mandatory sections present and valid. LM Master §1-§9 all adopted in Section 3.4. Cadence: 10 EXPLORATION precedents complete. CONFIRMATION exempt from rotation discipline. Feature column count disambiguation noted as implementation note (not a BLOCK — brief provides sufficient specificity to implement correctly). Wall-clock cap risk acknowledged in brief §3.6 with mitigation options; parallel dispatch or --seeds 1 fallback declared.
