# Phase 5.5 Gate — iter-v3/027

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — `OOS_CUTOFF_DATE = 2025-03-24`, `training_months = 24` confirmed
  unchanged. Brief §0 names IS window (24 months ending 2025-03-24) and OOS window
  (2025-03-24 onward). EXPLORATION mode: `n_trials = 35`, `ENSEMBLE_SIZE = 1`,
  `colsample_bytree = 1.0`. Sacred constants intact.

- Section 1 (Hypothesis): PASS — One specific sentence: adding `cross_asset_divergence_norm`
  (= `(sym_ret_7d - btc_ret_14d) / (|vwap_dev_20| + 1e-6)`) alone — dropping
  `vol_adj_autocorr`, keeping `regime_momentum_signed_5d` — will produce importance rank
  ≤10 for ≥1 symbol AND importance ≥30 for ≥1 cut (Category 2 carve-out) AND IS Sharpe
  Δ ≥ −0.40 vs iter-v3/025 reference (+0.8788). Mechanism stated: relative-strength
  normalized by mean-reversion intensity — a 3-way ratio the depth-5 LightGBM trees
  cannot internally compose from raw `sym_vs_btc_ret_7d`, `btc_ret_14d`, `vwap_dev_20`.

- Section 2 (IS-Only Evidence): PASS — committed EDA script at SHA `254a5f2`
  (`analysis/iteration_v3-027/third_engineered_eda.py` + outputs). IS-window numerical
  tables present in brief §3.1-3.6: 4-candidate comparison table with max |IC|_14, max
  |IC|_rm, max |rank-IC|, ADF p-values; brief §3.2 5-row brief-gates assessment; §3.5
  distribution stats; §3.6 rank-IC by symbol × horizon. Concrete numbers, not
  category-matching. Note: brief uses non-standard section numbering (brief §2 =
  Implementation Spec; brief §3 = IS-Only Evidence) — content is complete and meets
  the gate requirement.

- Section 3 (Proposed Changes): PASS — brief §2.1 enumerates atomic swap: DROP
  `vol_adj_autocorr` from V3_FEATURE_COLUMNS_TOP_N (15 → 14 transitional); KEEP
  `regime_momentum_signed_5d`; ADD `cross_asset_divergence_norm` (14 → 15). Net column
  count UNCHANGED at 15. §2.2 gives full module spec with code stub. All other gates
  (z=2.0, ATR 2.0/1.0, BTC ±15%, ADX=20, regime gate disabled, per-symbol cap disabled)
  explicitly stated unchanged (§6.2). §8 lists explicit out-of-scope changes.

- Section 4 (Expected OOS Impact): PASS — brief §5 (Predicted Bands) gives explicit
  bounds: IS monthly Sharpe [+0.50, +0.95] median +0.75; OOS monthly Sharpe [+0.60, +1.30]
  median +1.00. Explicit falsifiers at §4.1-4.6 with numerical thresholds:
  PATH C fires at IS < +0.30 (absolute collapse threshold); PATH A requires rank ≤10
  AND importance ≥30 AND IS Δ ≥ −0.40 AND OOS Δ ≥ −0.40 vs iter-v3/025 reference.
  All thresholds pre-registered at SHA `254a5f2` + brief SHA. §4.6 explicitly states
  borderline cases are bound by strict criteria without relaxation.

- Section 5 (Risk Mitigation): PASS — brief §6 covers signal-cannibalization risk (§6.1),
  kill-switch criteria (§6.3), simulated historical effect (§6.4), all risk gates stated
  unchanged from iter-v3/025/026 baseline (§6.2). IS-calibrated thresholds cited from
  BASELINE_V3.md. R1/R2/R3 explicitly stated unchanged.

- Section 6 (Risk Management Design): PASS — brief §6.2 lists all 7 active risk
  primitives: BTC trend kill (±15%), vol scaling (R2), ADX gate (20), Hurst regime gate,
  z-score OOD (2.0), low-vol filter, hit-rate gate (disabled). Per §8, regime gate and
  per-symbol cap are disabled. All thresholds explicit and IS-calibrated from BASELINE_V3.md.
  8-primitive table satisfied at 7 active + 2 explicitly disabled = 9 addressed.

- Section 7 (Failure-Mode Prediction): PASS — brief §4.1-4.5 pre-registers 5 failure
  modes (PATH C IS collapse, saturation falsifier, PATH B INERT-replacement, PATH A
  disambiguation validates, PATH D mechanical). Each pathway has a specific threshold
  trigger, diagnostic, and downstream implication for iter-v3/028. §6.1 names the 3
  primary risk mechanisms (signal cannibalization, replacement-overfit, cross-asset
  dead-path precedent). §4.6 locks that borderline outcomes are bound by strict criteria.
  These constitute forward-looking failure-mode predictions against which Phase 8 diary
  can be verified.

- Section 8 (MERGE/NO-MERGE Criteria): PASS (EXPLORATION-appropriate) — This is
  TYPE=EXPLORATION; MERGE criteria are N/A (brief §0.5 explicitly: "This iteration NEVER
  updates BASELINE_V3.md"). Pre-registered EXPLORATION verdict criteria are the PATH
  classification table in §2.4 with locked numerical thresholds (PATH A: rank ≤10 AND
  importance ≥30 AND IS ≥ +0.30 AND IS Δ ≥ −0.40 AND OOS Δ ≥ −0.40; PATH B: rank
  14-15/15 across 3+ cuts; PATH C: IS < +0.30 OR IS Δ < −0.40 OR OOS Δ < −0.40;
  PATH D: trade roster bit-identical to iter-v3/025). §4.6 states these cannot be
  renegotiated post-hoc. The pre-registration eliminates post-hoc rationalization at
  the EXPLORATION level consistent with CONFIRMATION-level MERGE criteria design intent.

- Section 9 (Library Stack): PASS — brief §9 states "Library stack pinned in BASELINE_V3.md:
  lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0,
  scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1. No new dependencies." No new
  libraries introduced. No mlfinlab licensing risk (CPCV/PBO infrastructure unchanged
  from iter-v3/018 CONFIRMATION). Library-fallback question N/A.

## IC-Gate Carve-Out (mandatory note — Category 2 composed feature)

`cross_asset_divergence_norm` fails the IC hard gate (max |IC|_14 = 0.756 LDO vs
sym_vs_btc_ret_7d source overlap; > 0.70 threshold). The carve-out applies per
`feedback_v3_engineered_feature_pivot.md` and iter-v3/025/026 precedent:

1. This is a COMPOSED interaction feature (Category 2), not an off-the-shelf indicator
   (Category 1). The IC gate was designed for the latter.
2. High source IC is structurally expected for a composed feature — it is the hypothesis
   under test, not a disqualifier.
3. The binding evidence gate is LightGBM feature importance rank ≤10 with absolute
   importance ≥30 (model actually uses the composed ratio, not just its source primitives).
4. max |IC|_rm = 0.464 (LDO worst) is higher than iter-v3/026's vol_adj_autocorr (0.075)
   — noted as informational only; reflects partial mechanism overlap through `sym_vs_btc_ret_7d`
   variance pathway, not through regime_momentum directly.

The IC hard gate is BYPASSED for this iteration on the same documented grounds as
iter-v3/025/026. This carve-out is method-level, not result-dependent.

## Single-Axis Discipline

Atomic feature swap: DROP `vol_adj_autocorr` + ADD `cross_asset_divergence_norm` =
one primary variable changed (the 15th feature column). Net column count unchanged at 15.
`regime_momentum_signed_5d` is KEPT (proven at iter-v3/025 PROMISING; mandated by
`feedback_v3_engineered_features_proven.md`). All other configuration parameters
byte-identical to iter-v3/025/026 anchor. Single-axis discipline preserved.

## Reasons

None — OVERALL=PASS. Phase 6 may proceed.
