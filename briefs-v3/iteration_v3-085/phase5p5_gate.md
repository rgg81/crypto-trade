# Phase 5.5 Gate — iter-v3/085

OVERALL: PASS

---

## Per-Section Status

- Section 0 (Data Split): PASS — `OOS_CUTOFF_DATE = 2025-03-24`, `training_months = 24` both
  declared UNCHANGED, IMMUTABLE. IS and OOS windows stated in absolute dates. No start_time
  trim or cherry-pick.
- Section 0.5 (Iteration Type): PASS — TYPE: EXPLORATION. 3-seed mode, n_trials=35, 2h wall-clock
  HARD CAP declared. Count change 14→15 stated as the sole axis. Cadence position: cycle-3
  EXPLORATION #4 of 10.
- Section 1 (Hypothesis): PASS — Single sentence: funding×momentum interaction the depth-4 tree
  cannot compose at runtime; momentum into crowded long = exhaustion (fade), into crowded short =
  squeeze (follow). Specific mechanism, falsifiable.
- Section 2 (IS-Only Evidence): PASS — Committed EDA SHA `5264091`. Four scripts:
  `pooled_model_cross_symbol_structure.py`, `pooled_with_symbol_dummy.py`,
  `ldo_donor_augmentation.py`, `funding_regime_engineered_feature.py`. All read IS data only
  (`open_time < OOS_CUTOFF_MS`). Confirmed output CSVs present:
  `q1_sample_sizes.csv`, `q2_feature_target_ic.csv`, `q3_scale_invariance.csv`,
  `q4_leave_one_symbol_out.csv`, `part2_pooled_3way.csv`, `part2_symbol_id_importance.csv`,
  `part3_ldo_donor.csv`, `part4_t1_engineered_ic.csv`, `part4_t2_orthogonality.csv`,
  `part4_t3_incremental.csv`, `part4_t4_funding_coverage.csv`.
  Section 2.0 pooled-model falsification (3 probes, all NOT SUPPORTED); T1 IC; T2 orthogonality;
  T3 incremental information; T4 funding coverage; T-LDO structural context — all with concrete
  numbers, no category-matching.
- Section 3 (Proposed Changes): PASS — Single axis enumerated: `funding_regime_momentum_5d`
  added (14→15). No labeling change, no symbol change, no risk-gate change, no model-arch change,
  no seed change. Look-ahead discipline stated (Section 3.4). Engineering checklist complete
  (Section 3.5). Wall-clock estimate based on /082 and /084 precedents (Section 3.6).
- Section 4 (Expected OOS Impact): PASS — Two anchors declared per the two-anchor mandate:
  ANCHOR 1 = /084 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.3322, 3-seed); ANCHOR 2 =
  /059 CONFIRMATION baseline (IS +1.0894 / OOS +0.5791, 10-seed) RESERVED for /092. Delta
  expressed vs ANCHOR 1. Holding-time predictor for a feature-only axis (Δ ≈ 0.0 candles).
  /076 trade-selection sub-channel falsifier pre-registered (+1.0 candle cap). OOS/IS ratio
  gate (>3.0 = SUSPICIOUS) and OOS-DOMINANT sub-mode pre-registered (Section 4.4).
- Section 5 (Risk Mitigation): PASS — 7-primitive gate stack declared UNCHANGED. Dominant
  risk (R-feature: overfit via feature expansion) mitigated by Category-2 construction
  (orthogonal T2), single-feature discipline, 3-seed ensemble. Look-ahead risk (R-leakage)
  mitigated by .shift(1) discipline and mandatory spike-perturbation test. Historical effect
  comparison vs /082's 4-feature addition.
- Section 6 (Risk Management Design): PASS — 7-primitive table present. All primitives
  declared UNCHANGED. Gate #5 (feature z-score OOD) noted to marginally increase fire rate
  (one more feature in vector). Regime coverage: new feature itself a regime-conditioning
  device.
- Section 7 (Failure-Mode Prediction): PASS — PROMISING-INERT as the leading mode (≈45%),
  probability grounded in T3 quick-probe (rank 14.0/15 mean; mean accuracy lift −0.0016) and
  cycle-track record. SUSPICIOUS-OOS-DOMINANT (≈20%), NEGATIVE (≈15%), PROMISING (≈20%)
  all enumerated with mechanisms. Probabilities internally consistent and honest (central
  estimate does not float PROMISING above the evidence).
- Section 8 (MERGE/NO-MERGE Criteria): PASS — LOCKED taxonomy declared, all thresholds
  pre-registered vs ANCHOR 1 (/084). Five-condition PROMISING gate (IS Δ ≥ +0.10, OOS Δ ≥
  −0.10, CPCV frac_positive_paths ≥ 0.50, NOT SUSPICIOUS, importance rank ≤10 AND
  absolute ≥30 for ≥1 symbol). SUSPICIOUS fires before PROMISING (disjunctive precedence).
  INERT defined as IS/OOS Δ inside noise bands OR importance rank ≥14/15 in ≥2 symbols.
  Only PROMISING advances to /092 CONFIRMATION bundle. An EXPLORATION never updates
  BASELINE_V3.md — stated explicitly.
- Section 9 (Library Stack): PASS — No new libraries. Pinned stack listed: lightgbm 4.6.0,
  optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0,
  statsmodels 0.14.6, pyarrow 23.0.1. Feature is pure numpy/pandas arithmetic. EDA scripts
  use already-pinned libraries.
- Section 10 (QR Audit Trail): PASS — Orchestrator direction (Direction 3, pooled model)
  documented and formally superseded by the three IS-only EDA probes (all NOT SUPPORTED).
  Literature-research path documented: Cakici et al. (2024), Gu/Kelly/Xiu (NBER w25398),
  BIS WP 1087. Selection criteria chain ("literature says X → axis is Y") explicit. EDA SHA
  and brief SHA backfilled.

---

## Funding-CLOSED Differentiation Adjudication (KEY GATE ITEM)

**Verdict: SUBSTANTIVE DIFFERENTIATION — PASS. The /085 axis is NOT a re-tread of the
closed v3 funding axis.**

Reasoning:

The closed v3 funding axis consists of 4 data points — iter-v3/019 (`funding_rate_zscore_30`,
Category-1 standalone z-score), iter-v3/023 (retest with extended window, still
`funding_rate_zscore_30`), iter-v3/024 (`btc_funding_rate_zscore_30`, cross-asset variant),
and iter-v3/082 (the 4-channel funding family: `funding_sign_persist_9`, `funding_momentum_3`,
`funding_accel_3`, `funding_price_divergence_6`). Every one of these fed funding data as a
DIRECT model feature — a column the LightGBM tree could split on independently. The uniform
verdict across all four was INERT-by-importance: the tree never learned to split on raw funding.

iter-v3/085's `funding_regime_momentum_5d` is structurally different in one load-bearing way:
the funding rate is NOT a model feature column at all. It enters exclusively as the `sign()`
argument inside the composed feature's construction. The tree receives a single column —
`funding_regime_momentum_5d` — that is the element-wise product of the already-baseline
`regime_momentum_signed_5d` and the discrete sign of the funding z-score. The tree cannot
decompose that product into its funding leg; it splits on the composed signal. This is the
Category-2 composed-feature construction defined by `feedback_v3_engineered_feature_pivot.md`
(the exact family of the only PROVEN-PROMISING v3 axis, `regime_momentum_signed_5d` from
iter-v3/025). The closed-axis failure mode — trees never splitting on raw funding — cannot
fire here because funding is not a splittable column.

The literal-name bans (`funding_rate_zscore_30`, `btc_funding_rate_zscore_30`) are verified
ABSENT: inspection of `V3_FEATURE_COLUMNS_TOP_N` in `features_v3/__init__.py` and the runner's
per-symbol feature assertions confirms neither literal name is present. The runner also
explicitly asserts the 4 /082 funding-family columns ABSENT. `funding_regime_momentum_5d`
is a different column name and a different construction. There is no re-tread.

---

## Code-Readiness Verification

1. ITERATION_LABEL: `run_baseline_v3.py` line 131 — `ITERATION_LABEL = "v3-085"`. PASS.

2. V3_FEATURE_COLUMNS_TOP_N: `features_v3/__init__.py` — 15-entry tuple; the 14 BASELINE_V3
   /059 anchor features are present in declared order; `funding_regime_momentum_5d` is the
   15th entry. The pre-flight count assertion in `run_baseline_v3.py` checks `n != 15` and
   raises `RuntimeError`. The by-literal assertion checks `"funding_regime_momentum_5d" not
   in V3_FEATURE_COLUMNS`. Both enforced. PASS.

3. Feature computation — look-ahead-clean audit:
   `compute_funding_regime_momentum_5d` in `engineered_v3.py` (lines 946–1030):
   - `funding_z_30` construction at lines 1016–1022: `fr_lag = r.shift(1)` applied BEFORE
     both the 30-bar rolling mean and 30-bar rolling std. Bar t's funding rate enters the
     numerator (`r - fr_lag.rolling(30).mean()`) but the denominator's rolling window uses
     `fr_lag` (the shifted series), so bar t's own settlement does NOT enter its own z-score
     denominator. This matches the brief formula exactly.
   - `regime_momentum_signed_5d` is a verified past-only column (ret_5d uses `log_close.shift(15)`;
     hurst_100 is a 100-bar trailing R/S window).
   - The composed feature at line 1027–1029: element-wise product of two past-only series.
   No look-ahead. PASS.

4. GROUP_REGISTRY: `features_v3/__init__.py` line 85 — `"funding_regime_momentum_v3":
   add_funding_regime_momentum_v3_features` registered AFTER `"engineered_v3"` (line 78).
   The test `test_group_registry_contains_funding_regime_momentum` asserts this ordering
   at runtime. PASS.

5. Config-accretion 11-knob `_canonical_v059` check: the 11 RiskV3 knobs all remain
   /059-canonical (runner lines 937–955). Feature axes do NOT appear in this table — the
   brief documents the 14→15 feature count change as the declared axis (runner comment block
   + brief), not as a knob-drift. The check still fires for any unintended RiskV3 config
   drift. PASS.

6. Tests: `tests/features_v3/test_funding_regime_momentum_v3.py` — 12 tests present:
   import smoke, composition correctness, past-only spike-perturbation (THE MANDATED TEST),
   funding-z shift discipline, NaN warm-up, sign exactness, missing-primitive graceful
   fallback, idempotency, GROUP_REGISTRY smoke + FileNotFoundError + KeyError. Ran:
   `uv run pytest tests/features_v3/ tests/strategies/ml/ -q` → 430 passed, 3 skipped.
   PASS.

7. Ruff: `uv run ruff check` on changed files → All checks passed. PASS.

8. Track isolation: `features_v3/__init__.py` and `engineered_v3.py` contain no imports from
   `crypto_trade.features` (v1) or `crypto_trade.features_v2` (v2). PASS.

---

## Phase 6 Pre-Work Note

The 3 v3 feature parquets (BCH/LDO/TRX) need regeneration before the backtest to materialize
the new `funding_regime_momentum_5d` column. The funding-rate CSVs at
`data/funding_rates/{BCH,LDO,TRX}USDT.csv` already exist (100% IS coverage per brief T4).
Phase 6 must run `uv run crypto-trade features --track v3` (or the runner's
`_generate_v3_features` entry point) for all 3 symbols BEFORE `uv run python
run_baseline_v3.py --exploration --n-trials 35 --clean-oof`. Data freshness check (8h kline
CSVs ≤ 16h stale) must pass first.

---

## Status

OVERALL: PASS — Phase 6 may proceed.
