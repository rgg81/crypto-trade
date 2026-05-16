# Phase 5.5 Gate — iter-v3/061

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24 and TRAINING_MONTHS=24 confirmed
  immutable in run_baseline_v3.py:81-82. IS window 2023-03-24 → 2025-03-23, OOS 2025-03-24
  onward declared in brief. OOS_CUTOFF_MS=1742774400000 stated. PASS.

- Section 0.5 (Iteration Type): PASS — TYPE=EXPLORATION (cycle 1 #2 of 10) declared. Anchor
  pre-locked as iter-v3/060 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.1403; 3-seed mode).
  Axis mandate trace: Critic FINAL 3cee250 Rec #3. Mode-flag refactor SHA 56f5a30 referenced.
  Wall-clock target ~1.1h. Run command includes --exploration --seeds 1 --n-trials 35. PASS.

- Section 1 (Hypothesis): PASS — Single-sentence Path B hypothesis: "Setting
  vol_scale_floor_per_symbol={"TRXUSDT": 0.5} lifts TRX OOS weighted_pnl by +0.47
  with IS bit-identical; predicts OOS Sharpe shift [0.0, +0.20] vs /060 anchor."
  Mechanism (floor applied AFTER existing vol-scaling; Q1_low bucket lift) specified.
  BCH/LDO invariance rationale given. PASS.

- Section 2 (IS-Only Numerical Evidence): PASS — committed EDA at SHA d198b25:
  analysis/iteration_v3-061/trx_anti_kelly_diagnostic.py. Q1 anti-Kelly significance
  tables (Welch t-stats + CI), Q2 weight distribution by win/loss, Q3 outcome by
  5-quantile weight bucket, Q4 counterfactual floor sensitivity, Q5 BCH/LDO invariance
  check, Q6 path decision synthesis — all numerical tables from IS data only. Script
  declared runnable: uv run python analysis/iteration_v3-061/trx_anti_kelly_diagnostic.py.
  PASS.

- Section 3 (Proposed Changes): PASS — 5 edits enumerated:
  (1) risk_v2.py: vol_scale_floor_per_symbol field added to RiskV2Config;
  (2) run_baseline_v3.py: vol_scale_floor_per_symbol={"TRXUSDT": 0.5} in RiskV2Config init;
  (3) run_baseline_v3.py: runtime assertion added to _verify_v3_assumptions;
  (4) new test file tests/strategies/ml/test_per_symbol_vol_scale_floor.py (3 tests);
  (5) ITERATION_LABEL bumped to "v3-061".
  Carry-forward state (V3_FEATURE_COLUMNS_TOP_N=14, V3_MODELS, gap=66, etc.) explicitly
  listed as UNCHANGED. PASS.

- Section 4 (Expected OOS Impact): PASS — predicted bands: IS shift ~0.00 (bit-identical
  counterfactual); OOS shift [+0.06] centered band [0.0, +0.20] vs /060. Per-symbol
  prediction tables (TRX +0.47 OOS wpnl; BCH/LDO ±0%) with BCH IS share projection
  [165%, 190%]. Behavioral effect predictor: IS trade-count change=0 (falsifier: >5),
  OOS trade-count change=0 (falsifier: >5), TRX OOS wpnl lift +0.47 (falsifier band:
  <+0.20 or >+1.0). Section 4.4 falsifier list complete. PASS.

- Section 5 (Risk Mitigation): PASS — 7-primitive gate stack unchanged declared. New
  considerations: per-symbol design isolation (Q5 invariance check + test Edit 4),
  trade-selection invariance (mechanical guarantee: floor applied AFTER kill-gates),
  cap/brake interaction (both disabled at /061 baseline). PASS.

- Section 6 (Risk Management Design): PASS — 8-primitive table with /061 change column:
  Vol-adjusted sizing ACTIVE with TRX-only override to 0.5; ADX ACTIVE global 20.0;
  Hurst ACTIVE; Z-score OOD ACTIVE; Drawdown brake DISABLED; BTC contagion ACTIVE;
  Per-symbol kill switch DISABLED block_long_for=(); Hit-rate gate DISABLED. PASS.

- Section 7 (Failure-Mode Prediction): PASS — 7-row failure mode table with probability
  estimates: INERT-AT-EXPLORATION ~55% (most likely), PROMISING ~15%, NEGATIVE ~10%,
  trade-selection-invariance violation ~5%, BCH/LDO isolation violation <1%, runtime
  failure <5%, methodology FAIL <5%. Most plausible failure mode paragraph describes
  counterfactual +0.05 to +0.10 OOS Sharpe shift below PROMISING threshold. PASS.

- Section 8 (MERGE/NO-MERGE Criteria): PASS — Pre-registered locked criteria:
  8.1 PROMISING-AT-EXPLORATION: IS shift ≥ +0.10 AND OOS shift ≥ +0.20 vs /060 AND
  BCH IS share ≥ 80% (one-sided lower, NOT closed band — per Critic /060 Rec #1) AND
  cpcv_frac_positive_paths ≥ 0.50 AND no methodology FAIL AND mode=="exploration"
  ensemble_size==3 AND 34/34 tests pass.
  8.2 INERT-AT-EXPLORATION: OOS shift in [-0.20, +0.20].
  8.3 SUSPICIOUS-OOS-DOMINANT classifier defined.
  8.4 DSR_relative informational only at EXPLORATION (n_trials=315).
  8.5 NEGATIVE-AT-EXPLORATION triggers axis closure.
  8.6 FAIL (methodology) defined.
  8.7 Cycle 1 cadence: /061 is #2 of 10; CONFIRMATION at /069 (DO NOT COLLAPSE).
  BCH IS share gate: one-sided ≥80% confirmed — PASS.

- Section 9 (Library Stack): PASS — Python 3.13, lightgbm 4.6.0, optuna 4.8.0
  (n_jobs=1 per revert 31665f6), numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0,
  scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1. No new dependencies.
  Mode-flag refactor SHA 56f5a30 intact. PASS.

- Section 10 (QR Audit Trail): PASS — 6 stages documented:
  Stage 1: Critic FINAL 3cee250 Rec #3 verbatim directive.
  Stage 2: EDA at analysis/iteration_v3-061/ SHA d198b25 (6 questions, 6 CSVs +
    diagnostic_summary.md).
  Stage 3: Path B selection rationale (5 reasons; Paths A/C/D/E rejected with causes).
  Stage 4: Setup commit SHA chain (Phase A revert 31665f6, Phase B-3 ab2d9ac,
    walk-forward fix e149e9d, mode-flag refactor 56f5a30, /060 diary b794d6a,
    EDA d198b25).
  Stage 5: Critic /060 Rec #1 BCH-share one-sided gate wording compliance verified.
  Stage 6: Cycle 1 cadence counting (061 = #2 of 10; CONFIRMATION at 069).
  PASS.

## Additional Verification Checks

**ITERATION_LABEL**: "v3-061" confirmed at run_baseline_v3.py:128. PASS.

**Mode-flag wiring**: EXPLORATION_ENSEMBLE_SIZE=3 (run_baseline_v3.py:92),
CONFIRMATION_ENSEMBLE_SIZE=10 (run_baseline_v3.py:90); --exploration CLI flag
documented in mode-flag refactor SHA 56f5a30. PASS.

**Per-symbol vol_scale_floor field threading**:
- RiskV2Config.vol_scale_floor_per_symbol field added at risk_v2.py with default_factory=dict.
- _vol_scale method updated: floor = config.vol_scale_floor_per_symbol.get(symbol, config.vol_scale_floor).
- _build_v3_model in run_baseline_v3.py passes vol_scale_floor_per_symbol={"TRXUSDT": 0.5}.
- _verify_v3_assumptions runtime assertion verifies dict=={"TRXUSDT": 0.5}.
PASS.

**Test suite**: 34/34 pass (3 new TestPerSymbolVolScaleFloor + 19 TestEnsembleUnified +
12 TestLookaheadEmbargo). Tests confirm: (1) empty dict = bit-identical weight_factor;
(2) TRX atr=0.3 clipped to 0.5; (3) BCH/LDO mean_vol_scale=0.3 unchanged when TRX
floor=0.5. PASS.

**Data freshness** (verified 2026-05-13): BCHUSDT lag=3.2h, LDOUSDT lag=3.2h,
TRXUSDT lag=3.2h, BTCUSDT lag=3.2h. All < 16h limit. PASS.

**Sacred constants unchanged**: OOS_CUTOFF_DATE=2025-03-24 (run_baseline_v3.py:81);
TRAINING_MONTHS=24 (run_baseline_v3.py:82). PASS.

**Track isolation**: grep -r "from crypto_trade.features " src/crypto_trade/features_v3/
returns only comment lines (no actual v1 imports). PASS.

**Linter**: ruff check risk_v2.py + new test file = 0 errors (new lines only; pre-existing
E501 lines in run_baseline_v3.py docstrings were present before this iteration and are
unchanged). PASS.

**One-variable discipline**: sole axis change is vol_scale_floor_per_symbol={"TRXUSDT": 0.5}.
Feature bundle, label, universe, all other risk parameters unchanged. PASS.

**Code committed before gate**: code commit SHA 6910fcf precedes this gate file. PASS.

## Reasons (if BLOCK)

N/A — OVERALL=PASS.

## Code Changes Commit

SHA: 6910fcf
Branch: iteration-v3/061
