# Phase 5.5 Gate — iter-v3/022

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24 explicitly stated as IMMUTABLE; ENSEMBLE_SIZE=1, n_trials=35, colsample_bytree=1.0 for EXPLORATION mode.
- Section 0.5 (Iteration Type): PASS — TYPE=EXPLORATION cadence #4 of 10; references feedback_v3_iter019_axis_priorities.md MEDIUM #4 ELEVATED; STRUCTURAL axis Category 4 (NEW risk primitive: regime-conditional kill switch). Wall-clock budget stated.
- Section 1 (Hypothesis): PASS — Single sentence: regime-conditional kill switch on TRX suppressing signals when BTC drawdown_30d > 20% OR |BTC vol_zscore_30d| > 1.5 will reduce PBO at high-PBO TRX cells (PBO max drop from 1.0 to [0.6, 0.85] is primary success metric). Falsifiers provided; mechanism explained.
- Section 2 (IS-Only Evidence): PASS — EDA script analysis/iteration_v3-022/regime_gate_eda.py committed at SHA b728313 BEFORE brief; 5 output CSVs + synthesis.md committed; threshold calibration on IS percentiles (DD 90th=20.6% → locked at 20.0%; vol_z 95th=1.55 → locked at 1.5); per-cell PBO correlation table shows both PBO=1.0 cells have non-trivial gate-fire activity (11.8% and 38.7%); behavioral-effect predictor provided (IS trades [170,175], saturation band [155,189]); past-only discipline verified with .shift(1) discipline noted. Original thresholds (DD>30%, vol_z>2.5) explicitly identified as not-firing in target window — honest calibration.
- Section 3 (Proposed Changes): PASS — 7-item sub-fix decomposition enumerated; V3_MODELS revert 5→3 (BCH+LDO+TRX); REQUIRED_GAP 110→66=(21+1)*3; 6 new RiskV2Config fields specified; past-only implementation detail described; ITERATION_LABEL update; per-symbol cap stays disabled; adversarial past-only test. 12-row brief-vs-code reconciliation table provided.
- Section 4 (Expected OOS Impact): PASS — predicted IS Sharpe [+0.32,+0.50], OOS Sharpe [+0.40,+0.55]; PBO max [0.6,0.85] as primary success metric; 7 numbered falsifiers with thresholds locked before backtest; EXPLORATION outcome interpretation table.
- Section 5 (Risk Mitigation): PASS — 5 inherited + 4 axis-specific safeguards (past-only discipline, IS-only calibration, TRX-only gate scope, calibration disclosure); 4 explicit PATH-C risks described with falsifiers that catch each.
- Section 6 (Risk Management Design): PASS — 9-primitive table (primitives 1-8 inherited, primitive 9 NEW regime gate); each primitive has enable status and threshold. Single-axis discipline verified: only primitive 9 added, existing 7 gates unchanged.
- Section 7 (Failure-Mode Prediction): PASS — 5 pre-registered predictions with probability estimates; P1+P2 joint probability computed; 3 explicit PATH-C scenarios described (over-filter, regime-misalignment, Optuna destabilization) with prior-round calibration.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — 8 EXPLORATION criteria locked; explicit statement that EXPLORATION does NOT enter MERGE evaluation and NEVER updates BASELINE_V3.md.
- Section 9 (Library Stack): PASS — full pinned version list (lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn >=1.8,<1.9, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1).

## Additional Sections Verified

- Section 10 (Adversarial Tests): PASS — test_regime_gate_past_only.py specified with explicit adversarial fixture (spike at t=50; gate must NOT fire at t=50, MUST fire at t=51).
- Section 11 (Catalog Row Pre-Commit): PASS — pre-committed catalog row format locked with TBD fields; verdict-classification distinctions (PROMISING-METHODOLOGY vs PROMISING-INERT-METHODOLOGY) documented; TRX/2022-Q4 axis re-open/close conditions stated.

## Reasons

No BLOCK reasons. All 10 mandatory sections plus Section 0.5 (EXPLORATION type declaration) pass. Key quality checks:
- EDA committed (b728313) before brief: confirmed by brief Section 2.7 integrity checklist.
- Threshold calibration is IS-percentile-based (90th/95th), NOT OOS-optimized: confirmed.
- Original thresholds (DD>30%, vol_z>2.5) identified as non-firing in target window: confirmed via Section 2.1 distribution table.
- Both PBO=1.0 cells (TRX/2022-10 at 11.8%, TRX/2023-01 at 38.7%) have gate-fire activity: confirmed in Section 2.5.
- Single-axis discipline: primitive 9 only; V3_MODELS 5→3 revert is a rollback of iter-v3/021's failed expansion; V3_FEATURE_COLUMNS unchanged at 13.
- Past-only adversarial test specified with concrete spike-bar fixture.
