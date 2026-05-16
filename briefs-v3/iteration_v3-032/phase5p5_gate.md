# Phase 5.5 Gate — iter-v3/032

OVERALL: PASS

## Per-Section Status
- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24 and training_months=24 declared immutable; IS/OOS absolute date windows stated; ENSEMBLE_SIZE=1 (--exploration); n_trials=35; colsample_bytree=1.0.
- Section 1 (Hypothesis): PASS — single specific sentence: per-symbol ATR multipliers for LDO (1.5, 0.75) replacing (2.0, 1.0) to align LDO's effective barrier widths with peer (BCH/TRX/ALGO) median natr; mechanism tied to LDO natr_21_raw 1.35x peer median; BCH+TRX+ALGO unchanged via dict fallback. Predicted IS/OOS bands with confidence intervals and explicit falsifiers (4 falsifiers with numerical thresholds).
- Section 2 (IS-Only Evidence): PASS — committed script `analysis/iteration_v3-032/per_symbol_atr_eda.py` at SHA `9834e84` (Phase 1, before this brief). Reads IS-window natr_21_raw + iter-v3/029 IS trades.csv only. Outputs: 5 numerical tables (per_symbol_atr_distribution.csv, per_symbol_label_outcome_pattern.csv, per_symbol_label_outcome_pattern_oos.csv, atr_multiplier_recommendation.csv, ldo_candidate_grid.csv, synthesis.md). Behavioral-effect predictor with explicit falsifier thresholds present (Section 2.4). OOS composition read informational only, NOT used in scoring.
- Section 3 (Proposed Changes): PASS — 7 enumerated sub-fixes with file paths, descriptions, and verifier commands; 8 reconciliation commands; adversarial test code included verbatim.
- Section 4 (Expected OOS Impact): PASS — PATH A/A-MARGINAL/B/C bands with IS Sharpe, OOS Sharpe, LDO OOS PnL, LDO IS trades, and interpretation; 4-row catalog framing table; median predicted OOS Sharpe band [+1.50, +2.00].
- Section 5 (Risk Mitigation): PASS — 3 categories (cadence-discipline, methodology-hygiene, axis-specific), 11 mitigations with explicit triggers.
- Section 6 (Risk Management Design): PASS — 7-primitive risk gate stack table with thresholds and UNCHANGED/DISABLED status for all primitives; gate fire-rate prediction (LDO shifts; BCH/TRX/ALGO bit-identical via fallback).
- Section 7 (Failure-Mode Prediction): PASS — 3 ranked failure modes with mechanisms, diagnostic signatures, and gate linkage. Most plausible: LDO trade-roster bit-identical (PROMISING-MECHANICAL via Falsifier 1); 2nd: LDO drag deepens (PATH B-1); 3rd: over-fitting from label-engineered trade-count expansion.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — EXPLORATION (BASELINE_V3.md never updated per iteration type). 13 numbered pre-registered criteria with PASS thresholds and FAIL verdicts; all 4 outcome dispositions pre-committed in Section 11.
- Section 9 (Library Stack): PASS — versions pinned (python 3.13, lightgbm 4.6.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, pyarrow 23.0.1, statsmodels 0.14.6, optuna 4.8.0, scipy 1.17.0); mlfinpy/pypbo unavailability declared with fallback.

## Single-Axis Discipline Check
PASS — ONE primary variable: per-symbol ATR multiplier dispatch (LDO: (1.5, 0.75); BCH+TRX+ALGO: default (2.0, 1.0) via fallback). V3_FEATURE_COLUMNS=14 BIT-IDENTICAL. V3_MODELS net unchanged at 4 (LDO restore = iter-v3/031 drop reversal). REQUIRED_GAP=88 restored (formula consequence of n_symbols=4). V3_FEATURES_PER_SYMBOL stays empty (iter-v3/030 LDO 7-feat subset NOT restored). Risk gate stack UNCHANGED.

## EDA Script Pre-Registration Check
PASS — `analysis/iteration_v3-032/per_symbol_atr_eda.py` committed at SHA `9834e84` BEFORE this brief (Phase 1 requirement per brief Section 0 preamble). Script reads IS-window only. OOS data read informational only, NOT used in candidate scoring or recommendation logic.

## Reasons (if BLOCK)
None. All 10 mandatory sections present and valid.
