# Phase 5.5 Gate — iter-v3/016

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24, OOS_CUTOFF_MS=1742774400000, ensemble_seeds via _derive_ensemble_seeds. Both sacred constants explicitly declared UNCHANGED.
- Section 0.5 (Iteration Type): PASS — TYPE=EXPLORATION declared; references both `feedback_v3_iter016_xgboost_mandate.md` AND `feedback_structural_over_knob_exploration.md`; NINTH EXPLORATION; Category 2 structural axis (model architecture); wall-clock 2h hard cap stated.
- Section 1 (Hypothesis): PASS — Single-sentence hypothesis ("Replacing LightGBM with XGBoost on iter-v3/013's 13-feature stack will produce IS Sharpe within ±0.30 of iter-v3/013's +1.0088 baseline AND will surface measurably different feature-importance rankings with Spearman ρ < 0.85"). Mechanism articulated (depth-wise vs leaf-wise growth, EFB vs hist binning). Three pathways (PATH A/B/C) pre-registered.
- Section 2 (IS-Only Evidence): PASS — Analysis script `analysis/iteration_v3-016/xgboost_baseline_eda.py` committed at SHA `b5592bd` BEFORE this brief. Four output files committed: `xgboost_param_map.csv` (14 rows, 6 cols), `xgboost_smoke_results.csv` (status=SKIPPED with documented reason — xgboost not yet installed), `xgboost_pitfalls.md` (10 pitfalls), `xgboost_eda_synthesis.md`. Behavioral-effect predictor present (§2.4) with saturation falsifier threshold (|IS trades − 209| < 11 AND bit-identical → NULL-RESULT). Smoke skip is documented and pre-committed for Phase 6 resolution. Verified files exist in `analysis/iteration_v3-016/`.
- Section 3 (Proposed Changes): PASS — 8 sub-fixes enumerated in §3.5 table with spec and verifier for each. 15-row reconciliation table in §3.6. Single-axis reaffirmed in §3.7. Inheritance from iter-v3/015 documented in §3.8. Implementation strategy in §3.9. All 4 first-commit pre-commits (drop tbr_zscore_30, add tbr_raw, fix _write_feature_importance, ITERATION_LABEL update) plus XGBoost integration (deps, class, CLI flag) listed.
- Section 4 (Expected OOS Impact): PASS — §4.2 predicted IS Sharpe band [+0.70, +1.30] median +1.00; predicted IS trade count [165, 250] median 200. §4.3 has 5 falsifiers (including saturation falsifier and process falsifiers). §4.4 has 6-row single decision tree (fixes the iter-v3/015 §4.3-vs-§4.4 conflict per Critic FINAL Rec 4). No §4.3-vs-§4.4 ambiguity — §4.4 is declared the canonical decision tree.
- Section 5 (Risk Mitigation): PASS — §5.1 cadence safeguards (4): wall-clock cap, single-axis, no BASELINE update, saturation falsifier active. §5.2 methodology safeguards (4): adversarial tests, file-artifact table, pre-flight library check, two-round Critic flow. §5.3 axis-specific risks (3): XGBoost integration bug surface, hyperparam space mismatch, NaN-row handling. All three have explicit mitigations.
- Section 6 (Risk Management Design): PASS — 7-primitive table with all gates byte-identical to iter-v3/013 baseline (adx_threshold=20.0 confirmed). Fire-rate predictions and regime coverage stated. Gate orthogonality to underlying library documented (all gates consume predict_proba output). Concentration informational-only under EXPLORATION declared.
- Section 7 (Failure-Mode Prediction): PASS — 6 pre-registered predictions (P1–P6): 3 process-level (P1 install failure P=10%, P2 mid-backtest crash P=15%, P3 feature_importance schema break P=5%) and 3 model-level (P4 PROMISING-ALTERNATIVE P=35%, P5 PROMISING-INERT P=30%, P6 NEGATIVE or NULL-RESULT P=20%). Probabilities sum to 115% (process tails are non-exclusive with model outcomes, explicitly noted). Calibrated against 8 prior EXPLORATIONs. Forward-looking — verifiable against diary.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — 11-criterion EXPLORATION-PROMISING table locked before backtest. EXPLORATION-NEGATIVE criteria stated. EXPLORATION-NEGATIVE-no-effect criteria stated. BLOCK criteria stated. No MERGE pathway declared (EXPLORATION never updates BASELINE_V3.md). Pre-registration eliminates post-hoc rationalization.
- Section 9 (Library Stack): PASS — 10-package table. ONE new dep declared: `xgboost>=2.0,<3.0`, Apache-2.0 license, Phase 6 sub-fix #6 adds it. Upper-bound pin <3.0 rationale documented. Fallback declared (source build if prebuilt wheel fails). All other packages confirmed already installed. Reproducibility stamp requirements stated.

## Reasons (if BLOCK)

None — all 10 sections PASS.

## Gate Notes

- Section 2.2 smoke SKIPPED is acceptable: xgboost is not yet installed (documented as EXPECTED in §2.5 setup integrity table). Phase 6 sub-fix #6 installs it and re-runs the EDA smoke, which is reconciliation verifier #15.
- The §4.3-vs-§4.4 conflict from iter-v3/015 is explicitly resolved in §4.4 opening sentence: "Decision tree applied IN ORDER. First matching row determines the verdict." §4.3 falsifiers remain present for process clarity but §4.4 is the canonical decision tree.
- Single-axis discipline confirmed: all 4 pre-commits (tbr_zscore_30 drop, tbr_raw addition, _write_feature_importance fix, ITERATION_LABEL update) are baseline-restoration housekeeping per §3.7, not axis variations. The sole semantic axis is LightGBM → XGBoost.
