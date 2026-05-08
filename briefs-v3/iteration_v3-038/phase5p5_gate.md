# Phase 5.5 Gate — iter-v3/038

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24 IMMUTABLE confirmed; IS/OOS windows named in absolute dates.
- Section 0.5 (Type Declaration): PASS — TYPE=EXPLORATION cadence #10/10 FINAL; single-axis per-symbol swap (revert LDO, add ALGO); wall-clock ≤2h; ANCHOR = iter-v3/035.
- Section 1 (Hypothesis): PASS — one sentence: ALGO-only fracdiff tests specificity (BCH-specific vs broadly useful); falsifier = OOS Sharpe < +2.0.
- Section 2 (IS-Only Evidence): PASS — cites iter-v3/034 per_symbol.csv (ALGO -8.24 universal drag, committed artifact), iter-v3/035 per_symbol.csv (ALGO +20.87 baseline, committed artifact). No new EDA required per brief §0.5 — prior committed scripts provide the numerical basis. Behavioral effect predictor included with explicit falsifier (IS trade delta = 0 for ALGO → INERT).
- Section 3 (Proposed Changes): PASS — 4 sub-fixes enumerated: (1) V3_FEATURES_PER_SYMBOL atomic dict swap, (2) _verify_feature_columns assertions updated, (3) ITERATION_LABEL bump, (4) adversarial tests updated. No labeling/symbol/risk-gate changes.
- Section 4 (Expected OOS Impact): PASS — IS band [-0.20, +0.20] median 0.0; OOS band [+2.50, +3.20] median +2.85 (anchor); path taxonomy A/B/C/D with explicit OOS falsifier at +2.0.
- Section 5 (Risk Mitigation): PASS — R1/R2/R3 carried forward from baseline; per-symbol heterogeneity risk noted; LDO revert risk noted; fracdiff parquet generation for all symbols noted as safe.
- Section 6 (Risk Management Design): PASS — 7-primitive gate table present with IS/OOS fire rates from iter-v3/035; no gate changes.
- Section 7 (Failure-Mode Prediction): PASS — two plausible failure modes pre-registered; gates to watch noted; scientific specificity interpretation (5-of-5 verdict) regardless of path; behavioral falsifier stated.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — EXPLORATION classification criteria (PROMISING/PROMISING-INERT/NULL-RESULT/NEGATIVE) pre-registered with locked numerical thresholds before backtest runs.
- Section 9 (Library Stack): PASS — fracdiff PyPI unavailable; pure-numpy FFD fallback confirmed in engineered_v3.py since iter-v3/034; no new dependencies; library versions pinned.

## Single-Axis Verification

ONE primary variable: atomic swap of V3_FEATURES_PER_SYMBOL (LDOUSDT removed, ALGOUSDT added with fracdiff_d05_close). V3_FEATURE_COLUMNS_TOP_N unchanged (14 features). No labeling, symbol universe, risk gate, or Optuna parameter changes. Attribution is clean: any OOS delta vs iter-v3/035 explained by (1) LDO returned to 14-feature fallback + (2) ALGO-only fracdiff_d05_close.

## Sacred Constants Verification

- OOS_CUTOFF_DATE = 2025-03-24: CONFIRMED unchanged
- training_months = 24: CONFIRMED unchanged
- ENSEMBLE_SIZE = 5 (inner): CONFIRMED unchanged (EXPLORATION uses size=1 via --exploration flag)
- REQUIRED_GAP = 88 = (21+1)×4: CONFIRMED unchanged (4 symbols, 21-candle timeout)

## Feature Column Pinning

Brief Section 3 sub-fix #2 specifies explicit per-symbol feature lists: BCH=15, ALGO=15, LDO=14, TRX=14. Runner passes `feature_columns=list(features_for_symbol(symbol))` — never None, never empty, never auto-discovered. PASS.

## Reasons (if BLOCK)

N/A — OVERALL=PASS. Phase 6 implementation authorized to proceed.
