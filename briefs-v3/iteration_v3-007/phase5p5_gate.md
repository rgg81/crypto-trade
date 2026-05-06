# Phase 5.5 Gate — iter-v3/007

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` confirmed UNCHANGED. `ENSEMBLE_SIZE=1`, `colsample_bytree=1.0`, `n_trials=10` are SET BY `--exploration` flag (not mutations of sacred constants). IS window `2022-09-24 → 2025-03-23 23:59:59 UTC`, OOS window `2025-03-24 00:00:00 UTC → data-extent`. Walk-forward unit (monthly retrain, 24-month rolling window) UNCHANGED.
- Section 0.5 (Iteration Type Declaration): PASS — `TYPE: EXPLORATION` declared explicitly in first line of Section 0.5. Justification paragraph references skill SHA `f0f8b84`, user direction 2026-05-06, the `--exploration` mode parameters, Critic scoring scope (Checks 1,2,4,5,6,8 full enforcement; Check 3 edge informational only), and expected verdict labels (`EXPLORATION-PROMISING` / `EXPLORATION-NEGATIVE`). Justification is specific and satisfies the "one paragraph, why EXPLORATION not CONFIRMATION" requirement.
- Section 1 (Hypothesis): PASS — single sentence with specific testable target: reducing `V3_FEATURE_COLUMNS` from 34 to top-14 by mean importance rank, running full v3 universe with `--exploration`, will produce IS monthly Sharpe > +0.5. Mechanism stated (low-importance features dilute LightGBM node gain under `colsample=1.0`). Not vague.
- Section 2 (IS-Only Evidence): PASS — committed script: `analysis/iteration_v3-007/feature_importance_topN_demo.py` at SHA `a394314` (timestamp 2026-05-06 01:59:40). Brief committed at SHA `d78dc2d` (timestamp 2026-05-06 02:04:39). Analysis predates brief by 5 minutes: CONFIRMED. Script reads only `reports-v3/iteration_v3-006/in_sample/feature_importance.csv` and `reports-v3/iteration_v3-003/in_sample/feature_importance.csv` — both computed inside walk-forward training on IS candles only. No OOS data contact. Three output artifacts committed alongside script (`top_n_features.csv`, `summary.json`, `synthesis.md`). Tables in §2.1 and §2.2 match `top_n_features.csv` rows and `summary.json` selected/dropped lists exactly. The rank-14 / rank-15 boundary argument (§2.3) is numerically justified.
- Section 3 (Proposed Changes): PASS — symbols UNCHANGED (full v3 universe BCH+MKR+LDO+TRX, verified disjoint from V3_EXCLUDED_SYMBOLS). Labeling UNCHANGED (triple-barrier ATR-scaled, timeout=21 candles, gap=88). Features reduced 34→14 with explicit enumerated dropped list (20 features named). Risk gates UNCHANGED (7-primitive table carried from iter-v3/006). Section 3.5 decomposes into 3 atomic sub-fixes with per-sub-fix specs and individual verifier commands. Section 3.6 reconciliation table has exactly 10 rows each with code path, file artifact, and executable verifier command — NO empty cells. Section 3.8 provides inheritance preconditions including 35/35 test requirement. "One variable at a time" satisfied: only `V3_FEATURE_COLUMNS` changes.
- Section 3.5 (Sub-fix Decomposition): PASS — 3 sub-fixes enumerated: (1) add `V3_FEATURE_COLUMNS_TOP_N` constant + reassign, (2) update `_verify_feature_columns()` assert from 34→14, (3) run `--exploration --seeds 1`. Each has a spec and a verifier.
- Section 3.6 (Reconciliation Cells Executable): PASS — all 10 reconciliation rows have non-prose verifier commands (`python -c "..."` or `grep ...` or `test -f ...`). Zero prose-only rows. Each verifier targets a specific file artifact.
- Section 4 (Expected OOS Impact): PASS — predicted IS Sharpe range [+0.2, +0.8] with median +0.5. Four numerical falsifiers pre-registered (§4.3). EXPLORATION pathway explicitly states headline metrics are guidance not gates for this TYPE. Falsifiers are specific and actionable.
- Section 5 (Risk Mitigation): PASS — 3 NEW structural safeguards (§5.1: `colsample=1.0`, TYPE=EXPLORATION declaration, 60-min wall-clock cap) plus 3 inherited methodology-pipeline safeguards (§5.2: 35 adversarial tests, reconciliation table, pre-flight len-check). No new model-level risks introduced (feature subsetting only removes already-audited features). Gate-feature-column independence explicitly argued (§6.1 note: `atr_pct_rank_200` dropped from training features but gates read parquet directly).
- Section 6 (Risk Management Design): PASS — 7-primitive table with fire-rate predictions and regime coverage identical to iter-v3/006. Important gate-feature independence note: primitives 1, 4, 5 use `atr_pct_rank_200` which is dropped from `V3_FEATURE_COLUMNS_TOP_N`, but the brief explicitly states gates read from the parquet DataFrame (all 34 features remain computed), not from the model's feature list. Engineer must verify this in Phase 6 pre-flight step 4.
- Section 7 (Failure-Mode Prediction): PASS — 5 predictions total: 3 process-level (P1: wrong column names / missing imports, P2: hidden `ENSEMBLE_SIZE=5` downstream dependency, P3: wall-clock overshoot) and 2 model-level (P4: IS Sharpe stays negative, P5: IS Sharpe shifts positively). Minimum requirement of ≥3 process-level predictions met. Each prediction includes detection signal and mitigation. Probabilities are Bayesian-calibrated and explicitly labelled.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — scoped correctly for EXPLORATION. CONFIRMATION-style thresholds (DSR > 0.95, PSR > 0.95, OOS Sharpe > 1.0) are explicitly stated as NOT IN SCOPE and not used as active gates. 10 EXPLORATION-PROMISING criteria enumerated. EXPLORATION-NEGATIVE and NO-MERGE-PROCESS pathways defined. Verdict interpretation table maps each outcome to next-iteration action. No post-hoc rationalization possible given pre-registered criteria.
- Section 9 (Library Stack): PASS — 8 packages declared (numpy, scipy, statsmodels, scikit-learn, lightgbm, pytest, pandas, pyarrow) with license, usage, and fallback columns. No new external dependencies. Aggregator strategy unchanged from iter-v3/006. Reproducibility stamp spec included.

## Commit-ordering Audit

- SHA `bce50c8` (`--exploration` flag, 2026-05-06 01:52:14) → committed BEFORE brief
- SHA `f0f8b84` (skill update, 2026-05-06 01:55:12) → committed BEFORE brief
- SHA `a394314` (analysis script + artifacts, 2026-05-06 01:59:40) → committed BEFORE brief at SHA `d78dc2d` (2026-05-06 02:04:39)

All three antecedents predate the brief. Phase 5.5 reproducibility requirement: SATISFIED.

## Pre-Phase-6 Preconditions (Engineer must verify)

The following must all be true before Phase 6 code edits begin:

1. `uv run pytest tests/strategies/ml/ -v` → 35/35 PASS at HEAD
2. `git log --oneline iteration-v3/007 -- run_baseline_v3.py | wc -l` ≥ 2 (SHA `9314db4` + SHA `bce50c8`)
3. `test -f tests/strategies/ml/test_outer_seed_propagation.py` → exists
4. `test -f tests/strategies/ml/test_per_cell_pbo_synthetic.py` → exists
5. `test -f tests/strategies/ml/test_ensemble_seed_propagation.py` → exists

Gate-feature independence check (Phase 6 step 4): confirm risk gate code references the parquet column for `atr_pct_rank_200`, `hurst_100`, and the z-score-OOD feature set — NOT the model's `feature_columns` argument.

## Reasons

None — OVERALL is PASS.
