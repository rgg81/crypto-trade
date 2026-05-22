# Phase 5.5 Gate — iter-v3/019

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — `OOS_CUTOFF_DATE = 2025-03-24`, `training_months = 24`, `ENSEMBLE_SIZE = 1` (set by --exploration), `n_trials = 10` (set by --exploration default). Sacred constants explicitly stated as UNCHANGED.
- Section 0.5 (Iteration Type): PASS — TYPE=EXPLORATION, cadence #1 of 10 post-bootstrap, ANCHOR = iter-v3/018 multi-seed mean +0.3788 IS / +0.3869 OOS (NOT iter-v3/013 single-seed, as required). References `feedback_v3_iter019_axis_priorities.md` LOCKED 2026-05-07 + `feedback_structural_over_knob_exploration.md`. Single-axis declaration (NOT a gate-threshold knob) present.
- Section 1 (Hypothesis): PASS — One-sentence hypothesis with explicit mechanism: funding-rate z-score over 30-cycle window captures derivatives-market-positioning crowding (mean-reversion direction, per BIS WP 1087 2025 mechanism), structurally orthogonal to existing 13 features (max |IC| = 0.3758 < 0.50 strict target), non-trivial rank-IC (TRX 7-bar -0.0485, LDO 7-bar -0.0234, BCH 3-bar -0.0194), predicted IS Sharpe band [+0.45, +0.85] (median +0.58).
- Section 2 (IS-Only Evidence): PASS — Committed analysis script `analysis/iteration_v3-019/funding_rate_eda.py` (SHA `95858cb`) stated before brief. 7 output CSV/md files. Quantitative tables: coverage (100% all 3 symbols), distribution (raw + z-scored per symbol with percentiles), ADF (p ≈ 0 all 3 symbols), IC matrix (39 rows, max 0.3758), rank-IC (9 rows, max |IC| = 0.0485), saturation predictor anchor ([129, 215]). IS-window slice enforced (pre-OOS-cutoff). Behavioral-effect predictor present with band [129, 215] = 172 ± 25%, lower/median/upper scenarios, and secondary feature-importance verifier (Falsifier 4). All 5 EDA gates (coverage, IC redundancy hard gate, IC strict brief target, ADF, rank-IC non-trivial) confirmed PASS.
- Section 3 (Proposed Changes): PASS — 4 change categories (symbols UNCHANGED, labeling UNCHANGED, features +1, risk gates UNCHANGED). 7-item sub-fix decomposition with spec + verifier for each. 15-row brief-vs-code reconciliation table (§3.6) with executable verifier commands. Inheritance checks enumerated.
- Section 4 (Expected OOS Impact): PASS — IS Sharpe band [+0.45, +0.85] (median +0.58) with anchor calibration. 4 named falsifiers (F1: IS Sharpe below anchor; F2: saturation band [129, 215]; F3: wall-clock >30 min; F4: feature importance 0 across all 3 models). Outcome interpretation table (6 verdict categories with conditions, catalog row, next iteration). Locked before backtest.
- Section 5 (Risk Mitigation): PASS — 8 cadence/methodology safeguards (4 inherited + 4 new-feature-axis-specific). 3 explicit axis-specific risks with mitigations: (1) fetcher reliability (cache-first, incremental, 16h-staleness guard); (2) look-ahead from settlement timing (detailed analysis confirming past-only discipline with .shift(1)); (3) feature redundancy with vwap_dev_20 (max |IC| 0.3758 — below 0.50 strict target; Falsifier 4 as backstop).
- Section 6 (Risk Management Design): PASS — 7-primitive table with fire-rate predictions and regime coverage. Primitive 4 (z-score OOD) correctly noted as now operating over 14 features (slightly tighter kill rate). Gate orthogonality analysis present. Section explicitly states 7-primitive table UNCHANGED from iter-v3/018 (single-feature-axis variation).
- Section 7 (Failure-Mode Prediction): PASS — 7 predictions (P1-P7, where P1-P3 are process failures at 10-15% each; P4-P7 are model outcomes; probabilities sum correctly). Each prediction includes: description, detection signal, mitigation or next-iteration consequence. Calibrated against prior 10 EXPLORATIONs + iter-v3/018 multi-seed evidence. P4+P5+P7 = 75% PROMISING-family, P6 = 15% NEGATIVE-clean.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — 11 EXPLORATION criteria with numerical thresholds, locked before backtest. Criterion 11 contains saturation falsifier [129, 215] + secondary feature-importance verifier (Falsifier 4). Catalog-row pre-committed disposition for all 4 verdict outcomes (PROMISING / PROMISING-INERT / PROMISING-MECHANICAL / NEGATIVE). Criterion 1 threshold (+0.4788 = anchor +0.10) and criterion 2 (< +0.3788 = below anchor) are unambiguous and non-overlapping with criterion 3 ([+0.3788, +0.4788) = INERT band).
- Section 9 (Library Stack): PASS — Full pinned library list matching iter-v3/018 stamp (lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1, mlfinpy 1.4.0, pypbo 0.10.0, fracdiff 0.10.0, httpx). Explicit statement: NO new package additions or version bumps.

## Pre-Flight Inheritance Checks (verified before Phase 6)

- V3_FEATURE_COLUMNS count: 13 (PASS — correct pre-edit state; `funding_rate_zscore_30` NOT yet present)
- `ITERATION_LABEL = "v3-018"`: PASS (present in run_baseline_v3.py:102; to be updated to v3-019 in Phase 6)
- `atr_tp_multiplier=2.0`: PASS
- `atr_sl_multiplier=1.0`: PASS
- `zscore_threshold=2.0`: PASS
- `adx_threshold=20.0`: PASS
- `threshold_pct=15.0`: PASS

## One-Variable Discipline Check

Single axis: `+funding_rate_zscore_30` to V3_FEATURE_COLUMNS (13 → 14). Supporting infrastructure (new fetcher module, new feature module, new GROUP_REGISTRY entry) is non-independent scaffolding for the single-feature axis. PASS.

## Track Isolation Check

New `funding_v3.py` must live in `features_v3/` with zero imports from `crypto_trade.features` (v1) or `crypto_trade.features_v2` (v2). This is verified as a Phase 6 pre-flight grep. Pre-committed as PASS by design (identical pattern to `volume_micro_v3.py`).

## Reasons (BLOCK — none; overall PASS)

No blocking gaps identified.
