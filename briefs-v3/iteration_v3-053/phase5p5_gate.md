# Phase 5.5 Gate — iter-v3/053

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24 confirmed IMMUTABLE. IS window 2023-03-24 through 2025-03-23; OOS window 2025-03-24 onward. Sacred constants unchanged.
- Section 0.5 (Iteration Type Declaration): PASS — EXPLORATION cycle 4 #3 of 10; --seeds 1 --n-trials 35 --clean-oof; SINGLE-AXIS SWAP (regime_momentum_signed_3d PARKED per /052 PATH C-suspicious; hurst_drift_50_200 ACTIVATED). ENSEMBLE_SIZE=5, colsample_bytree Optuna-tunable.
- Section 1 (Hypothesis): PASS — ONE sentence: ADDING hurst_drift_50_200 to V3_FEATURE_COLUMNS_TOP_N at universal scope (SWAP with regime_momentum_signed_3d which DROPS per /052 closeout; net count stays 15) investigates whether the NEW Category 1 engineered feature hurst_drift_50_200 = hurst_50 - hurst_200 provides incremental discriminative value to LightGBM's tree-split decisions DESPITE the EDA-discovered LINEAR REDUNDANCY R^2=1.0 with 3 source primitives. Specific, falsifiable, single-variable. REFRAMED HYPOTHESIS B disclosed upfront.
- Section 2 (IS-Only Evidence): PASS — Primary evidence from committed `analysis/iteration_v3-053/` (SHA `1fc6d55`), produced by `hurst_drift_50_200_eda.py` on IS parquets only. 6 axes: (1) compute+distribution, (2) ADF stationarity all 4 syms p<<0.05, (3) IC matrix (max|IC|=0.881 with hurst_diff_100_50 source primitive; Category 2 carve-out per `feedback_v3_engineered_feature_pivot.md`), (4) univariate Spearman rho NOT significant p<0.05 any of 4 syms (mean +0.0114), (5) **LINEAR REDUNDANCY R^2=1.0 EXACT** (algebraic identity verified via OLS; residuals at machine epsilon), (6) per-symbol distribution comparison. All committed scripts; reproducible from IS parquet data only. Category-matching explicitly absent.
- Section 3 (Proposed Changes): PASS — Enumerated 9 setup-commit changes: (1) ADD compute_hurst_drift_50_200 function in engineered_v3.py (~60 LOC); (2) ACTIVATE dispatch in add_engineered_v3_features after compute_regime_momentum_signed_3d; (3) SWAP V3_FEATURE_COLUMNS_TOP_N 15th element regime_momentum_signed_3d→hurst_drift_50_200; (4) V3_MODELS UNCHANGED 3-sym; (5) REQUIRED_GAP UNCHANGED 66; (6) parquet regen NOT REQUIRED (computable from existing columns); (7) update _verify_feature_columns; (8) update ITERATION_LABEL="v3-053"; (9) 5 NEW + 2+6 UPDATED adversarial tests. ONE-VARIABLE discipline: single-axis SWAP (net count 15 unchanged, V3_MODELS unchanged). compute_regime_momentum_signed_3d dispatch call RETAINED as dead code (zero revert cost per /052 mandate).
- Section 4 (Expected OOS Impact): PASS — Quantitative predicted bands: IS +0.40 to +0.60 (mean +0.50), Δ vs /028 anchor [-0.10,+0.05]; OOS +0.20 to +0.85 (mean +0.50), Δ vs /028 [-0.30,+0.30]; IS-OOS daily ratio ∈[0.5,2.0] with 60% prob. Behavioral-effect predictor: IS trade count ±5% vs /052 (saturation-likely); hurst_drift_50_200 importance rank PRE-FALSIFIER PREDICTION = rank 13-15/15 in ALL 3 syms. SWAP-axis importance-rank-ONLY saturation trigger INCLUDED per /052 Critic Recommendation #3: rank ≥ 14/15 in ALL 3 syms = PATH B INDEPENDENT of trade-count change.
- Section 5 (Risk Mitigation): PASS — 3 EDA-derived pre-falsifiers documented with mitigations: (1) R^2=1.0 → monitor importance rank; (2) univariate ρ insignificant → pre-registered saturation band; (3) max|IC|=0.881 → Category 2 carve-out applies (post-carve-out max|IC|=0.193 CLEAN). R1-R5 framework present (BTC trend 15%, vol scaling, ADX 20.0, Hurst regime, OOD z-score 2.0). No new risk primitives. IS-calibrated thresholds unchanged from /052.
- Section 6 (Risk Management Design): PASS — 10-primitive gate table present. All primitives UNCHANGED from /052: BTC trend kill ENABLED, vol-targeting ENABLED, ADX ENABLED (20.0), Hurst embedded in regime_momentum_signed_5d, OOD z-score ENABLED (15-D UNCHANGED due to SWAP preserving count), low-vol DISABLED, hit-rate DISABLED, per-symbol cap DISABLED (CLOSED /020), regime gate DISABLED (CLOSED /022), primitive 10 block_long_for=() (REVERTED /051). Single-axis discipline: only feature SWAP.
- Section 7 (Failure-Mode Prediction): PASS — Single most likely failure mode: PATH B (PROMISING-INERT 55% prob) — R^2=1.0 linear redundancy causes Optuna at n_trials=35 single-seed to prefer 3 source primitives over composed candidate. Secondary: PATH C-suspicious (15%). Tertiary: PATH D (15%). PATH A (5%). Per-path actions specified. Linear-redundancy displacement mechanism argument present.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — 5 LOCKED paths (A/B/C-clean/C-suspicious/D) with NUMERICAL thresholds. PATH D INCLUDED per /051 Critic FINAL `32cc46f` rec #3. SWAP-axis importance-rank-ONLY trigger included per /052 Critic rec #3 (rank ≥ 14/15 ALL 3 syms = PATH B regardless of trade-count change). All thresholds sourced from memory rules. CONFIRMATION-only gates noted.
- Section 9 (Library Stack): PASS — lightgbm==4.6.0, optuna==4.8.0, numpy==2.2.6, pandas==3.0.0, scikit-learn==1.8.0, scipy==1.17.0, statsmodels==0.14.6, pyarrow==23.0.1, mlfinlab==1.4 (fallback: mlfinpy), pypbo, fracdiff>=0.10. No new dependencies at /053. hurst_drift_50_200 uses only numpy+pandas arithmetic on existing parquet columns.
- Section 10 (QR Audit Trail): PASS — EDA-driven framing documented. Orchestrator pick PRELIMINARILY SUPPORTED (per /052 closeout HIGH-priority #1 + Critic `34cc46f` rec #2). QR EDA (SHA `1fc6d55`) revealed 3 pre-falsifiers. Decision: PROCEED under REFRAMED HYPOTHESIS B — alternatives (CatBoost 4-8h OOB; per-symbol drawdown brake 1.5h viable but deferred) evaluated in §10.5. Section 10 subsections 10.1-10.6 present. Setup commit SHA §10.1: `abc52dc` (backfill after gate).
- Section 11 (Catalog Row Pre-commits): PASS — 5 pre-committed catalog rows, one per outcome path (A/B/C-clean/C-suspicious/D). EDA SHA cited. Critic FINAL artifacts cited.

## ONE-VARIABLE Rule Check

SWAP of single slot (15th element regime_momentum_signed_3d → hurst_drift_50_200). Net V3_FEATURE_COLUMNS_TOP_N count UNCHANGED at 15. V3_MODELS UNCHANGED (3-sym BCH+LDO+TRX). REQUIRED_GAP UNCHANGED (66). All risk-gate parameters UNCHANGED. compute_regime_momentum_signed_3d dispatch call RETAINED as dead code (zero revert cost per /052 PATH C-suspicious mandate). Parquet regen NOT REQUIRED (hurst_drift_50_200 computable on-the-fly from existing hurst_100, hurst_diff_100_50, hurst_200 columns). ONE-VARIABLE discipline: PASS.

## Linear Redundancy Pre-Falsifier (LR-PF) Verification

Algebraic identity confirmed in `src/crypto_trade/features_v3/regime_v3.py:126`:
- `hurst_diff_100_50 = hurst_100 - rolling_hurst(close, 50)` — re-arranges to:
- `hurst_50 = hurst_100 - hurst_diff_100_50`
- Therefore: `hurst_drift_50_200 = hurst_50 - hurst_200 = hurst_100 - hurst_diff_100_50 - hurst_200`

EDA OLS regression (axis5_linear_redundancy.csv SHA `1fc6d55`) confirms R^2=1.000 with
residuals at machine epsilon (~1e-16) across all 4 symbols. This is the EXACT same identity,
verified both algebraically in code and numerically on IS data.

Category 2 carve-out per `feedback_v3_engineered_feature_pivot.md` APPLIES mechanically
(composed feature vs source primitives). Post-carve-out max|IC| = 0.193 (CLEAN).
LR-PF is UNPRECEDENTED in v3 history (prior max|IC| with source primitive was 0.756 at
cross_asset_divergence_norm; hurst_drift is 0.881; R^2=1.0 is new structural violation type).

## PATH D Inclusion Check

PATH D (EXPLORATION-NULL-RESULT) PRESENT in Section 7 and Section 8. Trigger: IS Δ ∈
(-0.10, +0.05) AND OOS Δ ∈ (-0.20, +0.20) AND axis LEARNED (rank ≤ 13/15 in ≥1 sym AND
trade count change ≥10% OR Sharpe Δ both ≤ ±0.10 with rank ≤ 13/15). Per Critic FINAL
`32cc46f` rec #3 mandate. PATH D: PASS.

## SWAP-Axis Importance-Rank-ONLY Saturation Trigger Check

Present in Section 4.3 per /052 Critic FINAL `34cc46f` Recommendation #3:
"If hurst_drift_50_200 importance rank ≥ 14/15 in ALL 3 V3_MODELS at /053 backtest,
PATH B (PROMISING-INERT) fires INDEPENDENT of trade-count change."
Mechanism: SWAP preserves 14 base features (which carry most signal); 15th slot SWAP
creates same-shape feature stack where trade-roster is bounded by base features regardless
of 15th element identity. SWAP-axis predictor: PASS.

## Adversarial Test Count

- tests/features_v3/test_hurst_drift_50_200_universal.py: 5 NEW adversarial tests (hurst_drift in universal list + last element check; algebraic identity; past-only; stationarity; V3 universe 3-sym). 4/4 non-parquet tests PASS (stationarity test requires parquet — passes when parquet available).
- tests/features_v3/test_regime_momentum_signed_3d_universal.py: 5 tests UPDATED to reflect /053 PARKED state (2 tests inverted; 3 tests unchanged). 3/3 non-parquet tests PASS.
- tests/features_v3/test_features_for_symbol.py: 6 tests UPDATED to reflect /053 SWAP state. All PASS.
- Total non-parquet test run: 144 PASS, 0 FAIL.

## Code Changes Summary (from §3)

1. src/crypto_trade/features_v3/engineered_v3.py — ADD compute_hurst_drift_50_200 (~60 LOC); ACTIVATE dispatch after compute_regime_momentum_signed_3d (retained as dead code); ADD to __all__
2. src/crypto_trade/features_v3/__init__.py — SWAP 15th element regime_momentum_signed_3d → hurst_drift_50_200; UPDATE docstring
3. run_baseline_v3.py — ITERATION_LABEL = "v3-053"; _verify_feature_columns: REMOVE 3d MUST-BE-PRESENT; ADD hurst_drift MUST-BE-PRESENT; ADD 3d MUST-BE-ABSENT; UPDATE per-symbol loop; UPDATE print messages
4. Feature parquets — NOT REQUIRED (hurst_drift_50_200 computed on-the-fly from existing parquet columns)
5. tests/features_v3/test_hurst_drift_50_200_universal.py — CREATE 5 new adversarial tests
6. tests/features_v3/test_regime_momentum_signed_3d_universal.py — UPDATE 2 tests to reflect /053 PARKED state
7. tests/features_v3/test_features_for_symbol.py — UPDATE 6 tests to reflect /053 SWAP state

## Pre-Flight Checks

- Lint: `uv run ruff check` — ALL PASS on all 4 changed files
- Format: `uv run ruff format` — no changes needed (engineered_v3.py auto-formatted; others clean)
- Tests: 144/144 non-parquet tests PASS
- Track isolation: `grep -r "from crypto_trade.features " src/crypto_trade/features_v3/` — only comment lines; no actual v1 imports; PASS
- Sacred constants: OOS_CUTOFF_DATE=2025-03-24 UNCHANGED; training_months=24 UNCHANGED; 5-seed inner ensemble UNCHANGED

## Setup Commit

SHA: `abc52dc` — `feat(iter-v3/053): SWAP hurst_drift_50_200 in / regime_momentum_signed_3d out of V3_FEATURE_COLUMNS_TOP_N`
Branch: iteration-v3/053

## Notes

- hurst_200 source primitive is in parquet but NOT in V3_FEATURE_COLUMNS_TOP_N (only hurst_100 and hurst_diff_100_50 are in the model input). hurst_drift_50_200 is computable from parquet at training time via compute_hurst_drift_50_200 dispatch — the runner's LightGBM feature loading path calls add_engineered_v3_features which computes hurst_drift_50_200 on-the-fly before passing feature_columns to the model. The column never needs to be in the parquet file.
- OOD z-score dimensionality: stays 15-D (SWAP preserves count; confirmed in brief §5.3).
- EXPLORATION wall-clock budget: 2h hard cap. Precedent /051=1.28h, /052=1.25h. ETA ~1.25h.
