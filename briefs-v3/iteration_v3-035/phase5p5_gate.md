# Phase 5.5 Gate — iter-v3/035

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24 and training_months=24 declared
  immutable; IS/OOS windows stated in absolute dates.
- Section 0.5 (Iteration Type): PASS — EXPLORATION cadence #7 of 10; single-axis per-symbol
  feature targeting; atomic operation documented and justified.
- Section 1 (Hypothesis): PASS — one sentence; specific (BCH-only fracdiff preserves +37.98
  OOS swing while restoring TRX/ALGO/LDO regressions); falsifiable.
- Section 2 (IS-Only Evidence): PASS — numerical tables from
  reports-v3/iteration_v3-034/out_of_sample/per_symbol.csv and
  reports-v3/iteration_v3-032/out_of_sample/per_symbol.csv (committed; reproducible).
  Per-symbol swing table with specific numbers. Behavioral effect predictor included per
  feedback_v3_axis_saturation_predictor.md requirement.
- Section 3 (Proposed Changes): PASS — 7 sub-fixes enumerated with exact assertions;
  feature column count changes documented (14 universal, 15 for BCH); ITERATION_LABEL change
  specified; adversarial test specification complete.
- Section 4 (Expected OOS Impact): PASS — predicted bands [+0.30, +0.70] IS and [+1.70, +2.20]
  OOS with explicit falsifier (OOS Sharpe < +1.0 rejects hypothesis). Path taxonomy A/B/C
  specified.
- Section 5 (Risk Mitigation): PASS — per-symbol feature heterogeneity risk documented; pipeline
  safety analysis (fracdiff generated for all but only passed to BCH explicitly); concentration
  risk noted.
- Section 6 (Risk Management Design): PASS — 7-primitive gate table present; all gates
  explicitly stated as unchanged from iter-v3/032 baseline.
- Section 7 (Failure-Mode Prediction): PASS — two failure modes predicted with specific
  metric signals; behavioral effect predictor included (BCH IS trade change ±5-15%;
  TRX/ALGO/LDO = 0 trade change); falsifier for contamination included.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — EXPLORATION classification criteria pre-registered:
  PROMISING (4 explicit numerical gates), PROMISING-INERT, NULL-RESULT, NEGATIVE (4 explicit
  conditions). No post-hoc rationalization possible.
- Section 9 (Library Stack): PASS — fracdiff PyPI unavailability documented with same
  constraint as iter-v3/034; pure-numpy fallback declared; no new dependencies required;
  implementation already exists in engineered_v3.py from iter-v3/034.

## Reasons

No blockers. All 10 mandatory sections present and complete.

## Implementation Notes (for Phase 6)

1. Only `features_v3/__init__.py` and `run_baseline_v3.py` require code changes.
   `engineered_v3.py` is unchanged (fracdiff_d05_close already implemented).
2. V3_FEATURES_PER_SYMBOL invariant changes: BCH entry EXTENDS V3_FEATURE_COLUMNS_TOP_N
   (not a strict subset). `_verify_feature_columns` must reflect this correctly.
3. Adversarial tests must replace the current iter-v3/034 assertions (which test all symbols
   return 15 features and V3_FEATURES_PER_SYMBOL is empty) with iter-v3/035 assertions
   (BCH=15 with fracdiff; TRX/ALGO/LDO=14 without fracdiff; dict has 1 entry).
4. REQUIRED_GAP remains 88 = (21+1)*4 (4 symbols, unchanged from iter-v3/034).
5. Pre-flight verification commands:
   - `grep -nE 'ITERATION_LABEL = "v3-035"' run_baseline_v3.py`
   - `uv run python -c "from crypto_trade.features_v3 import features_for_symbol, V3_FEATURE_COLUMNS_TOP_N; bch = features_for_symbol('BCHUSDT'); trx = features_for_symbol('TRXUSDT'); assert len(bch) == 15 and 'fracdiff_d05_close' in bch and len(trx) == 14 and 'fracdiff_d05_close' not in trx"`
   - `uv run pytest tests/`
