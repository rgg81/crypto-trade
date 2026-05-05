# Phase 5.5 Gate — iter-v3/002

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS
- Section 1 (Hypothesis): PASS
- Section 2 (IS-Only Evidence): PASS — committed script: `analysis/iteration_v3-002/methodology_diagnostics.py` at SHA `1f10ce7` (before brief at SHA `fbd853f`)
- Section 3 (Proposed Changes): PASS — includes reconciliation table at Section 3.7 (Critic Rec #1)
- Section 4 (Expected OOS Impact): PASS
- Section 5 (Risk Mitigation): PASS
- Section 6 (Risk Management Design): PASS
- Section 7 (Failure-Mode Prediction): PASS
- Section 8 (MERGE/NO-MERGE Criteria): PASS — criterion #17 `sign(IS_Sharpe) == sign(OOS_Sharpe)` present (Critic Rec #3)
- Section 9 (Library Stack): PASS

## Per-Section Detail

### Section 0 — Data Split
- `OOS_CUTOFF_DATE = 2025-03-24`: confirmed unchanged
- `training_months = 24`: confirmed unchanged
- `ensemble_seeds = [42, 123, 456, 789, 1001]`: confirmed unchanged
- IS window: symbol first usable kline (with listing-date floor 2022-09-24) through 2025-03-23 23:59:59 UTC exclusive
- OOS window: 2025-03-24 00:00:00 UTC through data-extent timestamp at backtest time
- Walk-forward unit and CPCV unit (N=10, k=2, 45 paths) with corrected purge gap formula stated explicitly: `(21+1) × 4 = 88 candles`
- PASS

### Section 1 — Hypothesis
- One specific, testable sentence: "Re-implementing CPCV/PBO/PSR per AFML Ch. 12 + CSCV with adversarial unit tests, fixing the embargo-rescaling silent bug, and computing per-(symbol, feature) ADF will produce statistically valid PBO/DSR/PSR/ADF on the same iter-v3/001 dataset, where the corrected PBO on iter-v3/001's path matrix should land in [0.40, 0.60] (chance baseline) rather than the buggy 0.0."
- Not vague ("explore methodology") — specifies which algorithms are repaired, the exact dataset, and the expected numerical range
- Falsifiers given in Section 4.3 (primary, secondary, tertiary)
- PASS

### Section 2 — IS-Only Numerical Evidence
- Script `analysis/iteration_v3-002/methodology_diagnostics.py` committed at SHA `1f10ce7` BEFORE the brief at SHA `fbd853f` — reproducibility requirement met
- Five CSV outputs committed alongside the script: `pbo_diagnostic.csv`, `dsr_diagnostic.csv`, `adf_per_symbol_demo.csv`, `path_sharpe_descriptive.csv`, `synthesis.md`
- `pbo_diagnostic.csv` verified: 5 test cases with numerical buggy_pbo (always 0.0) vs corrected_pbo (0.31 for A2, 0.86 for B, 0.0 for C, 0.66 for D, NaN for A) — discriminates overfit/clean/random as claimed
- `dsr_diagnostic.csv` verified: 12 rows; buggy=0.0 on negative SR, corrected returns 1.62e-24 (informative, non-clamped) — demonstrates the clamp failure
- `adf_per_symbol_demo.csv` verified: LDOUSDT `cusum_reset_count_200` p=0.0707 (FAIL) masked to 0.0178 by averaging — the key ADF-averaging-bias demonstration is present
- All tables use IS-data-only (IS mask applied via `ts < OOS_CUTOFF` in the ADF function; PBO/DSR diagnostics are synthetic or reading IS report data)
- No category-matching; all evidence is numerical
- PASS

### Section 3 — Proposed Changes
- **Symbols (3.1)**: BCH+MKR+LDO+TRX unchanged; `set({BCH, MKR, LDO, TRX}) ∩ V3_EXCLUDED_SYMBOLS = ∅` explicitly stated
- **Labeling (3.2)**: triple-barrier params stated (tp=2.9×NATR_21, sl=1.45×NATR_21, timeout=21 candles); NO meta-labeling confirmed; purge gap formula restated
- **Features (3.3)**: V3_FEATURE_COLUMNS (34 cols) unchanged; no cluster-importance check needed (no additions)
- **Risk gates (3.4)**: explicit table of 10 gate states with rationale; R1/R2/R3 explicitly dropped with deferred-to notation; v2 5-gate + BTC as the spec
- **Methodology stack (3.5)**: 5 fixes in numbered table with explicit "Engineer-side implementation" column naming specific files and functions
- **Adversarial unit tests (3.6)**: 3 test files with explicit assert specifications
- **Brief-vs-code reconciliation table (3.7, Critic Rec #1)**: PRESENT — 8 rows covering every Section 3 promise; each row has "Code path implementing this" and "Engineer verification step" columns; cells in the right columns are explicitly specified (not empty — they contain implementation targets for Engineer to fill/verify); table structure meets the Phase 5.5 new requirement
- PASS

**Note on reconciliation table cells**: The brief's reconciliation table correctly pre-fills the right two columns with Engineer-side specifications (file paths, function names, CLI verification commands). The Phase 5.5 spec requires the table's PRESENCE and row-by-row coverage — not that the Engineer has already filled implementation artifacts (Phase 6 hasn't happened yet). All 8 rows have explicit non-empty "Code path" and "Engineer verification step" cells. PASS.

### Section 4 — Expected OOS Impact
- Table of 9 metrics with iter-v3/001 vs iter-v3/002 predictions and Δ
- Primary falsifier: corrected PBO < 0.4 still is a FAIL; NaN (S=1) is acceptable and strictly stronger
- Secondary falsifier: per-(symbol, feature, month) ADF that does not surface LDO `cusum_reset_count_200` p ≥ 0.05 in at least one month = still averaging
- Tertiary falsifier: any of 3 adversarial unit tests fails = iteration cannot ship
- Expected OOS MERGE outcome explicitly predicted as NO-MERGE on headline metrics; "the iteration's success is measured by 6 checkpoints" explicitly stated
- PASS

### Section 5 — Risk Mitigation
- v2 5-gate + BTC inherited with references to specific prior iterations (v2 iter-v2/059/069, iter-v2/019)
- IS-calibrated: states thresholds inherited from v2 without re-tuning, with reference iter
- Simulated effect: references iter-v3/001's kill rate 69–78% as expected continuation
- No new risk gates: explicit enumeration with rationale and deferred-to notation for R1/R2/R3
- Three methodology-pipeline safeguards named as the iteration's actual risk mitigation
- PASS

### Section 6 — Risk Management Design
- 7-primitive table with Spec, Fire-rate prediction (IS), and Regime coverage columns
- Regime coverage analysis: IS window, crypto regimes 2020-2025 named
- Concentration acknowledged as expected failure (Section 6.3: MKR at 50–60% expected)
- Hit-rate feedback gate explicitly DISABLED with reference to iter-v2/045 lesson
- PASS

### Section 7 — Pre-Registered Failure-Mode Prediction
- 5 predictions: 2 process-level (Prediction 1: ADF dropped by Engineer; Prediction 2: CPCV wall-clock > 24h) and 3 model-level
- Per the iter-v3/001 diary's lesson ("future Section 7s must include at least one process-level prediction"), this is explicitly addressed
- Each prediction includes probability estimate, detection signal, and mitigation
- Forward-looking (not post-hoc); Phase 8 diary will verify calibration
- PASS

### Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria
- 19 criteria in locked numerical table
- Criterion #17 `sign(IS_Sharpe) == sign(OOS_Sharpe) = True` as a hard merge precondition: PRESENT (Critic Rec #3 requirement)
- Criterion #18 adversarial unit tests pass in CI: PRESENT (Critic Rec #2 structural requirement)
- Criterion #19 brief-vs-code reconciliation table has no empty cells: PRESENT (Critic Rec #1 requirement)
- NO-MERGE clause is explicit with 4 additional automatic triggers
- Discretionary split-merge clause documented with explicit conditions (criteria 13, 18, 19 must all pass)
- PASS

### Section 9 — Library Stack
- No new third-party dependencies introduced (explicit)
- All 6 libraries listed with license and usage: numpy, scipy, statsmodels, scikit-learn, lightgbm, pytest — all "already installed"
- Fallback rationale: references iter-v3/001's audit that mlfinpy/pypbo/fracdiff are unavailable on Python 3.13; iter-v3/002 uses pure-Python implementations from iter-v3/001's validation_v3.py
- Reproducibility stamp spec listed (what the Engineer's Phase 6 report must include)
- PASS

## New Phase 5.5 Requirements (per Critic Recommendations #1 and #3)

### Brief-vs-Code Reconciliation Table (Critic Rec #1)
- Location: Section 3.7
- Coverage: 8 rows covering every Section 3 architectural promise
  - 3.5#1 — PBO algorithm → `validation_v3.py:pbo_from_cpcv`
  - 3.5#2 — CPCV scope on candle sequence → `validation_v3.py:combinatorial_purged_cv` + `run_baseline_v3.py:_compute_cpcv_paths`
  - 3.5#3 — Embargo-gap assertion → `validation_v3.py:combinatorial_purged_cv`
  - 3.5#4 — Per-(sym, feat, month) ADF → `run_baseline_v3.py` + `adf_test.csv`
  - 3.5#5 — DSR + n_eff_trials → `validation_v2/v3.deflated_sharpe_ratio` + `validation_v3.n_effective_trials`
  - 3.4 — v2 5-gate + BTC config → `run_baseline_v3.py:_build_v3_model`
  - 3.3 — V3_FEATURE_COLUMNS unchanged → `features_v3/__init__.py:V3_FEATURE_COLUMNS`
  - 3.2 — same triple-barrier params → `BacktestConfig` in `_build_v3_model`
- Engineer verification step column present for every row (pytest command or grep or runtime assertion)
- Engineer instructions present: "Empty rows = Phase 6 cannot proceed"
- STATUS: PRESENT — PASS

### Sign-Flip Merge Precondition (Critic Rec #3)
- Location: Section 8, criterion #17
- Exact text: "sign(IS Sharpe) == sign(OOS Sharpe) — True — NEW: regime-mismatch precondition (per Critic Recommendation #3)"
- Listed as a hard MERGE requirement (#17 of 19 criteria)
- Also listed in the NO-MERGE trigger list: "Any of the 19 criteria fails"
- Also referenced in Section 5.3 ("Sign-flip precondition") as one of three structural safeguards
- STATUS: PRESENT — PASS

## Reasons (if BLOCK)

N/A — OVERALL is PASS.

## Gate Summary

All 10 mandatory sections verified PASS. Both new Phase 5.5 requirements (brief-vs-code reconciliation table per Critic Rec #1; sign-flip merge precondition per Critic Rec #3) verified PASS. The analysis script was committed before the brief (SHA `1f10ce7` < SHA `fbd853f`) — reproducibility requirement met.

Phase 6 may proceed. The Engineer must:
1. Fill the right-column cells of the Section 3.7 reconciliation table ROW BY ROW as code is written — any row left empty = Phase 6 cannot conclude
2. Implement and pass all 3 adversarial unit tests (Section 3.6) before running the backtest
3. Verify `len(V3_FEATURE_COLUMNS) == 34` runtime assertion at runner startup
4. Assert `gap == (timeout_candles + 1) × n_symbols = 88` at runner startup AND inside `combinatorial_purged_cv`
5. Verify `adf_test.csv` row count == `n_symbols × n_features × n_retrain_months` at run completion
