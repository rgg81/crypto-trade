# Phase 5.5 Gate — iter-v3/130

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE = 2025-03-24 and training_months = 24 explicitly confirmed unchanged. IS window: earliest 4h candle close through 2025-03-24. OOS window: 2025-03-24 through current extent (~2026-05-21). Bar-interval 4h named as primary axis change.
- Section 1 (Hypothesis): PASS — Specific one-sentence hypothesis with quantified bands: IS monthly Sharpe Δ ∈ [−0.30, +0.40] vs /121 ADJUSTED (~+1.06) AND OOS monthly Sharpe Δ ∈ [−0.30, +0.40] vs /121 OOS +0.9682. Explicit falsifiers (F1–F9) registered. HIGH-RISK posture declared per G1 FAIL.
- Section 2 (IS-Only Numerical Evidence): PASS — EDA at `analysis/iteration_v3-130/` committed SHA `ccc0446` BEFORE brief. 6 tables (T1–T6): bar-interval candidate catalog, data depth proxy, closed-loop Optuna-re-training simulator (T3a 8h baseline + T3b 4h proxy + T3c relative improvement), feature stability proxy, ADF stationarity, pre-flight gate decision. Simulator enforces IS-only fence (IS trades from /121 only, close_time < OOS_CUTOFF_MS). No OOS data referenced. Numerical tables committed.
- Section 3 (Proposed Changes): PASS — Single axis enumerated: (1) bar_interval 8h→4h with argparse choices extension; (2) features_v3 cache dir `data/features_v3_4h/`; (3) REQUIRED_GAP=66 in candle-count terms unchanged; (4) enable_per_symbol_drawdown_brake=False (REVERT preserved) + enable_per_symbol_drawdown_scaling=False (NEW REVERT); (5) ITERATION_LABEL "v3-130"; (6) accretion guard update. Zero new features.
- Section 4 (Expected OOS Impact): PASS — IS Sharpe Δ band [−0.30, +0.40] vs ADJUSTED anchor; OOS Sharpe Δ band [−0.30, +0.40] vs /121 +0.9682. Falsifier F1: IS < 0.76 or > 1.46 fires. Falsifier F2: OOS < 0.67 or > 1.37 fires. Confidence interval present. F6 (Jaccard < 0.70) and F7 (IS trade-count outside [260, 433]) are explicit falsifiers.
- Section 5 (Risk Mitigation): PASS — Five risk mitigations listed: (1) bar-interval-axis closure discipline; (2) F6 Optuna-trajectory-shift Jaccard binding (adapted for bar-interval open-time mismatch); (3) F7 behavioral-effect predictor binding; (4) F9 wall-clock cap binding (2.5h); (5) no structural risk mitigations beyond /121 baseline (7-gate RiskV2 unchanged). HIGH-RISK posture rationale per PRIME DIRECTIVE.
- Section 6 (Risk Management Design): PASS — 7-gate RiskV2 stack unchanged from /121; fire-rate predictions implicit in Section 4 falsifier bands; regime coverage per Section 7 modal distribution. HIGH-RISK posture declared at Section 6 entry. Both /127 binary brake and /129 continuous scaling REVERTED (both closed).
- Section 7 (Failure-Mode Prediction): PASS — Pre-registered modal expectation distribution with 7 outcome modes and explicit prior probabilities: NEGATIVE-catastrophic 30%, NEGATIVE-Optuna-trajectory-shift 20%, NEGATIVE-INERT 15%, NEGATIVE-methodology-defect 5%, NEUTRAL 15%, PROMISING 10%, SUSPICIOUS-OOS-DOMINANT 5%. Forward-looking; verifiable at Phase 8 diary. Total NEGATIVE-class prior 70% honestly declared per cycle-7 base rate (8/8 NEGATIVE through /129).
- Section 8 (MERGE/NO-MERGE Numerical Criteria): PASS — Pre-registered first-match-wins decision tree with 10 criteria (C1–C10). Numerical thresholds locked before backtest runs: C1 IS < +0.91 OR OOS < +0.67 = NEGATIVE-catastrophic; C2 F6 Jaccard < 0.70 = NEGATIVE-Optuna-trajectory-shift; C9 IS ≥ +1.06 AND OOS ≥ +0.97 AND F6 PASS = PROMISING-MECHANICAL; C10 IS ≥ +1.16 AND OOS ≥ +1.07 = PROMISING-strong. No post-hoc reclassification allowed.
- Section 9 (Library Stack Declaration): PASS — Brief Section 9 is the "Acceptance smoke test" (10 items per /128 closeout mandate). No new libraries introduced; stack inherited from /121 baseline (LightGBM, Optuna, standard scipy/numpy/pandas). No mlfinlab/mlfinpy/pypbo/fracdiff changes. Library stack unchanged = no new declaration required per v3 precedent (same pattern as /129, /128, /127, /126, /125, /121).

## Reasons (if BLOCK)

None — OVERALL PASS. Proceeding to Phase 6 implementation.

## Engineer Notes

- label_timeout_minutes at 4h: The brief specifies K=21 × 4h = 84h = 5040 min. However the runner's `_verify_timeout_consistency` currently hard-asserts expected_timeout_minutes == 10080. The 4h bar-interval branch MUST update this check to be bar-interval-conditional (5040 at 4h, 10080 at 8h). BacktestConfig.timeout_minutes and LightGbmStrategy.label_timeout_minutes must both be set to 5040 when --bar-interval 4h is passed.
- accretion guard: The current guard asserts enable_per_symbol_drawdown_scaling == True (the /129 axis). For /130 this must become False (REVERT). The guard must be updated to reflect /130 state.
- run.log: The 5-occurrence instrumentation gap persists from /129. The setup commit must implement run.log capture (stdout+stderr redirect to reports-v3/iteration_v3-130/run.log at run end, or TeeLogger at startup).
- FEATURES_DIR_4H: A new `Path("data/features_v3_4h")` constant must be added alongside existing FEATURES_DIR and FEATURES_DIR_24H.
- _generate_v3_features: The 4h branch must call process_symbol_v3 with interval="4h" and output to FEATURES_DIR_4H.
- Feature parquet loading: pq_path for 4h must resolve to `FEATURES_DIR_4H / f"{sym}_4h_features.parquet"`.
- _run_adf_tests and _compute_ic_matrix: These load feature parquets; must be passed the correct features_dir path for 4h.
