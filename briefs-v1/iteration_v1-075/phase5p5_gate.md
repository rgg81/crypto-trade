# Phase 5.5 Gate — iter-v1/075

OVERALL: PASS

## Iteration Type (from Brief Section 0.5)
TYPE: SPECIALIST EXPLORATION — NEW SYMBOL (single-coin cohort; universe-extension)

## Axis Family + Rotation Status
FAMILY: universe (NEW SYMBOL — ATOMUSDT; first universe-extension EXPLORATION in v1 history)
ROTATION_STATUS: VALID

Prior 5 EXPLORATION families (/066 → /074):
  - iter-v1/066: universe (LINK SPECIALIST) → ELIMINATED
  - iter-v1/067: universe (LTC SPECIALIST) → ELIMINATED
  - iter-v1/072: risk-primitive (BTC R1 streak-cooldown enable) → NEGATIVE
  - iter-v1/073: feature-family (ETH feature-subset reduction) → NEGATIVE
  - iter-v1/074: risk-primitive (ETH mid-bull SHORT VETO) → verdict pending
Last-5 families: {universe, universe, risk-primitive, feature-family, risk-primitive}
NOT 5-of-5 monoculture → rotation VALID. Cycle-7 per-symbol regime-specialist mandate
suspends formal rotation discipline (feedback_v1_cycle6_per_symbol_regime_specialist_mandate.md);
universe axis is additionally valid under the mandate.

## HIGH-RISK Declaration
HIGH-RISK: YES (universe substitution changes Optuna's training-objective domain)
Mitigation: 50-INNER-seed averaging (sigma_pop <= 0.30 gate; held at /063, /064, /065).
Multi-outer-seed deferred to follow-up if /075 PROMISING + basin-lottery triggers fire.

## LM Master Response Verification
- briefs-v1/iteration_v1-075/lgbm_advisor.md exists: PASS
- Brief Section 3.4 addresses each LM Master recommendation: PASS
  - HP direction #1 (verify cohort ATOMUSDT + label v1-075): ADOPTED VERBATIM
  - HP direction #2 (observe n_estimators distribution at Phase 7.4): ADOPTED
  - HP direction #3 (observe min_data_in_leaf + lambda_l1 at Phase 7.4): ADOPTED
  - Feature-engineering direction (verify cross-asset + within-symbol NaN): VERIFIED (table_09)
  - Predicted modal IS Sharpe +0.30 / band [−0.10, +0.65]: ADOPTED as F-AXIS #1 reference
  - Risk Flag 1 (TS-mom positive-baseline trap nuance): ADOPTED as H1d + F-AXIS-FALSIFIER #1
  - Risk Flag 2 (deep-bear IS + OOS short-cohort overfit risk): ADOPTED as F-AXIS-FALSIFIER #1
  - Risk Flag 3 (0.61 BTC corr cross-asset feature dilution): ADOPTED as F-AXIS-FALSIFIER #2
  - Risk Flag 4 (v2 dead-paths ATOM swap failure): PRE-REGISTERED as orthogonal confound
  - Risk Flag 5 (0.81 IS DOT corr BUNDLE-002 redundancy concern): FLAGGED for downstream
  - Saturation Risk 1 (validate composite predictor on rank-2/3): ACKNOWLEDGED
  - Saturation Risk 2 (+0.30 modal is prior not calibrated frequentist): ACCEPTED
  - Saturation Risk 3 (basin-lottery at 50-inner-seed): ADOPTED as F-AXIS #2
  - Closing note (per-direction Sharpe + WR + trade count): HARDWIRED as F-AXIS-FALSIFIER #1

## Cadence Check
- Wall-clock budget declared: 2h hard cap (SPECIALIST EXPLORATION) — PASS
- Cadence type: SPECIALIST EXPLORATION (NEW SYMBOL mine; no precedent-count cadence required)

## Per-Section Status
- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24 + training_months=24 confirmed
  immutable; IS window 2023-03-24 → 2025-03-24 (2160 8h candles); OOS 2025-03-24 → present;
  IS firewall: _assert_is_only_path + is_only(df) applied; OOS NaN counts informational only.
- Section 0.5 (Iteration Type): PASS — TYPE: SPECIALIST EXPLORATION — NEW SYMBOL declared;
  cycle-7 SPECIALIST-MINE 1/N; wall-clock 2h hard cap; kill-switch conditions enumerated.
- Section 0.6 (Architecture-Family Justification): PASS — FAMILY=universe; ROTATION_STATUS=VALID;
  one-sentence mechanism rationale present; prior 5 families documented.
- Section 0.7 (SPECIALIST EXPLORATION 1-of-N): PASS — mine-phase rank 1/N; cohort ATOMUSDT;
  data extent 6.33y; methodology constants table; single-bit changes enumerated; anchor stated
  (NONE — universe-extension); strike rule ONE-ATTEMPT pre-registered.
- Section 1 (Hypothesis): PASS — specific: LOCKED SPECIALIST methodology on ATOMUSDT produces
  IS Sharpe in PROMISING band [+0.15, +0.50] via idiosyncratic-distance mechanism (0.617 IS BTC
  corr); mechanism chains H1a-H1e with quantified sub-claims and named risks H1d+H1e.
- Section 2 (IS-Only Evidence): PASS — committed script analysis/v1-075/eda.py; 10 tables
  persisted (table_01 through table_10 / table_09 NaN audit); IS firewall documented;
  numerical evidence: corr table (0.617 BTC IS), vol table (81.98% 2024), regime table (58%
  chop), TS-mom table (5,1 = +0.638), label dist table (LONG SL 60%), cross-cohort pyramid.
- Section 2.5 (HIGH-RISK Axis Declaration): PASS — HIGH-RISK declared; reason: universe
  substitution; mitigation: 50-INNER-seed averaging; multi-outer-seed deferral + trigger
  conditions stated; NEW SYMBOL strike rule explicit.
- Section 3 (Proposed Changes): PASS — (a)-(e) code-level changes enumerated; byte-identical
  table vs /063//065; Section 3.3 explicit no-change list; Section 3.4 LM Master response
  table present with all 14 advisory items addressed.
- Section 4 (Expected OOS Impact): PASS — F-AXIS #1 bands pre-registered (PROMISING-CLEAN
  >= +0.50; PROMISING-TENTATIVE [+0.20, +0.50); NEGATIVE < +0.20 or < 50 trades); F-AXIS #2
  sigma_pop bands; F-AXIS #3 OOS informational only; F-AXIS-FALSIFIER #1 per-direction table;
  F-AXIS-FALSIFIER #2 feature-importance dilution check; F-AXIS-BEHAVIORAL trade-count floor;
  explicit falsifier conditions stated.
- Section 5 (Risk Mitigation): PASS — axis-specific risks (positive-baseline trap grey-mid-band;
  deep-bear IS short-bias mirage; 2 ALL-NaN-IS SYMBOL-conditional features); risk wrappers table
  Model A pattern (R1=OFF, R2=OFF, R3=ON-SHARED, R5=ON, AXIS-R DISABLED); QE Phase 6.0 Critic
  pre-flight check items enumerated (15 items).
- Section 6 (Risk Management Design — v1 analog): PASS — integrated in Section 5 risk wrappers
  table; brief references each risk primitive: R3 OOD cutoff=0.70, R5 vol-target=0.3, R1=OFF
  (CATALOG-CLOSED), R2=OFF; brief Section 2.5 and 5.2 provide the 8-primitive equivalent table.
  Note: v1 SPECIALIST uses a 4-gate subset (R1/R2/R3/R5); R4 (liquidation gap) and R6-R8 are
  N/A at v1 SPECIALIST level; this is acceptable per v1 iteration plan (Model A pattern).
- Section 7 (Failure-Mode Prediction): PASS — Section 1 H1d (positive-baseline trap) + H1e
  (deep-bear IS short-bias mirage) are forward-looking failure-mode predictions; Section 4
  F-AXIS-FALSIFIER #1 specifies what the failure looks like in metrics (per-direction Sharpe);
  Section 5.1 explicitly documents the LINK/LTC-precedent verdict pattern.
- Section 8 (MERGE/NO-MERGE Numerical Criteria): PASS — pre-registered verdict bands frozen at
  brief commit SHA (Section 12): PROMISING-CLEAN >= +0.50; PROMISING-TENTATIVE [+0.20, +0.50);
  NEGATIVE < +0.20 or < 50 IS trades. Strike rule: ONE-ATTEMPT-AND-ELIMINATE. Per-direction
  Sharpe falsifier: >70% short + short >> long by 1.5sigma → NEGATIVE-SHORT-BIAS-MIRAGE.
  Anti-tuning language explicit (Section 7 items 1-6: bands frozen at brief commit SHA;
  no post-Phase-7 re-tuning; no retroactive band-edge adjustment).
- Section 9 (Library Stack): PASS — Section 3.1 + runner clones /065 which uses standard
  LightGBM via lgbm.py; no mlfinlab/mlfinpy/pypbo/fracdiff usage at this iteration;
  LightGBM standard PyPI package via uv.lock; no license risk.

## Additional v1-only Checks
- Section 11 (Backtest-Live Parity): PASS — Section 11 explicit: parity N/A at /075 EXPLORATION
  (single-coin SPECIALIST; no bundle assembly); parity requirements for BUNDLE-002 assembly
  pre-committed (engine.py:_initial_setup ATOMUSDT fetch; per-symbol model registry; no
  coin overlap; IS-only weights; no post-trade netting).
- V1_ITER075_UNIVERSE declared in features_v1/__init__.py: PASS (QE Phase 6 setup complete)
- run_iteration_075.py created (clone of /065 with single-bit changes): PASS
- Dispatch branch elif iteration_label=="v1-075" in run_baseline_v1.py: PASS
- V1_ITER075_UNIVERSE imported in run_baseline_v1.py: PASS
- 18/18 pytest tests/test_iteration_v1_075.py PASS
- data/features/ATOMUSDT_8h_features.parquet exists (6933 x 230 cols; 48 V1_FEATURE_COLUMNS_PRUNED
  columns confirmed via test_atomusdt_parquet_contains_all_48_feature_columns): PASS
- ATOMUSDT not in V1_EXCLUDED_SYMBOLS: PASS (test_atom_not_in_v1_excluded_symbols PASS)
- Lint (ruff check) PASS; Format (ruff format) PASS on all modified files.

## Reasons (if BLOCK)
N/A — OVERALL: PASS. All sections present and complete. Phase 6 backtest may proceed.
