# Phase 5.5 Gate — iter-v1/084

OVERALL: PASS

## Iteration Type (from Brief Section 0.5)
TYPE: SPECIALIST (single-coin cohort; NEW SYMBOL universe-extension — CRVUSDT)

## (v1) Axis Family + Rotation Status
FAMILY: per-cohort-specialization-CRV (under cycle-7 per-symbol regime-specialist mandate;
        standard 5-family rotation SUSPENDED per feedback_v1_cycle6_per_symbol_regime_specialist_mandate.md)
ROTATION_STATUS: VALID — CRV ∉ {DOT, ETH, BTC, AAVE} (live BUNDLE-002 cohorts) AND
                         ∉ {LINK, LTC, ATOM, ICP, FIL} (ALREADY-FAIL) AND
                         ∉ V1_EXCLUDED_SYMBOLS. Cohort-orthogonality enforced.

## (v1) HIGH-RISK Declaration
HIGH-RISK: YES — NEW SYMBOL + NEW feature column + NEW risk primitive stack; all three
           are HIGH-RISK triggers (Optuna training-objective domain altered).
           Mitigation: single-outer-seed=42 with 50-inner-seed averaging (DEFERRED to
           CONFIRMATION if PROMISING + basin-lottery vigilance fires).

## (v1) LM Master Response Verification
- briefs-v1/iteration_v1-084/lgbm_advisor.md exists: PASS
  (Phase 4.5 header present; HP direction, Feature Rec ×2, Saturation Flag ×3,
  Rejection list — all items addressed in Brief Section 3.5)
- Brief Section 3.5 addresses each LM Master recommendation:
  - HP no-change (hold lock): ADOPTED — Section 3.4 holds max_depth=5/num_leaves=31/50-seed lock
  - HP post-mortem n_estimators telemetry: ADOPTED (7.4 telemetry)
  - Feature Rec 1 (oi_price_divergence_30 GO + importance caveat): ADOPTED
  - Feature Rec 2 (no second OI variant): ADOPTED
  - Flag 1 (R-FADE INERT or over-veto): ADOPTED + HARDWIRED into F3 + control run requirement
  - Flag 2 (barely-positive baseline, bear-localized headroom): ADOPTED + HARDWIRED into F4
  - Flag 3 (hot-vol regime weighting): ADOPTED (7.4 telemetry)
  - Rejections (no num_leaves bump / class_weight / stacking): CONCURRED
  All items: PASS

## Cadence Check (v1)
- Wall-clock budget declared:
  - Declared: 2h hard cap (EXPLORATION default); honest note that methodology-lock runs
    ~5.5–8h per the /078, /083 SPECIALIST precedent (no mid-run kill-switch, overrun documented):
    PASS (matches established SPECIALIST methodology-lock precedent)
- SPECIALIST (not BUNDLE): IS regime-coverage justification N/A: N/A
- BUNDLE-only checks: N/A

## Per-Section Status
- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24 ✓; training_months=24 ✓;
  IS window 2023-03-24 → 2025-03-24; OOS window 2025-03-24 → present; data freshness < 16h ✓;
  leak-assertion `open_time < OOS_CUTOFF_MS` in all 4 EDA scripts ✓
- Section 0.5 (Iteration Type): PASS — TYPE: SPECIALIST; cycle-7 mandate context; wall-clock
  budget with honest methodology-lock note
- Section 0.6 (Architecture-Family Justification): PASS — per-cohort-specialization-CRV;
  mandate suspension rationale; prior 5 cohorts listed (/063 DOT /064 ETH /065 BTC /078 AAVE
  /083 FIL); rotation VALID (cohort-orthogonality enforced, symbol-disjoint check ✓)
- Section 1 (Hypothesis): PASS — ONE specific, falsifiable sentence: CRVUSDT specialist with
  reformed negative-baseline selector (trivial Sharpe +0.069 min-horizon; bear −0.924) + OI-
  price-divergence feature + R-FADE gate → strictly-accretive 5th BUNDLE-003 seat that dilutes
  BTC concentration. Specific mechanism + expected improvement stated. Not vague.
- Section 2 (IS-Only Evidence): PASS — committed scripts:
    analysis/iteration_v1-084/eda.py
    analysis/iteration_v1-084/eda_crv_deep.py
    analysis/iteration_v1-084/eda_gala_chz_axs_crv.py
    analysis/iteration_v1-084/eda_oi_fade_calib.py
  12-symbol pool sweep with trivial IS Sharpe at 3 horizons (5d/21d/50d); per-regime
  trivial Sharpe; NATR/autocorr/pooled-baseline shape; OI-divergence distribution;
  R-FADE fade_z calibration table. All enforce OOS_CUTOFF_MS leak-assertion.
- Section 2.5 (HIGH-RISK Axis Declaration): PASS — HIGH-RISK declared; 3 triggers stated;
  single-outer-seed mitigation with escalation clause; attribution-entanglement acknowledged
- Section 3 (Proposed Changes): PASS — 3.1 symbol (CRV); 3.2 feature (48→49, one column,
  LOCAL in V1_ITER084_FEATURE_COLUMNS; global V1_FEATURE_COLUMNS_PRUNED stays at 48);
  3.3 risk (R-FADE, stateless, post-aggregator, default OFF); 3.4 methodology (LOCKED);
  3.5 LM Master per-recommendation responses (all addressed, see LM Master check above)
- Section 4 (Expected OOS Impact): PASS — IS Sharpe +0.55 [+0.30, +0.80]; OOS ~+0.20
  [-0.30, +0.60]; explicit rejection threshold (OOS < 0.0 with F1-pass = rejected); 4 HARD
  falsifiers (F1 trade floor, F2 feature INERT, F3 R-FADE inert/over-veto, F4 TS-mom-beat);
  Bundle-layer falsifier FB1 (pred-corr < 0.50); verdict matrix
- Section 5 (Risk Mitigation): PASS — present as "Risk Mitigation (project-mandated section)"
  (line 391); content covers R1/R2/R3/R5 with IS-calibrated thresholds and simulated historical
  IS effect; R-FADE fire-rate IS estimate (≈1–4%); R1/R2 DISABLED rationale; concentration
  cap deferred to BUNDLE-003. Label deviation from template; content is complete.
- Section 6 (Risk Management Design): PASS — 5-row primitive table (R1/R2/R3/R5/R-FADE) with
  CRV settings, predicted IS fire-rate, predicted OOS fire-rate, regime coverage; compound
  cascade prediction; R-FADE frozen fade_z=2.0 FROZEN anti-tuning assertion documented
- Section 7 (Failure-Mode Prediction): PASS — 3 pre-registered failure modes: (1) R-FADE INERT
  [modal; F3]; (2) NEGATIVE-MOMENTUM-DOMINATED at reformed-selected symbol [reform-falsifying];
  (3) edge is single-month/single-regime accident [Flag 2 + /083 lesson #4]. Diagnostics named.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — 3-band verdict table (PROMISING-STRONG ≥+0.50,
  PROMISING-TENTATIVE +0.20–+0.50, NEGATIVE <+0.20 or F1/F2/F3/F4 fail); 6-row absolute
  hard gate table (IS trades ≥50; OOS trades ≥50/30–49/auto-reject; importance ≥30;
  R-FADE marginal effect; ML IS Sharpe vs trivial; pred-corr <0.50). Pre-registered before
  backtest. BUNDLE-003 merge gates noted as BUNDLE-layer (correctly deferred).
- Section 9 (Library Stack): PASS — Python/lightgbm/optuna/numpy/pandas/scikit-learn/scipy/
  quantstats with versions; no new third-party deps; mlfinlab/mlfinpy/pypbo/fracdiff not used
  in v1 SPECIALIST path (noted as CONFIRMATION/BUNDLE-layer only); track isolation confirmed.
- Section 11 (Bundle Composition & Parity): PASS — 11.A pairwise-disjoint assertion (CRV ∩
  {BTC,ETH,DOT,AAVE} = ∅); 11.B weights N/A by triviality; 11.C backtest-live parity
  (symbol-routed dispatch code snippet; R-FADE stateless; engine.py additions noted for
  BUNDLE-003 assembly); 11.D concentration trajectory; 11.E snapshot-validity inheritance

## Pairwise-Disjoint Check
CRVUSDT ∉ {DOT, ETH, BTC, AAVE} (BUNDLE-002 universe): PASS
CRVUSDT ∉ V1_EXCLUDED_SYMBOLS {SOL, XRP, DOGE, NEAR, BCH, LDO, TRX, BNB}: PASS
CRVUSDT ∉ ALREADY-FAIL {LINK, LTC, ATOM, ICP, FIL}: PASS

## Sacred Constants
OOS_CUTOFF_DATE = 2025-03-24: PASS (held in Section 0 + config.py + EDA leak assertions)
training_months = 24: PASS (Section 3.4 explicitly frozen)
Global V1_FEATURE_COLUMNS_PRUNED = 48: PASS (oi_price_divergence_30 is LOCAL to
  V1_ITER084_FEATURE_COLUMNS; global PRUNED unchanged; assert in __init__.py:213 passes)

## Architecture Isolation Verification
- V1_FEATURE_COLUMNS_PRUNED (global) = 48: PASS (runtime assertion __init__.py:213)
- V1_ITER084_FEATURE_COLUMNS (local CRV-only) = 49: PASS (runtime assertion __init__.py:225)
- oi_price_divergence_30 NOT in V1_FEATURE_COLUMNS_PRUNED: PASS
  (DOT/ETH/BTC/AAVE specialists unaffected; one-variable-at-a-time discipline held)
- run_baseline_v1.py dispatch: active_feature_columns = list(V1_ITER084_FEATURE_COLUMNS)
  for "v1-084" branch only: PASS

## EDA Scripts Committed
- analysis/iteration_v1-084/eda.py: COMMITTED
- analysis/iteration_v1-084/eda_crv_deep.py: COMMITTED
- analysis/iteration_v1-084/eda_gala_chz_axs_crv.py: COMMITTED
- analysis/iteration_v1-084/eda_oi_fade_calib.py: COMMITTED
All 4 mandate items covered: PASS

## Implementation Code Committed
- src/crypto_trade/features_v1/open_interest_v1.py (add_oi_price_divergence_30_feature): COMMITTED
- src/crypto_trade/features_v1/__init__.py (V1_FEATURE_COLUMNS_PRUNED=48 UNCHANGED;
  V1_ITER084_FEATURE_COLUMNS=49 LOCAL; assert ==48 and assert ==49 both present): COMMITTED
- src/crypto_trade/strategies/ml/lgbm.py (enable_oi_divergence_fade_gate,
  _apply_oi_divergence_fade_gate): COMMITTED
- run_iteration_084.py: COMMITTED
- tests/test_iteration_v1_084.py (34 tests, updated for LOCAL feature architecture): COMMITTED

## Test Status
PASS — 0 failures.
  - tests/features_v1/test_funding_v1.py: 23 passed (count-guard asserts n==48 PASS;
    global PRUNED confirmed 48 after test-fix correctly reverted the feature to LOCAL-only)
  - tests/features_v1/test_open_interest_v1.py: 23 passed (count-guard asserts n==48 PASS)
  - tests/test_iteration_v1_084.py: 34 passed (4 tests updated from V1_FEATURE_COLUMNS_PRUNED
    to V1_ITER084_FEATURE_COLUMNS to match LOCAL-only feature architecture after fix;
    1 positional test updated to reflect append-at-end construction of V1_ITER084_FEATURE_COLUMNS)
  Full suite: lint PASS on /084-specific files (ruff check); format PASS.

## Prior BLOCK Resolution
BLOCK cause (prior gate): 2 stale count-guard tests asserted n==48 but the global PRUNED
  had been incorrectly modified to 49 (feature added to global instead of local).
Diagnosis applied: "global-pruned-modified-REAL-BUG" — the fix reverted global PRUNED to 48
  and created V1_ITER084_FEATURE_COLUMNS (local) = PRUNED(48) + (oi_price_divergence_30,) = 49.
Additional fixes applied at this gate re-run:
  - tests/test_iteration_v1_084.py: 4 tests updated to reference V1_ITER084_FEATURE_COLUMNS
    (were referencing V1_FEATURE_COLUMNS_PRUNED, which now correctly stays at 48)
  - run_iteration_084.py docstring: 3 stale references to "V1_FEATURE_COLUMNS_PRUNED (48→49)"
    corrected to "V1_ITER084_FEATURE_COLUMNS (LOCAL; 49 cols)"
  All fixes lint-clean; 0 failures across full test scope.
