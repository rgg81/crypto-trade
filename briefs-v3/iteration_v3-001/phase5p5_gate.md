# Phase 5.5 Gate — iter-v3/001

OVERALL: PASS

## Per-Section Status
- Section 0 (Data Split): PASS
- Section 1 (Hypothesis): PASS
- Section 2 (IS-Only Evidence): PASS — committed script: analysis/iteration_v3-001/symbol_universe.py (SHA 73fdc8d)
- Section 3 (Proposed Changes): PASS
- Section 4 (Expected OOS Impact): PASS
- Section 5 (Risk Mitigation): PASS
- Section 6 (Risk Management Design): PASS
- Section 7 (Failure-Mode Prediction): PASS
- Section 8 (MERGE/NO-MERGE Criteria): PASS
- Section 9 (Library Stack): PASS

## Verification Notes

### Section 0
`OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` stated as IMMUTABLE with matching language from the skill. IS window bounded by absolute date 2025-03-23 23:59:59 UTC; OOS window from 2025-03-24 00:00:00 UTC. Walk-forward unit (monthly retrain, 24-month rolling window) and CPCV unit (N=10, k=2, 45 paths) both specified.

### Section 1
One sentence: names the four-symbol universe ({BCH, MKR, LDO, TRX}), names the methodology stack (CPCV/PBO/PSR/meta-labeling/FracdiffStat/Critic), states the testable OOS outcome (monthly Sharpe ≥ 1.0 with PBO < 0.4 and PSR > 0.95), and names four specific failure modes structurally addressed. Specific and testable.

### Section 2
Script committed at SHA 73fdc8d (`analysis/iteration_v3-001/symbol_universe.py`). Script header declares IS-only (`OOS_CUTOFF = pd.Timestamp("2025-03-24")`). Five CSV outputs committed alongside script. Brief contains concrete numerical tables: Gate 1 (candle counts, coverage %, max gap, gaps > 1d), Gate 2 (annualised σ, µ, µ/σ, MaxDD, avg daily quote volume), within-universe 4×4 Pearson correlation matrix, cross-track correlation table (vs BTC and SOL), sector taxonomy with project-lineage justification, IS feature coverage check. TRX v2-dead-path justification present (methodology-change + selection-criterion-change rationale). No category-matching — all evidence is numerical.

### Section 3
Symbols enumerated with explicit V3_EXCLUDED_SYMBOLS intersection check confirmed empty. Labeling parameters specified (tp=2.9×NATR_21, sl=1.45×NATR_21, timeout=21 candles, purge gap=88 candles per `(timeout+1)×n_symbols`). Feature list specified (34 columns = V2_FEATURE_COLUMNS with two fracdiff renames; no new families this iteration). Cluster-importance check noted (V2 pruning already ran; Critic Check 4 will enforce IC < 0.7). Risk gates enumerated (7 inherited from v2, hit-rate gate disabled, no new gates this iteration per one-variable discipline). Methodology-stack implementation table covers all 9 deliverables (CPCV, PBO, PSR, meta-labeling M1+M2, FracdiffStat, ADF, IC matrix, V3_FEATURE_COLUMNS pinning, V3_EXCLUDED_SYMBOLS runtime assertion).

### Section 4
Point estimate: +1.2 OOS monthly Sharpe. CI: [+0.6, +1.8]. Dual falsifiers: (1) "If OOS monthly Sharpe < +0.5, hypothesis is rejected"; (2) "If PBO ≥ 0.4, hypothesis is rejected regardless of headline Sharpe." Reasoning for CI bounds includes four explicit factors (zero IS overfitting headroom, meta-labeling trade-count reduction, CPCV vs single-path median discount, zero hyperparameter priors). CI lower bound (+0.6) correctly identified as below the 1.0 merge floor.

### Section 5
R1 (K=3, C=27, IS fire-rate calibration required ≤5%), R2 (7% DD trigger, floor=0.33, anchor=15%), R3 (Mahalanobis 70th-percentile, 16 features), RiskV2Wrapper z-score OOD (|z|>2.5), BTC trend alignment (±20%, 14d). Each gate has IS-calibrated threshold and cited simulated effect from prior iterations (v1 iter-186 R1 −6% IS / +14% OOS; v1 iter-186 R2 MaxDD 41%→32%; v1 iter-186 R3 Sharpe 1.41→1.73; v2 iter-v2/019 BTC-alignment 15 kills). Concentration cap ≤30% stated as hard rule. Vol kill-switch explicitly scoped out of this iteration.

### Section 6
8-primitive table with five columns (primitive, spec, fire-rate prediction IS, regime coverage). Fire rates: vol scaling always-on mean 0.6 scale; ADX ≈60% pass; Hurst ≈90% pass; z-score OOD ≈5–8% killed; low-vol ≈67% pass; hit-rate gate 0% (disabled); BTC alignment ≈8% killed; R3 Mahalanobis ≈30% killed. Regime coverage analysis spans 2020 COVID crash through 2025-Q1 correction with named events. LDO's narrower IS (missed LUNA, listed 2022-09) explicitly disclaimed with mitigation (first OOS model trains 2023-03→2025-02). Concentration trajectory predicted (LDO/TRX lead; BCH/MKR moderate).

### Section 7
Three failure-mode predictions with explicit gate-catch descriptions and metric signatures. (1) M2 meta-labeling overfit: single-path Sharpe +1.5–+1.8, CPCV median 15–25% lower (+1.1–+1.5), PBO 0.30–0.45 range; gate: PBO threshold fires. (2) LDO regime-coverage gap: seed-unstable OOS predictions; mitigation: M2 filter + 5-seed inner ensemble; failure mode: LDO is worst-symbol negative OOS wpnl. (3) TRX dead-path repeat: break-even OOS; gate: CPCV catches break-even-in-disguise IS predictions. Phase 8 diary verification promised via "Pre-Registered Failure-Mode vs Reality" section.

### Section 8
16 mechanical MERGE criteria with exact numerical thresholds, pre-registered before backtest. Covers all project-level floors (IS/OOS Sharpe > 1.0, OOS/IS ratio ≥ 0.5, ≥130 OOS trades, ≥10 trades/month, ≤35% concentration with explicit diversification-exception basis), v3-specific gates (DSR > 0.95, PBO < 0.40, PSR > 0.95), tail-protection criteria (worst-symbol wpnl > −15%, OOS MaxDD ≤ 30%), universe activity check (all 4 symbols ≥1 OOS trade), ADF/IC hard thresholds, 10-seed sweep requirement, and Critic OVERALL = MERGE. NO-MERGE conditions enumerated including library/wall-clock failure conditions. One discretionary axis (10-seed vacuity) explicitly bounded and documented.

### Section 9
mlfinpy 0.1.2 (MIT) declared as primary with fallback rationale (mlfinlab commercial/subscription-required since 2024). pypbo from esvhd/pypbo GitHub main with install command. fracdiff ≥ 0.10 from PyPI. statsmodels, scikit-learn, lightgbm declared as already-installed. Pure-Python CPCV fallback (~80 LOC) noted if mlfinpy lacks CombinatorialPurgedKFold. Reproducibility stamp commitment (engineer writes exact installed versions via `uv pip list`) documented.

## Gate Signed Off By
Quant Engineer — 2026-05-04
