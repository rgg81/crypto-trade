# Phase 5.5 Gate — iter-v3/039

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24 confirmed
  immutable; IS window 2023-03-24 to 2025-03-23 and OOS window 2025-03-24 onward named
  in absolute dates.
- Section 0.5 (Type Declaration): PASS — TYPE=CONFIRMATION explicitly declared; 10/10
  EXPLORATIONs complete (iter-v3/029–038); 6h hard cap stated; runner spec `--seeds 2`
  with ENSEMBLE_SIZE=5, n_trials=35, colsample_bytree Optuna-tunable.
- Section 1 (Hypothesis): PASS — ONE sentence: iter-v3/035 single-seed OOS +2.85 compresses
  to multi-seed mean >= +1.0 at `--seeds 2`, clearing the +1.0 floor for the first time in
  v3 history. Specific numerical threshold stated. Falsifier pre-committed.
- Section 2 (IS-Only Numerical Evidence): PASS — Tables from committed analysis script
  `analysis/iteration_v3-039/is_pbo_strategy_axis_analysis.py` (SHA 9294855 committed
  before this brief). iter-v3/035 comparison.csv metrics tabulated verbatim. iter-v3/028
  multi-seed compression precedent (42% IS / 59% OOS) cited with numbers. Per-symbol OOS
  attribution table included. No category-matching — all numbers sourced from committed
  artifacts.
- Section 3 (Proposed Changes): PASS — Single enumerated sub-fix: remove ALGOUSDT from
  V3_FEATURES_PER_SYMBOL (revert iter-v3/038 ALGO fracdiff entry). Plus docstring + test
  updates + ITERATION_LABEL change. All changes are a logically atomic revert to
  iter-v3/035 bundle state.
- Section 4 (Expected OOS Impact): PASS — Predicted Sharpe delta with CI: OOS [+1.10, +1.70]
  median +1.40; IS [+0.20, +0.70] median +0.45. Explicit OOS falsifier: if OOS < +1.0 the
  +1.0 floor is not cleared; if OOS <= 0.51 hypothesis FALSIFIED entirely. Path taxonomy
  A/B/C pre-registered.
- Section 5 (Risk Mitigation): PASS — R1/R2/R3 gates stated unchanged. Multi-seed variance
  risk discussed with quantitative BCH concentration threshold (>60% = anomaly flag).
  IS/OOS Sharpe divergence resolution rationale present.
- Section 6 (Risk Management Design): PASS — 7-primitive gate table present with fire rates
  from iter-v3/035 single-seed. All 7 gates listed with parameters and fire-rate columns.
  iter-v3/035 btc_killed=43 noted. No gate changes.
- Section 7 (Failure-Mode Prediction): PASS — Two plausible failure modes described
  forward-looking: (1) COMPRESSION-WIPEOUT driven by IS/OOS regime divergence; (2) BELOW-
  FLOOR with IS lift. Specific metric to watch named: BCH fracdiff importance rank in BCH
  model. Behavioral effect predictor included with falsifier (> 30 IS trade change vs
  iter-v3/035 anchor triggers investigation).
- Section 8 (MERGE/NO-MERGE Criteria): PASS — 10 gate table with thresholds, sources, and
  priority classification. MERGE/MERGE-NO-FLOOR/NO-MERGE logic pre-committed in pseudocode.
  Quantitative "strictly better than iter-v3/028" thresholds locked: OOS > +0.5053 AND
  IS > 0.0.
- Section 9 (Library Stack): PASS — All 9 package versions listed with pyproject.toml pins.
  fracdiff PyPI unavailability and pure-numpy fallback explicitly declared (same constraint
  as iter-v3/034/035).

## CONFIRMATION-Mode Additional Checks

- One primary variable: PASS — Single change is ALGO entry removal from V3_FEATURES_PER_SYMBOL
  (revert to iter-v3/035 bundle). All other bundle settings unchanged.
- 10 EXPLORATION precedents satisfied: PASS — iter-v3/029 through iter-v3/038 = 10
  EXPLORATIONs in this cycle.
- Bundle ingredients all have EXPLORATION backing: PASS — regime_momentum_signed_5d
  (iter-v3/025 PROMISING + iter-v3/028 CONFIRMED); LDO ATR tuning (iter-v3/032 PROMISING);
  ALGO universe (iter-v3/032 PROMISING as part of 4-sym anchor); BCH fracdiff (iter-v3/035
  PROMISING).
- Section 8 MERGE gates table: PASS — 10 gates with pre-committed decision logic.

## Reasons (if BLOCK)

N/A — OVERALL=PASS.
