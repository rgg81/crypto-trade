# Phase 5.5 Gate — iter-v3/052

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24 confirmed IMMUTABLE. IS window 2023-03-24 through 2025-03-23; OOS window 2025-03-24 onward. Sacred constants unchanged.
- Section 0.5 (Iteration Type Declaration): PASS — EXPLORATION cycle 4 #2 of 10; --seeds 1 --n-trials 35 --clean-oof; SINGLE-AXIS SWAP (PIVOTED from TWO-VARIABLE bundle). ENSEMBLE_SIZE=5, colsample_bytree Optuna-tunable.
- Section 1 (Hypothesis): PASS — ONE sentence: ADDING regime_momentum_signed_3d at universal scope (SWAP with fracdiff_d05_close; net count stays 15) investigates whether the 3-bar time-scale variant of regime_momentum_signed_5d captures shorter-horizon regime persistence, lifting bundle IS Sharpe vs iter-v3/028 baseline +0.5101 while preserving OOS Sharpe ≥ +0.5053. Specific, falsifiable, single-variable.
- Section 2 (IS-Only Evidence): PASS — Primary evidence from committed `analysis/iteration_v3-051/axis_c_regime_3d_*.csv` (SHA `290f37b`). ADF p=0 all 4 syms; IC strict-gate PASS max|IC|=0.6192<0.70 (NO carve-out needed); univariate Spearman ρ -0.044 to -0.068 significant all 4 syms (mean -0.057 > fracdiff -0.044). Secondary evidence from `analysis/iteration_v3-052/ldo_removal_eda.py` SHA `0a10581` documenting orchestrator-supersession. Both committed scripts; reproducible from IS parquet data only.
- Section 3 (Proposed Changes): PASS — Enumerated 10 setup-commit changes: (1) activate compute_regime_momentum_signed_3d dispatch in add_engineered_v3_features; (2) SWAP V3_FEATURE_COLUMNS_TOP_N 15th element fracdiff_d05_close→regime_momentum_signed_3d; (3) V3_MODELS UNCHANGED 3-sym; (4) REQUIRED_GAP UNCHANGED 66; (5) regen 4-symbol parquets; (6) update _verify_feature_columns; (7) _verify_v3_models UNCHANGED; (8) _verify_required_gap UNCHANGED; (9) ITERATION_LABEL="v3-052"; (10) banner comment update. ONE-VARIABLE discipline: single-axis SWAP (net count 15 unchanged, V3_MODELS unchanged). fracdiff_d05_close PARKED (compute function + 5 tests retained as dispatched-but-unused).
- Section 4 (Expected OOS Impact): PASS — Quantitative predicted bands: IS +0.58±0.18 [+0.40,+0.75], OOS +0.55±0.30 [+0.25,+0.85], IS-OOS daily ratio 1.05±0.45 [0.60,1.50] IN-BAND. Behavioral-effect predictor: IS trade count -13% to +12%; OOS trade count -22% to +20%; 3d importance rank top-10 in ≥1 sym. Explicit falsifier for axis saturation (rank ≥14/15 ALL syms AND trade count change <±5%). Explicit falsifier band for IS/OOS Δ.
- Section 5 (Risk Mitigation): PASS — R1-R5 framework present: 2-candle cooldown (R1); vol scaling weight_factor [0.33,1.0] (R2); OOD z-score 15-D ACTIVE (R3); BTC trend kill 15% ACTIVE (R4); per-symbol PnL cap DISABLED per /020 CLOSED (R5). IS-calibrated thresholds stated (BTC 15%=calibrated /050 EDA; OOD 2.0=calibrated /011; vol scaling calibrated /028). No gate-threshold changes at /052.
- Section 6 (Risk Management Design): PASS — 10-primitive gate table present. All primitives accounted for: BTC trend kill, vol scaling, ADX gate, Hurst regime, z-score OOD (15-D UNCHANGED count due to SWAP), low-vol filter, hit-rate gate DISABLED, per-symbol cap DISABLED, regime gate DISABLED, primitive 10 INFRASTRUCTURE-ONLY (wired off per /051 REVERT). Explicit audit column for each primitive state.
- Section 7 (Failure-Mode Prediction): PASS — Single most likely failure mode identified: PATH B (PROMISING-INERT, 30%) — 3d not learned decisively by Optuna at single-seed n_trials=35 due to sister-5d IC 0.43-0.47 stacking distortion. Secondary: PATH C-clean (20%). Tertiary: PATH C-suspicious (10%). PATH A (25%). PATH D (15%). Per-path action specified. Stacking-risk mitigation argument present (IC 0.43-0.47 BELOW 0.50 threshold; time-scale orthogonality).
- Section 8 (MERGE/NO-MERGE Criteria): PASS — 5 LOCKED paths (A/B/C-clean/C-suspicious/D) with numerical thresholds. PATH D explicitly added per Critic FINAL `32cc46f` rec #3. All thresholds sourced from memory rules. CONFIRMATION-only gates noted (DSR, BOTH-must-improve). PBO<0.4 and PSR>0.95 enforced at both EXPLORATION and CONFIRMATION per §8.4.
- Section 9 (Library Stack): PASS — lightgbm==4.6.0, optuna==4.8.0, numpy==2.2.6, pandas==3.0.0, scikit-learn==1.8.0, scipy==1.17.0, statsmodels==0.14.6, pyarrow==23.0.1, mlfinlab==1.4 (fallback: mlfinpy), pypbo, fracdiff>=0.10. No new dependencies at /052. Python 3.13+.
- Section 10 (QR Audit Trail): PASS — Full supersession documented: orchestrator pick (LDO removal + fracdiff drop) PRE-FALSIFIED by /052 EDA SHA `0a10581`. LDO IS weighted_pnl premise correction (+36.78% vs orchestrator's misread -14.96% from net_pnl_pct). 2-sym counterfactual: IS Δ -0.16 BREAKS BOTH-must-improve gate; IS-OOS daily ratio 3.58 OUT-OF-BAND (PATH C-suspicious by construction). QR EDA supersedes per `feedback_v3_axis_selection_quant_discipline.md` rule 4. PIVOTED axis (regime_momentum_signed_3d UNIVERSAL) cited with /051 EDA RANKED #2 SHA `290f37b`. Section 10 subsections 10.1-10.9 present. Setup commit SHA placeholder §10.1 marked PENDING (Engineer backfills at setup-commit time, as specified by brief).
- Section 11 (Catalog Row Pre-commits): PASS — 5 pre-committed catalog rows, one per outcome path (A/B/C-clean/C-suspicious/D). File references. Memory rules consulted. Critic FINAL artifacts cited.

## ONE-VARIABLE Rule Check

SWAP of single slot (15th element fracdiff_d05_close → regime_momentum_signed_3d). Net V3_FEATURE_COLUMNS_TOP_N count UNCHANGED at 15. V3_MODELS UNCHANGED (3-sym BCH+LDO+TRX). REQUIRED_GAP UNCHANGED (66). All risk-gate parameters UNCHANGED. fracdiff_d05_close PARKED (compute function + 5 adversarial tests retained as dispatched-but-unused). ONE-VARIABLE discipline: PASS.

## PIVOT-Supersession Verification

LDO-removal axis PRE-FALSIFIED by /052 QR EDA (SHA `0a10581`). Orchestrator pick REPLACED by /051 EDA RANKED #2 (regime_momentum_signed_3d UNIVERSAL, SHA `290f37b`). Both EDA scripts committed. `feedback_v3_axis_selection_quant_discipline.md` rule 4 satisfied. Section 10 QR audit trail present. PIVOT documented in brief header and §§10.3-10.9.

## Adversarial Test Count

- tests/features_v3/test_fracdiff_d05_universal.py: 5 tests — RETAINED as dead-code coverage. Per brief §3.2 "RETAIN unchanged." These tests will FAIL after the SWAP because test 1 checks fracdiff in V3_FEATURE_COLUMNS_TOP_N and test 5 checks the /051 architecture. They must be UPDATED to reflect /052 state (fracdiff PARKED; regime_momentum_signed_3d PRESENT). Updated count: 5 tests retained with updated assertions.
- tests/features_v3/test_regime_momentum_signed_3d_universal.py: 5 NEW adversarial tests per brief §3.2.
- Total new adversarial tests: 5 new + 5 updated = 10 tests covering the /052 axis.

## Code Changes Required (from §3)

1. src/crypto_trade/features_v3/engineered_v3.py — ACTIVATE regime_momentum_signed_3d dispatch in add_engineered_v3_features (1 line; from dead code at L330-376)
2. src/crypto_trade/features_v3/__init__.py — SWAP 15th element fracdiff_d05_close → regime_momentum_signed_3d in V3_FEATURE_COLUMNS_TOP_N
3. run_baseline_v3.py — Update _verify_feature_columns: REMOVE fracdiff MUST-BE-PRESENT; ADD regime_momentum_signed_3d MUST-BE-PRESENT; CHANGE regime_momentum_signed_3d MUST-BE-ABSENT to MUST-BE-PRESENT; ADD fracdiff_d05_close MUST-BE-ABSENT; update docstring and print messages
4. run_baseline_v3.py — ITERATION_LABEL = "v3-052"
5. Feature parquets — regen for BCHUSDT, LDOUSDT, TRXUSDT, ALGOUSDT via `uv run crypto-trade features --track v3 --interval 8h --symbols BCHUSDT,LDOUSDT,TRXUSDT,ALGOUSDT --format parquet --workers 4`
6. tests/features_v3/test_fracdiff_d05_universal.py — Update 5 tests to reflect fracdiff PARKED state (swap assertion direction)
7. tests/features_v3/test_regime_momentum_signed_3d_universal.py — CREATE 5 new adversarial tests

## Notes

- fracdiff_d05_close compute function KEPT in dispatch (add_engineered_v3_features line 585 unchanged); column continues to be generated in parquets but DROPPED from V3_FEATURE_COLUMNS_TOP_N. This is the PARKED pattern per /051 closeout.
- Section 10.1 setup commit SHA placeholder will be backfilled at setup-commit time per brief instruction.
- OOD z-score dimensionality: stays 15-D (SWAP preserves count; confirmed in brief §5.3).
