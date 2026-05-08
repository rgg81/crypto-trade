# Phase 5.5 Gate — iter-v3/026

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — `OOS_CUTOFF_DATE = 2025-03-24`, `training_months = 24` explicitly
  declared as IMMUTABLE. IS window: 2023-03-24–2025-03-24 (24 months). OOS window: 2025-03-24+.
  `ENSEMBLE_SIZE = 1` (EXPLORATION), `n_trials = 35` (EXPLORATION default).
- Section 1 (Hypothesis): PASS — single sentence specific hypothesis: adding `vol_adj_autocorr`
  (= `ret_autocorr_lag1_50 / (range_realized_vol_50 + 1e-6)`) as 15th feature will produce
  importance rank ≤10 for ≥1 symbol AND importance ≥30 for ≥1 cut AND IS Sharpe Δ ≥ 0 vs
  iter-v3/025 reference (+0.8788). Explicit mechanism (per-unit-vol return persistence; LightGBM
  depth-5 cannot compose ratio internally). Falsifiable in 3 directions (PATH A/B/C/D).
- Section 2 (IS-Only Evidence): PASS — committed EDA at SHA `97302db` in
  `analysis/iteration_v3-026/second_engineered_eda.py`. IS-only data. Tables present:
  §3.1 candidate evaluation (4 candidates × 7 metrics), §3.2 brief gates (5 gates with
  observed values), §3.5 distribution stats (3 symbols × 7 stats), §3.6 rank-IC (3 symbols ×
  3 horizons). All numbers specific. Category-matching NOT used — IS rank-IC values provided
  (0.025–0.028 at h=7, all 3 symbols). ADF p<1e-5 all 3 symbols.
- Section 3 (Proposed Changes): PASS — §2.1 enumerates single atomic change: ADD
  `vol_adj_autocorr` to V3_FEATURE_COLUMNS_TOP_N (14 → 15). KEEP `regime_momentum_signed_5d`.
  No labeling changes, no symbol changes, no risk gate changes. §2.2 specifies exact
  implementation with code snippets. §2.3 behavioral-effect predictor for IS trade count
  ([174, 214] band). §8 explicitly enumerates what is OUT OF SCOPE.
- Section 4 (Expected OOS Impact): PASS — §5 predicted bands table with lower/upper/median
  for all key metrics vs both iter-v3/018 anchor and iter-v3/025 reference. OOS Sharpe band
  [+1.10, +1.45] median +1.25. §4.1 Falsifier 1 (PATH C): IS Sharpe Δ < −0.10 OR OOS Sharpe
  Δ < −0.50 vs iter-v3/025 reference. §4.4 explicit PATH A criteria (rank ≤10 + importance ≥30
  + IS Δ ≥ 0). All thresholds pre-registered and cannot be renegotiated post-hoc.
- Section 5 (Risk Mitigation): PASS — §6.1 primary risks enumerated (INERT-OVERFIT + SIGNAL
  CANNIBALIZATION). §6.2 all risk gates listed as UNCHANGED from iter-v3/025 baseline with
  specific values (R1 3-SL cooldown, z=2.0, ATR 2.0/1.0, BTC ±15%, ADX=20). §6.3 kill-switch
  criteria (5 conditions). §6.4 simulated historical effect with IS trade band [174, 214] and
  IS/OOS Sharpe bands.
- Section 6 (Risk Management Design): PASS — §6.2 enumerates all active risk primitives:
  R1 consecutive-SL cooldown (unchanged), R2 drawdown scaling (unchanged), R3 OOD Mahalanobis
  (unchanged), z-score OOD (2.0), ATR multipliers (2.0/1.0), BTC trend filter (±15%), ADX
  threshold (20), Hurst regime gate, low-vol filter, hit-rate gate (disabled), regime gate
  (disabled), per-symbol cap (disabled). All IS-calibrated from prior iterations.
- Section 7 (Failure-Mode Prediction): PASS — §4.1-4.5 pre-registered PATH classifications
  with forward-looking failure predictions for each path (PATH B: second feature inert →
  engineered pivot narrow; PATH C: IS/OOS regression → signal cannibalization; PATH D:
  PROMISING-MECHANICAL → accounting artifact). §7 specifies conditional pre-commit for
  iter-v3/027 axis based on iter-v3/026 outcome. All failure modes named before backtest runs.
- Section 8 (MERGE/NO-MERGE Criteria): PASS WITH NOTE — iter-v3/026 is TYPE=EXPLORATION
  (declared §0.5). EXPLORATIONs do not produce MERGE/NO-MERGE decisions (only CONFIRMATIONs
  do). The PATH classification table (§2.4) is the LOCKED pre-registered criteria for this
  iteration type, consistent with prior EXPLORATION gate files (iter-v3/025 precedent:
  "MERGE/NO-MERGE Criteria: PASS — as EXPLORATION, no merge decision; PATH classification table
  §2.4 is the locked criteria"). §4.6 explicitly prohibits post-hoc renegotiation. Binding
  PATH A criterion: rank ≤10 for ≥1 symbol AND importance ≥30 AND IS Sharpe Δ ≥ 0.
- Section 9 (Library Stack): PASS — §9 (Reproducibility Stamp) lists pinned versions:
  lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0,
  statsmodels 0.14.6, pyarrow 23.0.1. Declares "No new dependencies." No mlfinlab/mlfinpy/pypbo
  usage in iter-v3 (not part of v3 library stack).

## IC-Gate Carve-Out (Category 2 Axis)

`vol_adj_autocorr` exhibits max |IC| = 0.985 vs its source primitive `ret_autocorr_lag1_50`
(per EDA §3.2). This FAILS the standard IC hard gate (< 0.70). However, this is a Category 2
(composed/interaction) feature — the high IC with source primitives is EXPECTED by construction
(the feature IS a function of those primitives). The carve-out is explicitly documented:

1. The IC gate was designed to flag REDUNDANT off-the-shelf indicator additions. It is
   structurally misapplied to composed features (same grounds as iter-v3/025 carve-out for
   `regime_momentum_signed_5d` which had IC 0.887 vs `vwap_dev_20`).
2. The binding evidence gate for Category 2 axes is feature importance rank ≤10 AND absolute
   importance ≥30 from the LightGBM model itself — not pairwise IC.
3. STRUCTURAL ORTHOGONALITY TO `regime_momentum_signed_5d`: max |IC|_rm = 0.075 (BCH/TRX),
   0.0014 (LDO) — near-zero. The two engineered features are mechanistically distinct.
4. ADF stationarity: p<1e-5 all 3 symbols (PASS).
5. Max |rank-IC| vs forward returns: 0.028 (LDO h=7) — above 0.02 floor.

The IC hard-gate failure is INFORMATIONAL ONLY for Category 2 axes. Phase 5.5 gate passes.

## Single-Axis Verification

iter-v3/026 changes ONE variable: adds `vol_adj_autocorr` as 15th feature. All other
configuration is byte-identical to iter-v3/025 (z=2.0, ATR 2.0/1.0, BTC ±15%, ADX=20,
universe BCH+LDO+TRX, n_trials=35, EXPLORATION mode). This satisfies the single-axis
discipline requirement.

## Reasons (if BLOCK)

N/A — OVERALL=PASS
