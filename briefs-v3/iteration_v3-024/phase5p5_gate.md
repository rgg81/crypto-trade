# Phase 5.5 Gate — iter-v3/024

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24 explicitly restated; IS/OOS windows in absolute dates; ENSEMBLE_SIZE=1 (--exploration); n_trials=35 (EXPLORATION default); sacred constants UNCHANGED.
- Section 0.5 (Iteration Type): PASS — EXPLORATION cadence #6 of 10; single-axis discipline explicitly declared. DROP+ADD is ONE axis (per-symbol funding → cross-asset BTC funding broadcast); functionally a single "swap funding source" axis per the brief's own justification. The §0.5 framing explicitly addresses this: "DROP per-symbol funding_rate_zscore_30 from V3_FEATURE_COLUMNS (revert 14 → 13). ADD btc_funding_rate_zscore_30 to V3_FEATURE_COLUMNS (13 → 14). Cross-asset feature: BTC's funding rate broadcast to all 3 per-symbol models." The two changes (drop + add) are inseparable (the column count stays at 14 both before and after; the axis is "switch funding source" not two independent changes). No brief amendment required.
- Section 1 (Hypothesis): PASS — Single sentence with locked numerical bands: "Replacing per-symbol funding_rate_zscore_30 … will produce importance rank improvement (predicted ≤7 for ≥ 1 symbol) AND IS Sharpe Δ ≥ +0.10 … Predicted IS Sharpe band [+0.30, +0.55] median +0.40 … predicted OOS Sharpe band [+0.40, +0.65] median +0.50." Mechanism explained. Not vague.
- Section 2 (IS-Only Numerical Evidence): PASS — committed script: `analysis/iteration_v3-024/btc_funding_eda.py` (SHA `afdb8bc`). 5 of 5 IS-only EDA gates pass (coverage 100%, IC max 0.1921 < 0.50 and < 0.70, ADF p=0.0, rank-IC max 0.0474 ≥ 0.02). §2.5 behavioral-effect predictor with saturation band [129, 215]. §2.6 PATH-A/B/C pre-classification table with locked conditions.
- Section 3 (Proposed Changes): PASS — enumerated 6-sub-fix decomposition; labeling UNCHANGED (ATR 2.0/1.0, timeout 21 candles, gap 66); risk gates UNCHANGED; symbols UNCHANGED (BCH+LDO+TRX); 13-row brief-vs-code reconciliation table; iter-v3/023 inheritance verifiers listed.
- Section 4 (Expected OOS Impact): PASS — predicted IS Sharpe [+0.30, +0.55] median +0.40; predicted OOS Sharpe [+0.40, +0.65] median +0.50 (PATH A) / [+0.20, +0.50] (PATH B) / [-0.50, +0.10] (PATH C). Explicit falsifiers F1–F5 + process falsifier all locked before backtest.
- Section 5 (Risk Mitigation): PASS — 4 cadence-discipline + 4 methodology-specific = 8 total safeguards; 3 cross-asset-axis-specific risks with mitigations; IS-calibrated thresholds referenced (OOD gate over 14 columns, BTC trend ±15%, ADX 20, Hurst range, low-vol 0.33).
- Section 6 (Risk Management Design): PASS — 7-primitive table with fire-rate predictions and regime coverage for ALL 7 primitives; regime gate (primitive 9) explicitly DISABLED; per-symbol cap DISABLED; gate orthogonality addressed. Cross-asset BTC funding column's effect on primitive 4 (z-score OOD over 14 features) explicitly documented.
- Section 7 (Failure-Mode Prediction): PASS — 6 predictions (P1-P6) calibrated against 13 prior EXPLORATIONs + iter-v3/019/023 INERT precedents; process predictions P1-P3 sum 25%; model predictions P4-P6 sum 95%; PATH A 30%, PATH B 45%, PATH C 20% — forward-looking, not post-hoc.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — 12 EXPLORATION criteria pre-registered including primary PATH-classification thresholds (IS Sharpe ≥ +0.4788 → PATH A; IS Sharpe < +0.2788 → PATH C; IS Sharpe in [+0.2788, +0.4788] → PATH B); PRIMARY DISAMBIGUATION VERIFIER (rank ≤7 for ≥ 1 symbol); saturation falsifier band [129, 215]; all locked before backtest. EXPLORATION never updates BASELINE_V3.md — explicitly stated.
- Section 9 (Library Stack): PASS — full pinned stack declared (python 3.13, lightgbm 4.6.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, pyarrow 23.0.1, mlfinpy 1.4.0, pypbo 0.10.0, fracdiff 0.10.0, statsmodels 0.14.6, optuna 4.8.0, scipy 1.17.0). No version bumps. No new package additions. No library availability risk.

## Single-Axis Discipline — DROP+ADD Confirmation

The brief's §0.5 classifies this as "single-axis variation: NEW external-data-source feature family — cross-asset variant." The DROP+ADD pair is functionally ONE axis change: V3_FEATURE_COLUMNS column count stays at 14 before and after (iter-v3/023 had 14 with funding_rate_zscore_30; iter-v3/024 has 14 with btc_funding_rate_zscore_30). The brief explicitly addresses this in §0.5 framing and §3.5 "Sub-fix decomposition (5-item)." No ambiguity about multi-variable contamination — this is an atomic swap of one feature for its cross-asset counterpart.

## Pre-Flight Inheritance Verifiers (checked at gate time)

- BEFORE sub-fix #1: `len(V3_FEATURE_COLUMNS) == 14 and 'funding_rate_zscore_30' in V3_FEATURE_COLUMNS` — CONFIRMED (observed at gate time)
- BEFORE sub-fix #4: `ITERATION_LABEL = "v3-023"` — CONFIRMED (observed at gate time)
- BTC funding cache: `data/funding_rates/BTCUSDT.csv` present, 7295 data rows — CONFIRMED (observed at gate time)
- Branch: `iteration-v3/024` — CONFIRMED (observed at gate time)
- Track isolation: v3 code does not import from v1 or v2 feature packages — structurally enforced by MODULE_REGISTRY pattern

## Reasons

N/A — OVERALL=PASS. All 10 mandatory sections present and valid. No missing sections, no vague hypotheses, no category-matching without numbers, no missing falsifiers.

## Next Step

Phase 6 implementation authorized. Engineer proceeds to:
1. DROP `funding_rate_zscore_30` from `V3_FEATURE_COLUMNS_TOP_N`, ADD `btc_funding_rate_zscore_30` (sub-fix #1)
2. Implement `compute_btc_funding_rate_zscore` + `add_btc_funding_v3_features` in `funding_v3.py` (sub-fix #2)
3. Register `btc_funding_v3` in GROUP_REGISTRY (sub-fix #3)
4. Update `_verify_feature_columns()` + `ITERATION_LABEL` in `run_baseline_v3.py` (sub-fix #4)
5. Add adversarial tests (past-only + broadcast invariants)
6. Verify BTC funding cache, run linter, run tests
7. Commit `feat(iter-v3/024): btc_funding_rate_zscore_30 cross-asset`
8. DO NOT run backtest — that is the orchestrator's responsibility post-commit
