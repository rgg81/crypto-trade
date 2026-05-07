# Phase 5.5 Gate — iter-v3/021

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24 stated UNCHANGED; IS window 2023-03-24→2025-03-24 and OOS window 2025-03-24→present named; sacred constants explicitly restated.
- Section 0.5 (Iteration Type): PASS — TYPE=EXPLORATION cadence #3 of 10 post-bootstrap declared; STRUCTURAL axis Category 5 (NEW universe); single-axis rule honored; references `feedback_v3_iter019_axis_priorities.md` LOCKED axis #2b + `feedback_v3_concentration_is_signal.md` LOCKED; wall-clock budget <30 min target / 2h hard cap stated.
- Section 1 (Hypothesis): PASS — single-sentence hypothesis: universe 3→5 (HBAR+AVAX) dilutes concentration via denominator expansion without removing edge from incumbents; predicted IS band [+0.30, +0.55] median +0.40 / OOS band [+0.45, +0.70] median +0.55; 3 explicit PATH-C failure scenarios provided; mechanism is specific and falsifiable.
- Section 2 (IS-Only Evidence): PASS — committed EDA script `analysis/iteration_v3-021/symbol_candidate_eda.py` at SHA `a360251` BEFORE this brief; 6 CSV outputs committed (symbol_candidate_ranking.csv, per_candidate_data_quality.csv, per_candidate_liquidity.csv, per_candidate_correlations.csv, per_candidate_volatility.csv, synthesis.md); full 10-symbol ranking table with composite scores + Gate 1/2 verdicts; HBAR + AVAX top-2 decision tiles with numerical properties; cross-correlation matrix vs BCH/LDO/TRX; mechanical counterfactual (Section 2.5); behavioral-effect predictor with derived saturation band [186, 269] anchored at iter-v3/018 IS trades 172 (Section 2.6). IS-only discipline honored: EDA ranking and top-2 recommendation logic reads ONLY IS-window kline data.
- Section 3 (Proposed Changes): PASS — 7 sub-fixes enumerated with verifier commands; 15-row reconciliation table (§3.6); changes are: (1) V3_MODELS 3→5 (+HBAR+AVAX); (2) REQUIRED_GAP 66→110=(21+1)×5; (3) _verify_label_leakage_gap message update; (4) _verify_feature_columns UNCHANGED confirmed; (5) enable_per_symbol_cap=False revert; (6) ITERATION_LABEL v3-020→v3-021; (7) fetch + regen features for all 5 symbols including BTC. Single-axis variation confirmed (no labeling/feature/gate/model changes).
- Section 4 (Expected OOS Impact): PASS — predicted Sharpe delta with explicit IS band [+0.30, +0.55] / OOS band [+0.45, +0.70]; 6 explicit falsifiers (Falsifiers 1-6 + process falsifier) with numerical thresholds; saturation falsifier band [186, 269]; 5-row §4.4 catalog-verdict table with explicit criteria per verdict type; PATH C scenarios listed (C-1, C-2, C-3).
- Section 5 (Risk Mitigation): PASS — 11 safeguards (4 cadence-discipline + 4 methodology-pipeline + 3 axis-specific); cap-revert classified as MANDATED closeout (not a separate axis); REQUIRED_GAP propagation risk + BTC-dependency parquet regeneration risk explicitly addressed.
- Section 6 (Risk Management Design): PASS — 7-primitive table (vol scaling, ADX gate, Hurst regime, z-score OOD, low-vol filter, hit-rate feedback DISABLED, BTC trend alignment); cap listed as DISABLED (primitive 8 crossed out); IS fire-rate predictions per primitive; regime coverage stated; gate orthogonality order documented.
- Section 7 (Failure-Mode Prediction): PASS — 8 pre-registered predictions (P1-P8) with probability estimates summing to ~100%; process failures P1-P3 (35% combined: V3_MODELS expansion silent break, REQUIRED_GAP propagation break, parquet stale/column-misaligned); model outcomes P4-P8 (PATH A PROMISING 25%, INERT 30%, NEGATIVE 25%, SPIKE 10%, NULL-RESULT 5%); calibrated against 12 prior EXPLORATIONs including iter-v3/013 universe-reduction precedent.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — 11 pre-registered EXPLORATION criteria (not MERGE gates per EXPLORATION cadence); OOS Sharpe ≥ anchor+0.10 for PROMISING / < anchor-0.10 for NEGATIVE / [anchor±0.10] for INERT; trade-rate floor ≥50 bundle; PBO < 0.40; IC max < 0.70; ADF p<0.05 for 5 symbols; reproducibility SHA; symbol exclusion; behavioral-effect verifier (4 Falsifiers 4-6 signals); pre-committed catalog disposition (cannot be renegotiated post-hoc).
- Section 9 (Library Stack): PASS — identical stack to iter-v3/008-020; no new package additions; versions pinned (lightgbm=4.6.0, numpy=2.2.6, pandas=3.0.0, scikit-learn=1.8.0 PINNED, pyarrow=23.0.1, optuna=4.8.0, scipy=1.17.0, statsmodels=0.14.6); universe expansion uses only existing infrastructure (V3_MODELS tuple, REQUIRED_GAP constant, existing feature pipeline).

## Reasons (if BLOCK)

None — OVERALL=PASS. All 10 sections present with specific numerical content, committed EDA evidence, and executable verifiers.

## Gate Verifications

- EDA script committed at SHA `a360251` before brief commit `6b84934`: CONFIRMED
- Saturation falsifier band [186, 269]: explicitly derived from IS anchor 172 + per-symbol proxy increments: CONFIRMED
- Single-axis variation (only V3_MODELS expansion + mechanical REQUIRED_GAP update + MANDATED cap revert): CONFIRMED
- 15-row §3.6 reconciliation table with verifier commands: CONFIRMED
- Section 8 behavioral-effect verifier uses ALL FOUR falsifier signals (4, 5, 6 + aggregate): CONFIRMED
- HBARUSDT + AVAXUSDT ∩ V3_EXCLUDED_SYMBOLS = ∅: stated and confirmed in §2.7
