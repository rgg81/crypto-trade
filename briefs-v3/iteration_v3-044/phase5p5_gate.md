# Phase 5.5 Gate — iter-v3/044

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24, IS/OOS windows in absolute dates stated (2023-03-24 through 2025-03-23 IS; 2025-03-24+ OOS), OOS_CUTOFF_MS=1742774400000 declared. Sacred constants UNCHANGED.
- Section 0.5 (Iteration Type): PASS — TYPE=EXPLORATION, Cycle 3 #5 of 10, wall-clock <= 2h, spec `--seeds 1` LightGBM. Two-part axis clearly enumerated: PART A (ER revert already at code level) + PART B (add regime_momentum_signed_3d). Net feature count 15 stated. Predicted classification PROMISING with rationale.
- Section 1 (Hypothesis): PASS — ONE sentence. Specific: 3-bar variant of proven sign-flip mechanism captures shorter-horizon (1-day) regime persistence, complementing the 5-bar variant. Mechanism named (different lookback horizon adds complementary signal). Falsifier implied by Path C threshold (OOS < +1.55).
- Section 2 (IS-Only Evidence): PASS — Numerical tables from committed artifacts: iter-v3/028 BASELINE_V3.md multi-seed IS/OOS lift table (+0.1313 IS Sharpe, +0.1184 OOS Sharpe from 5d variant addition), iter-v3/025 portfolio importance rank 1 at 51%. Behavioral-effect predictor present with falsifier (< 5% trade count delta; > 20% triggers investigation). Sources are committed IS-fold data only. No category-matching.
- Section 3 (Proposed Changes): PASS — 5 sub-fixes enumerated: (1) formalize ER revert, (2) add regime_momentum_signed_3d to V3_FEATURE_COLUMNS_TOP_N (14 → 15), (3) implement compute_regime_momentum_signed_3d in engineered_v3.py with past-only proof, (4) update _verify_feature_columns for 15-feature assertions, (5) ITERATION_LABEL v3-044 (already set). Bundle state verification table present with all 15 assertions.
- Section 4 (Expected OOS Impact): PASS — Predicted bands tabulated (IS [+0.55, +1.05] median +0.80; OOS [+1.50, +2.10] median +1.80). Explicit falsifier stated (OOS < +1.55 → NEGATIVE → drop 3d at iter-v3/045). Three classification paths (PROMISING/PROMISING-INERT/NEGATIVE) with locked thresholds.
- Section 5 (Risk Mitigation): PASS — R1/R2/R3 explicitly addressed. IS-calibrated thresholds (ADX 20.0, z-score 2.0, BTC trend 15.0) stated unchanged from iter-v3/040 baseline. OOD 15-feature space expansion impact bounded. IS trade-rate stability addressed with falsifier.
- Section 6 (Risk Management Design): PASS — 7-primitive table with config, enabled/disabled status for each gate. OOD fire-rate prediction bounded (±10% vs iter-v3/040). Regime coverage noted across 4 symbols.
- Section 7 (Failure-Mode Prediction): PASS — Three forward-looking failure-mode paragraphs: (1) 3d redundant with 5d at 8h cadence (INERT), (2) PROMISING-INERT via parsimony-neutral outcome, (3) concentration shift toward TRX. Diagnostic indicators stated (feature importance rank, IS/OOS ratio). What gates should catch noted.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — Pre-registered EXPLORATION outcome classification (PATH A PROMISING / PATH B PROMISING-INERT / PATH C NEGATIVE) with numerical thresholds. Locked before backtest with explicit no-post-hoc-renegotiation statement. Non-applicable MERGE criteria correctly noted (EXPLORATION spec).
- Section 9 (Library Stack): PASS — All 8 library versions pinned. No new libraries introduced. regime_momentum_signed_3d uses only pandas/numpy built-ins. No mlfinlab/mlfinpy/pypbo/fracdiff dependencies. No license risk. No fallbacks needed.

## One-Variable Check

Single primary variable: regime_momentum_signed_3d (3-bar variant of proven sign-flip mechanism).
The efficiency_ratio_50 REVERT is a pre-condition restoration (removing iter-v3/043's DISASTROUS
addition that was already applied at code level before this brief was written) — same classification
as prior pre-condition reverts (iter-v3/016 tbr_zscore_30 drop, iter-v3/042 ret_skew_50/sym_vs_btc/
regime_momentum restore). ITERATION_LABEL update is cosmetic. PASS.

## Track Isolation

Not run here (Engineering Phase 6 check). Will be verified in pre-flight.

## Gate Decision

All 10 mandatory sections PRESENT and PASS. One-variable check PASS. OVERALL=PASS.
Phase 6 may proceed.
