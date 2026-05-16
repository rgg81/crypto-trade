# Phase 5.5 Gate — iter-v3/029

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24 and training_months=24 declared IMMUTABLE; IS window 2023-03-24 to 2025-03-24 (24 months); OOS window 2025-03-24 onward. ENSEMBLE_SIZE=1 (--exploration), n_trials=35, colsample_bytree=1.0 declared.
- Section 1 (Hypothesis): PASS — single sentence: "Adding ALGOUSDT to V3_MODELS (3→4; V3_FEATURE_COLUMNS=14 UNCHANGED; risk gate stack UNCHANGED) will mechanically dilute single-symbol concentration without removing edge from incumbent symbols, because the candidate was selected on per-symbol feature-signature alignment (the corrected criterion vs iter-v3/021 raw-correlation mistake) and ALGO's volatility regime + BTC-trend coupling profile match the SHARED top-7 features BCH+LDO+TRX use jointly." Falsifiable: Falsifiers 4-6 defined. Predicted IS [+0.30, +0.65] median +0.50, OOS [+0.30, +0.65] median +0.50 vs anchor +0.5101/+0.5053.
- Section 2 (IS-Only Evidence): PASS — committed EDA scripts: `analysis/iteration_v3-029/per_symbol_feature_analysis.py` (SHA d451885) and `analysis/iteration_v3-029/symbol_candidate_targeted.py` (SHA c30369d). Outputs include: per_symbol_feature_signature.csv, feature_dispersion_ranking.csv (14-row table with rank_range per feature across BCH/LDO/TRX), candidate_targeted_ranking.csv (5-candidate composite score ranking). All inputs are IS-window-only (pre-OOS_CUTOFF_MS). Behavioral-effect predictor present with saturation band [110, 145] IS trades, anchored to iter-v3/028 single-seed equivalent. Falsifiers 4-6 numerically defined.
- Section 3 (Proposed Changes): PASS — 5 sub-fixes enumerated: (1) V3_MODELS 3→4 with ALGOUSDT; (2) REQUIRED_GAP 66→88=(21+1)×4; (3) ITERATION_LABEL v3-028→v3-029; (4) feature parquet regen for ALGO; (5) V3_FEATURE_COLUMNS BYTE-IDENTICAL=14 UNCHANGED. Reconciliation table with 6 verifier commands present.
- Section 4 (Expected OOS Impact): PASS — IS/OOS Sharpe bands [+0.30, +0.65] median +0.50 vs anchor. 5 catalog framing rows with distinct PATH labels (PATH A PROMISING, PATH B NEGATIVE-DILUTION, PATH C INERT, PATH C-2 NEGATIVE-no-effect, PATH B Falsifier-6). Falsifier 4 (regime_momentum rank 14/14 on ALGO), Falsifier 5 (TRX concentration ≥70%), Falsifier 6 (ALGO OOS PnL < -10%) all defined with explicit thresholds.
- Section 5 (Risk Mitigation): PASS — 11 entries across 3 risk categories (4 cadence-discipline, 4 methodology-hygiene, 3 axis-specific). Hard 2h wall-clock cap stated. OOS contamination mitigation documented. Single-axis discipline stated.
- Section 6 (Risk Management Design): PASS — 7-primitive gate stack declared UNCHANGED from iter-v3/028 baseline: BTC trend kill ±15%/14d, vol scaling, ADX 20.0, Hurst regime, feature z-score OOD |z|≤2.0, low-vol filter, hit-rate DISABLED. Per-symbol cap DISABLED (iter-v3/020). Regime gate DISABLED. ALGO inherits byte-identically.
- Section 7 (Failure-Mode Prediction): PASS — 8 failure-mode predictions (P1-P8) with probability estimates calibrated against 22 prior EXPLORATIONs: P4 PROMISING 30-40%, P5 PATH B 30-35%, P6+P7 INERT/concentration-unchanged 20-30%, P8 OOS-suspicious-lottery 15-20%.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — 11 EXPLORATION criteria pre-registered (OOS Sharpe ≥0.50 → PROMISING, <0.40 → Falsifier 1 FIRES, [0.40,0.50] → INERT; trade-rate floor ≥50 IS + ≥50 OOS bundle; PBO <0.40; IC max <0.70; ADF p<0.05 all 14 features all 4 symbols; reproducibility; saturation falsifier [110,145] + 3 sub-falsifiers). Catalog-axis verdicts map to §4.4 table. 4 pre-committed dispositions for PATH A/B/C/C-2.
- Section 9 (Library Stack): PASS — stack declared UNCHANGED from iter-v3/028: python=3.13, lightgbm=4.6.0, numpy=2.2.6, pandas=3.0.0, scikit-learn=1.8.0, pyarrow=23.0.1, mlfinpy=1.4.0, pypbo=0.10.0, fracdiff=0.10.0, statsmodels=0.14.6, optuna=4.8.0, scipy=1.17.0. No new package additions.

## Notes

- Single-axis discipline confirmed: ONE new symbol (ALGOUSDT); all other parameters (features, risk gates, labeling, ATR multipliers, Optuna budget, CPCV params) BYTE-IDENTICAL to iter-v3/028 baseline.
- ALGOUSDT is NOT in V3_EXCLUDED_SYMBOLS (v1 symbols: BTC/ETH/LINK/LTC/DOT; v2 symbols: SOL/XRP/DOGE/NEAR; v3-dropped: MKR). PASS.
- EXPLORATION cadence discipline: iter-v3/029 is cadence #1 of 10 in NEW post-iter-v3/028 cycle; next CONFIRMATION = iter-v3/039. STRICT 10:1 per feedback_v3_cadence_discipline.md.
- Brief self-check at end of document: all 11 checklist items marked [x]. Cross-verified by Engineer: confirms all 10 mandatory sections complete.
- Brief SHAs: research_brief.md at 9301744; EDA SHAs d451885 (Phase 1) and c30369d (Phase 3) pre-date this brief as required.
