# Phase 5.5 Gate — iter-v3/025

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24 and training_months=24 confirmed
  unchanged. IS window: 2023-03-24 to 2025-03-23. OOS window: 2025-03-24 onward. Sacred
  constants immutable.

- Section 0.5 (Iteration Type Declaration): PASS — TYPE=EXPLORATION, cadence #7 of 10 in
  post-bootstrap cycle. FEATURE ENGINEERING pivot per Critic FINAL `5a47f5d` of iter-v3/024
  + user directive 2026-05-08. Single-axis discipline preserved: DROP
  btc_funding_rate_zscore_30 + ADD regime_momentum_signed_5d (14 → 13 → 14; net=14
  unchanged). Wall-clock budget <30 min target / 2h hard cap. Axis category explicitly
  declared as Category 2 (GENUINE FEATURE ENGINEERING — composed feature; NEW axis category
  in v3 catalog history).

- Section 1 (Hypothesis): PASS — Specific, falsifiable, one-mechanism. "Adding
  regime_momentum_signed_5d (= ret_5d × sign(hurst_100 − 0.5)) as the 14th feature will
  produce importance rank ≤10 for ≥1 symbol AND IS Sharpe Δ ≥ +0.10 if the
  regime-conditional momentum interaction is genuinely informative AND the LightGBM trees on
  the 13-feature stack cannot internally compose this interaction at depth-5." Mechanism
  explanation present (trending vs mean-reverting regime sign-flip). Direction symmetry
  discussed. Falsifiable in 3 directions (PATH A/B/C). NOT a vague "explore composed
  features" hypothesis.

- Section 2 (IS-Only Numerical Evidence): PASS — committed EDA at SHA `917605b`
  (`analysis/iteration_v3-025/feature_engineering_eda.py`). Tables present for 6 candidates
  (rank-IC × 3 symbols × 3 horizons, max |IC| vs all 13 V3_FEATURE_COLUMNS members, ADF
  p-values, distribution stats, composite leaderboard scores). Numerical evidence is on IS
  data only. Category-matching absent; all evidence is quantitative.

  NOTE: Section 3.3 IC hard-gate methodology decision — APPROVED WITH CARVE-OUT. See detail
  below.

- Section 3 (Proposed Changes): PASS — Enumerated atomically: (1) DROP
  btc_funding_rate_zscore_30 from V3_FEATURE_COLUMNS_TOP_N; (2) ADD
  regime_momentum_signed_5d to V3_FEATURE_COLUMNS_TOP_N; (3) net column count 14 (unchanged);
  (4) all other gates BYTE-IDENTICAL to iter-v3/018 anchor. Module structure spec provided
  (engineered_v3.py). GROUP_REGISTRY entry and insertion-order dependency documented. Past-only
  computation spec explicit (ret_5d uses shift, hurst_100 already past-only). No changes to
  labeling, symbols, model architecture, or risk gates.

- Section 4 (Expected OOS Impact): PASS — Predicted IS Sharpe band [+0.30, +0.55] median
  +0.40 (anchor +0.3788). Predicted OOS Sharpe band [+0.40, +0.65] median +0.50 (anchor
  +0.3869). OOS/IS ratio band [0.55, 1.50]. Feature importance rank band [7, 12] median 9.
  PATH A relaxation rationale explicit: rank ≤10 (not standard ≤7) for composed features,
  with importance ≥30 required. All 5 falsifiers (PATHs A/B/C/D + saturation falsifier)
  pre-registered with locked thresholds.

- Section 5 (Risk Mitigation): PASS — R1/R2/R3 and all 7 v3 risk primitives (BTC trend
  kill, vol scaling, ADX, Hurst regime, z-score OOD, low-vol filter, hit-rate disabled)
  explicitly stated as UNCHANGED from iter-v3/018 baseline. Primary risk identified as
  INERT-OVERFIT (same mechanism as iter-v3/023/024). Kill-switch criteria enumerated (5
  conditions). Historical effect simulation present (IS trade band [175, 209], IS Sharpe
  ±0.20, OOS Sharpe ±0.30).

- Section 6 (Risk Management Design): PASS — All 7+ v3 risk primitives accounted for with
  explicit "unchanged" statement per primitive. IS-calibrated thresholds identical to
  iter-v3/018 anchor. Saturation falsifier pre-registered (IS trades > 215 OR < 130).

- Section 7 (Failure-Mode Prediction): PASS — Pre-registered failure mode is INERT-OVERFIT:
  if regime_momentum_signed_5d ranks 14/14 across all symbols, the 14th feature at n_trials=35
  expands Optuna's search space along an uninformative dimension, producing IS-overfit
  hyperparameter trajectories that don't generalize to OOS. Conditional iter-v3/026 axis
  selection pre-registered for each PATH (A/B/C/D) outcome.

- Section 8 (MERGE/NO-MERGE Criteria): PASS — This is EXPLORATION (not a MERGE candidate);
  no MERGE criteria required. Equivalent gate is the PATH classification table (§2.4, LOCKED):
  PATH A PROMISING requires rank ≤10 + importance ≥30 + IS Δ ≥ +0.10. PATH B PROMISING-INERT
  requires rank 14/14 across ≥3 of 4 cuts. These criteria cannot be renegotiated post-hoc per
  §4.6 explicit statement.

- Section 9 (Library Stack Declaration): PASS — Section 0 explicitly states
  ENSEMBLE_SIZE=1 (SET BY --exploration) + n_trials=35 (PRELIMINARY-VALIDATED through 5 prior
  EXPLORATIONs) + colsample_bytree=1.0 (HARDCODED by --exploration). Parent baseline
  architecture SHA `c494d19` declared. Library stack pinned in BASELINE_V3.md
  (lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0,
  statsmodels 0.14.6, pyarrow 23.0.1). No new library dependencies introduced by this axis
  (regime_momentum_signed_5d uses only numpy + pandas primitives already available).

## IC-Gate Carve-Out Decision (Section 3.3 — METHODOLOGY DECISION)

The standard IC hard gate (max |IC| < 0.70) is APPROVED WITH CARVE-OUT for this Category 2
axis. Rationale approved:

1. regime_momentum_signed_5d max |IC| = 0.887 (BCH; vs vwap_dev_20) — exceeds the 0.70 hard
   gate AND the 0.50 brief target. Both failures are EXPECTED for a composed feature that
   multiplies two primitives, one of which (ret_5d, a 5-day log return) is partially correlated
   with a 20-bar VWAP deviation by construction.

2. The IC hard gate was designed to flag REDUNDANT off-the-shelf indicator additions. Applying it
   to a composed interaction feature is a category error: the IC elevation is structural
   (composed features always share variance with source primitives), NOT evidence of redundancy.

3. The HYPOTHESIS under test is precisely whether the COMPOSED form provides INTERACTION value
   the model cannot internally compute at depth-5. The empirical arbiter is feature importance
   rank from LightGBM itself, NOT pairwise IC.

4. Approved gate replacement for Category 2 axes: importance rank ≤10 AND absolute importance
   ≥30 for at least 1 symbol (PATH A threshold, §2.4). Codified in memory rule
   `feedback_v3_engineered_feature_pivot.md`.

This carve-out applies ONLY to Category 2 (composed/interaction) axes. Category 1 (off-the-
shelf indicator additions) remain subject to the IC hard gate < 0.70 without exception.

## Single-Axis Discipline Verification

The brief proposes exactly ONE primary change:
- DROP btc_funding_rate_zscore_30 (14 → 13)
- ADD regime_momentum_signed_5d (13 → 14)

This is an atomic swap, net column count unchanged at 14. All other configuration bytes are
identical to the iter-v3/018 BOOTSTRAP baseline. Single-axis discipline PRESERVED.

## Behavioral-Effect Predictor Verification (per feedback_v3_axis_saturation_predictor.md)

Section 2.3 provides a behavioral-effect predictor table (IS trades band [175, 209] based on 4
prior +1-feature iterations). Saturation falsifier threshold pre-registered (IS trades > 215 OR
< 130). This satisfies the axis-saturation-predictor requirement.

## Reasons (if BLOCK)

None. OVERALL=PASS.

## Engineer Action Items

Per brief Section 10 (Hand-Off to Engineer):
1. Implement `src/crypto_trade/features_v3/engineered_v3.py` (new module)
2. Add `engineered_v3` entry to GROUP_REGISTRY (after `cross_btc`, before `fracdiff` —
   alphabetical AND after regime group to ensure hurst_100 is computed first)
3. DROP `btc_funding_rate_zscore_30` from V3_FEATURE_COLUMNS_TOP_N
4. ADD `regime_momentum_signed_5d` to V3_FEATURE_COLUMNS_TOP_N
5. Update `_verify_feature_columns` in run_baseline_v3.py to assert:
   - len == 14
   - `regime_momentum_signed_5d` PRESENT
   - `btc_funding_rate_zscore_30` NOT present
   - `funding_rate_zscore_30` NOT present
   - `tbr_zscore_30` NOT present
   - `vwap_dev_50` NOT present
6. Update ITERATION_LABEL "v3-024" → "v3-025"
7. Write adversarial past-only test in `tests/features_v3/test_engineered_v3.py`
8. Run `uv run pytest tests/` — must PASS
9. Run `uv run ruff check . && uv run ruff format .` — must PASS
10. Commit code BEFORE running backtest
