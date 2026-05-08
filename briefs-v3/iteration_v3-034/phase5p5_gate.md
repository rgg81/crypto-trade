# Phase 5.5 Gate — iter-v3/034

OVERALL: PASS

## Per-Section Status
- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24 immutable; IS and OOS windows named in absolute dates
- Section 0.5 (Type Declaration): PASS — EXPLORATION cadence #6 of 10; single-axis (atomic swap: DROP VET + ADD fracdiff_d05_close); justified as one-variable per anchor reasoning
- Section 1 (Hypothesis): PASS — ONE sentence; specific mechanism (FFD d=0.5 preserves long-memory complementary to regime_momentum sign-flip); quantified lift target +0.10 IS Sharpe over anchor +0.2360
- Section 2 (IS-Only Evidence): PASS — LdP AFML Ch. 5 methodology fully cited; weight formula given explicitly (iterative recurrence); truncation threshold 1e-4; ADF stationarity pre-registered as falsifiable claim (p < 0.05 across all 4 symbols); complementarity argument with regime_momentum_signed_5d is structural (non-overlapping source primitives). No committed EDA script required: the brief invokes the Category 2 carve-out (computational-only, well-defined method) consistently with how iter-v3/025 regime_momentum was approved
- Section 3 (Proposed Changes): PASS — 6 enumerated sub-fixes with code snippets; DROP VET, REQUIRED_GAP 110→88 formula justified, fracdiff_d05_close implementation spec (numpy recurrence, d=0.5, truncation 1e-4, log(close)), V3_FEATURE_COLUMNS_TOP_N 14→15, _verify_feature_columns update, ITERATION_LABEL update
- Section 4 (Expected OOS Impact): PASS — IS band [+0.20, +0.55] median +0.38; OOS band [+1.60, +2.10] median +1.85; explicit OOS falsifier (OOS Sharpe < +1.0 → hypothesis rejected); Path A/B/C taxonomy
- Section 5 (Risk Mitigation): PASS — Universe risk noted (4→3 diversification); IC risk noted (fracdiff_d05_close IC with non-active fracdiff_logclose_dstat is benign); warmup-bar impact quantified (150 bars at 8h vs 2742-bar IS window); threshold calibration unchanged
- Section 6 (Risk Management Design): PASS — 7-primitive gate table with fire-rate references and explicit "no change" per gate
- Section 7 (Failure-Mode Prediction): PASS — 2 plausible failure paragraphs (PROMISING-INERT / NEGATIVE-OOS), gate triggers identified, per-symbol concentration and OOS trade-count signals named
- Section 8 (MERGE/NO-MERGE Criteria): PASS — EXPLORATION classification criteria: PROMISING (IS ≥ 0.20 AND importance ≥ 30 on ≥ 2/4 symbols AND ADF p < 0.05 all symbols) / PROMISING-INERT (importance 5-29) / NULL-RESULT (importance < 5 all) / NEGATIVE (IS < 0.10 OR OOS < 1.0 OR ADF failure); pre-registered before backtest runs
- Section 9 (Library Stack): PASS — fracdiff PyPI package UNAVAILABLE documented; pure-numpy fallback specified; scipy not required; no new dependencies; implementation location named

## Reasons
None — all 10 sections PASS.

## Notes
- The "one variable at a time" principle is satisfied: the DROP VET is a mechanical revert to the iter-v3/032 anchor (not a new experiment), and ADD fracdiff_d05_close is the single new variable measured against that anchor. This is identical in structure to the iter-v3/027 atomic-swap precedent (vol_adj_autocorr dropped, cross_asset_divergence_norm added).
- Section 2 omits a committed analysis script. The Category 2 carve-out (established in iter-v3/025 phase5p5_gate.md §IC-Gate Carve-Out and the Module docstring of engineered_v3.py) explicitly permits computational-only evidence for engineered features derived from peer-reviewed methodology. This carve-out is pre-existing policy, not a new exception.
- REQUIRED_GAP formula: (21+1) × 4 = 88. This is a pure formula application of the established v3 gap rule; no new calibration needed.
