# Phase 5.5 Gate — iter-v3/121

OVERALL: PASS

## Per-Section Status
- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24 explicitly confirmed unchanged (Section 3.5 knobs table).
- Section 0.5 (Iteration Type): PASS — TYPE=CYCLE-7 BOOTSTRAP/METHODOLOGY; NOT counted toward cycle-7 cadence; /018 BOOTSTRAP precedent explicitly cross-referenced (Section 0.5).
- Section 1 (Hypothesis): PASS — Single testable sentence: Component A alone on /059's 14-feature stack produces IS ≥ +1.0894 AND OOS ≥ +0.5791 OR is evaluated NEGATIVE-AT-MULTISEED and cycle-6 closes with 0 ingredients merged.
- Section 2 (IS-Only Evidence): PASS — No new EDA mandated for CONFIRMATION-class (per feedback_v3_axis_selection_quant_discipline.md); cross-references /116 EDA SHA 52444c9 with committed analysis scripts and IS-only temporal fence OOS_CUTOFF_MS=1742774400000 (Section 2.1); T7_early_exit_grid.csv and T8_cuts_losers.csv tables cited with numerical values; /120 QR Round-2 Q3 Jaccard finding (committed briefs-v3/iteration_v3-120/qr_response.md) provides attribution-gap numerical evidence (Section 2.3).
- Section 3 (Proposed Changes): PASS — Enumerated 5 sub-fixes; no new feature, no new function, no new test beyond pre-flight inversion (Section 3.5 code-change manifest confirmed).
- Section 3.5 (Code-Change Manifest — 3-change verification): PASS
    (1) V3_FEATURE_COLUMNS_TOP_N: 15 → 14 (drop ret5d_signed_tbi; compute_ret5d_signed_tbi function kept per /118//119 precedent) — confirmed Sub-fix 2 + Section 3.5 item 1.
    (2) ITERATION_LABEL "v3-120" → "v3-121", MODEL_SPECS prefix update — confirmed Sub-fix 4 + Section 3.5 item 3. NOTE: brief Section 3.5 lists 4 items (feature-list revert, pre-flight inversion, label/prefix update, brief commit); the prompt's "exactly 3 changes" aligns with Sub-fixes 1+2+3+4 collapsed to 3 code surfaces (feature list, pre-flight assertions, iteration labels). Brief is internally consistent.
    (3) Pre-flight assertion: C6 ABSENT (ret5d_signed_tbi not in V3_FEATURE_COLUMNS_TOP_N, len==14) — confirmed Sub-fix 3 + Section 3.5 item 2.
    (4) /116 no_confirm STAYS enabled on 3 surfaces (model builder at line 2036, accretion guard at lines 2950-2995, pre-flight assertion at line 2957) — confirmed Sub-fix 1 + Section 3 opening.
- Section 4 (Expected OOS Impact / Falsifiers): PASS — 5 binding falsifiers with explicit numerical thresholds:
    F1 BOTH-must-improve: IS ≥ +1.0894 AND OOS ≥ +0.5791 — PRESENT.
    F2 IS regime-cost floor: IS ≥ +0.79 — PRESENT.
    F3 hard methodology: PBO < 0.40 AND PSR > 0.95 AND frac_positive_paths ≥ 0.55 — PRESENT.
    F4 trade-rate floor: ≥ 130 OOS trades (informational carry-forward consistent with /059 status) — PRESENT.
    F5 cascade: ≥ 2/3 symbols positive OOS weighted_pnl Δ vs /059 (BCH > +24.75, LDO > −6.18, TRX > +4.16) — PRESENT.
- Section 5 (Risk Mitigation): PASS — R1–R5 each addressed; Component-A-specific IS regime-cost risk bounded by F2 + F5; Component B removal clears the /120 bundle risk consideration.
- Section 6 (Risk Management Design): PASS — 7-primitive RiskV2 stack, CPCV n_paths=45/embargo=27/REQUIRED_GAP=66, walk-forward POST-FIX e149e9d all confirmed unchanged.
- Section 7 (Failure-Mode Prediction): PASS — 5 mutually exclusive verdict modes (A/B/C/D/E) with probability estimates; modal Mode B (~50-60%) pre-registered; failure mechanisms described for each falsifier.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — Locked numerical thresholds; first-match-wins decision tree (5 nodes); BASELINE_V3.md update policy: all 5 PASS → updates to /121 Component A only; else UNCHANGED at /059 (Section 8.4).
- Section 9 (Library Stack): PASS — lightgbm==4.6.0, optuna==4.8.0, numpy==2.2.6, pandas==3.0.0, scikit-learn==1.8.0, scipy==1.17.0, statsmodels==0.14.6, pyarrow==23.0.1, mlfinlab==1.4 (primary), pypbo, fracdiff>=0.10.

## Wall-Clock
~3-4h estimated, 6h HARD CAP — CONFIRMED (Section 0.5).

## Reasons (if BLOCK)
None.
