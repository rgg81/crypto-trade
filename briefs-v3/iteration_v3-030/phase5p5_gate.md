# Phase 5.5 Gate — iter-v3/030

OVERALL: PASS

## Per-Section Status
- Section 0 (Data Split): PASS — `OOS_CUTOFF_DATE = 2025-03-24`, `training_months = 24`, `OOS_CUTOFF_MS = 1742774400000` all restated; IS/OOS windows named; sacred constants declared UNCHANGED.
- Section 1 (Hypothesis): PASS — Single sentence: LDO trained on top-7 features (ret_skew_200, ret_kurt_50, ret_kurt_200, vwap_dev_20, hurst_diff_100_50, btc_ret_14d, range_realized_vol_50) from iter-v3/028 multi-seed importance, BCH+TRX+ALGO unchanged at 14 features. Mechanism explained (LDO 31-IS-month sample, dimensionality-reduction via halving feature space). Predicted IS [+0.70, +0.95] median +0.82, OOS [+1.65, +1.95] median +1.80. LDO OOS PnL band [-1.0%, +5.0%] median +1.0%.
- Section 2 (IS-Only Evidence): PASS — committed script `analysis/iteration_v3-030/ldo_feature_subset_analysis.py` at SHA `36aaacd` BEFORE this brief. Reads IS-only `reports-v3/iteration_v3-028/in_sample/model_importance_last_month_{BCH,LDO,TRX}USDT.csv`. Outputs: `ldo_top7_features.csv`, `ldo_top14_full_ranking.csv`, `cross_symbol_top7_overlap.csv`, `synthesis.md`. Concrete numbers: LDO top-7 importances (264.4→224.6), LDO-TRX Jaccard 0.40 (lowest pair). Behavioral-effect predictor included: LDO IS trade band [13, 18] anchored at iter-v3/029's 15 ±20%. 4 falsifiers pre-registered.
- Section 3 (Proposed Changes): PASS — 8-item sub-fix table: (1) add `V3_FEATURES_PER_SYMBOL` dict in `features_v3/__init__.py`; (2) add `features_for_symbol()` helper; (3) runner uses `features_for_symbol(symbol)` in `_build_v3_model`; (4) extend `_verify_feature_columns()` for subset-subset assertion; (5) `_verify_feature_columns()` regime_momentum carve-out check; (6) ITERATION_LABEL v3-029 → v3-030; (7) V3_MODELS=4 byte-identical; (8) V3_FEATURE_COLUMNS portfolio-level unchanged at 14. Reconciliation table with 8 verifier commands. 3 mandatory adversarial pytest cases specified.
- Section 4 (Expected OOS Impact): PASS — 4-path catalog framing table with conditions and verdicts. Predicted Sharpe delta anchored to iter-v3/029 +1.7653. Explicit falsifiers: F1 (LDO bit-identical), F2 (BCH+TRX+ALGO bit-identical), F3 (LDO OOS < -10%), F4 (bundle OOS < +1.50). Confidence intervals explicit for each path.
- Section 5 (Risk Mitigation): PASS — 4 cadence-discipline risks, 4 methodology-hygiene risks, 3 axis-specific risks. Explicit `feedback_v3_engineered_features_proven.md` deviation justification (regime_momentum drop from LDO subset is portfolio-level-compliant). 2h wall-clock cap cited; estimated 25-35 min.
- Section 6 (Risk Management Design): PASS — 7-primitive risk gate stack table: BTC trend kill, vol scaling, ADX gate (20.0), Hurst regime, feature z-score OOD, low-vol filter, hit-rate feedback. All UNCHANGED from iter-v3/029. Status column explicit for each primitive.
- Section 7 (Failure-Mode Prediction): PASS — 8 failure modes (P1–P8) with probabilities and evidence. PATH A 30-40%, PATH A-MARGINAL 20-25%, PATH B 20-25%, PATH C <10%, lottery P8 15-20%. Combined PATH A+A-MARGINAL ≈ 50-65%.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — 11 pre-registered EXPLORATION criteria. Criterion 1: OOS Sharpe ≥ +1.65 → PROMISING. Criterion 2: OOS Sharpe < +1.50 → Falsifier 4. Criterion 11: saturation falsifier with [13, 18] LDO IS trade band + 4 falsifiers. Note: this is an EXPLORATION (not CONFIRMATION/MERGE), so criteria govern catalog-row disposition not BASELINE_V3.md update. 4 pre-committed dispositions (PATH A, A-MARGINAL, B, C) explicitly enumerated in §11.
- Section 9 (Library Stack): PASS — explicit library stack restated as SAME as iter-v3/029: python 3.13, lightgbm 4.6.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, pyarrow 23.0.1, mlfinpy 1.4.0, pypbo 0.10.0, fracdiff 0.10.0, statsmodels 0.14.6, optuna 4.8.0, scipy 1.17.0. No new package additions.

## Single-Axis Verification
PASS — ONE new architectural element: per-symbol feature subset for LDO only. V3_FEATURE_COLUMNS=14 portfolio-level UNCHANGED. V3_MODELS=4 UNCHANGED. REQUIRED_GAP=88 UNCHANGED. All risk gates UNCHANGED. No labeling change, no Optuna budget change, no ENSEMBLE_SIZE change.

## Phase 1 EDA SHA Verification
PASS — `analysis/iteration_v3-030/ldo_feature_subset_analysis.py` committed at SHA `36aaacd` (2026-05-08), BEFORE brief at SHA `5ea6099`. EDA reads IS-only inputs. OOS data not consulted.

## Gate Rationale
All 10 mandatory sections present and complete. Brief is specific (exact 7 features named, exact LDO importance rankings, exact Jaccard scores), falsifiable (4 pre-registered falsifiers with numerical thresholds), and reproducible (committed EDA script + reconciliation verifier table). Single-axis discipline confirmed: only V3_FEATURES_PER_SYMBOL dict + features_for_symbol() dispatch is new; everything else is byte-identical to iter-v3/029.

Phase 6 implementation authorized.
