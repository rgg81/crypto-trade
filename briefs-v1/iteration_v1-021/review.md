# Phase 7.5 Critic Review — iter-v1/021

OVERALL: BLOCK-PENDING-FIX — Pool Model_A feature_importance write defect renders H2 falsifier non-evaluable; H1 evidence + Layers A/B/C otherwise PASS, single isolated defect; QE patch + targeted re-run sufficient.

## Iteration Type
TYPE: EXPLORATION — cycle-3 #6 of 10 — METHODOLOGY PIVOT subtype (diagnostic)

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
IS-only EDA. Foundation invariants hold. `walk_forward.py:113` unchanged. 4 mandated regression tests at `tests/test_lookahead_embargo.py` lines 120/163/232/261.

### Check 2 — Embargo Width: PASS
2-sym Pool at 8h interval, label_timeout=10080 min → embargo=22 candles. cv_gap=44 (2 syms × 22). Foundation discipline intact.

### Check 3 — Multiple-Testing Correction: FAIL (informational only for METHODOLOGY-PIVOT)
DSR=0.0 / PSR=2.7e-05 / PBO=null. n_eff=21 at n_trials=21. Carry-forward N_eff PCA architectural debt per /005 catalog row. For TYPE=METHODOLOGY-PIVOT, Check 3 INFORMATIONAL only — iteration is non-edge-finding by design.

### Check 4 — IC Correlation: PASS (vacuous; no new features)
V1_FEATURE_COLUMNS_PRUNED 40-col set unchanged.

### Check 5 — ADF Stationarity: PASS
40/40 features cleared bonferroni_pass + raw_pass at IS extent.

### Check 6 — Pareto Dominance: N/A (single-seed EXPLORATION)

### Check 7 — Reproducibility: PASS
HEAD `25d070e`; explicit `feature_columns=active_feature_columns`; atomic write for params parquet; iter-stamped paths.

### Check 8 — Hypothesis-Implementation Alignment: PASS (with H2 instrumentation-defect carve-out)
Brief §3.1 (params_persist_path) + §3.2 (_write_feature_importance) + /021 dispatch branch all match brief spec. NO scope creep. However: H2 evaluation INSTRUMENTATION-BLOCKED because `_write_feature_importance` reads `_strat_a.inner._models` post-dispatch but `LightGbmStrategy._models` is re-assigned each walk-forward month — captures stale/empty references for Pool model. **`feature_importance_POOL_Model_A.csv` total gain = 0.0 across 40 features.** BTC-only Model_H wrote correctly (98,881 gain). Brief Section 12 explicitly contemplates this scenario → BLOCK-PENDING-FIX.

### Check 13 — Anti-Pattern Static Scan: PASS
A1-A13 all clean. Atomic write for params parquet (A7 PASS).

### Check 14 — Axis Family Validation: PASS
`methodology-pivot` NEW 12th family. Rotation VALID; prior 5 distinct.

## Verdict Synthesis

**Concern #1 (BLOCK-PENDING-FIX vs proceed with H1-only)**: Brief Section 12 rollback protocol explicitly contemplates "feature_importance.csv emission fails but determinism holds" → BLOCK-PENDING-FIX. The 9-cell joint matrix at Section 4.3 has NO UNDETERMINED H2 row. Coercing UNDETERMINED-as-MIXED is post-hoc rationalization the brief was designed to prevent. **VERDICT: BLOCK-PENDING-FIX.**

**Concern #2 (Layer B BLOCK-FINAL letter vs intent)**: Brief Section 4.4 Layer B was structurally ambiguous between "Model A slice of 5-sym baseline" vs "2-sym Pool same-config repeat-run". The params_persist_path code path is structurally a true no-op (only fires AFTER `study.optimize()` completes). **Adjudication: Layer B = PASS-WITH-NOTE** (not BLOCK-FINAL).

**Concern #3 (H1 verdict cell at BORDERLINE)**: 9-cell joint matrix has no UNDETERMINED H2. Closing /021 without fixing H2 forces post-hoc verdict assignment — brief was designed to prevent this.

**Concern #4 (/022 routing)**: HIGH-CONFIDENCE gate (≥6 + ≥2 key) NOT met by H1 BORDERLINE (4/10 + 1/4 key). Even if post-fix H2 lands CONFIRMED, /022 routes to LTC-only (cadence-preserved), NOT /027 acceleration.

**Concern #5 (Cadence position)**: Post-fix, /021 still counts as 1 EXPLORATION. /022 is the 7th; 3 more before /027 absent acceleration trigger.

## H1 Evidence (PASS — carries forward to post-fix verdict)

| Param | % > 0.30 |
|---|---:|
| confidence_threshold | **54.7%** |
| n_estimators | 43.4% |
| max_depth | **73.6%** |
| num_leaves | 49.1% |
| learning_rate | 35.9% |
| subsample | **54.7%** |
| colsample_bytree | 43.4% |
| min_child_samples | 47.2% |
| reg_alpha | 39.6% |
| reg_lambda | **60.4%** |

**4/10 shifted on ≥50% (CONFIRMED BORDERLINE band).** Only 1/4 key params shifted. HIGH-CONFIDENCE gate not met.

## Recommendations to QR (for post-fix rerun + /022 brief)

1. **Fix `_write_feature_importance` Pool-CSV write defect** as SINGLE diff. Two patch options:
   (a) Extend `_train_for_month` to append per-month `feature_importances_` to a `_per_month_fi_log` list on the strategy
   (b) Bind post-dispatch reference to snapshot taken at LAST walk-forward month
   Match v3 reference at `run_baseline_v3.py:2730-2818`.

2. **Specify Layer B anchor unambiguously** in future methodology-pivot briefs. /021 Layer B was ambiguous between 5-sym baseline slice vs 2-sym Pool repeat-run.

3. **Forward-binding mandate for /022 brief**: H1 verdict-cell at post-fix /021 MUST be one of pre-registered 9 cells in Section 4.3. NO UNDETERMINED-as-MIXED coercion. If H2 instrumentation fails again after rerun, /021 closes EXPLORATION-NEGATIVE.

## BLOCK-PENDING-FIX Rerun Protocol

- **Specific defect**: `_write_feature_importance` access to `_strat_a.inner._models` at post-dispatch time captures stale/empty Pool model references. BTC-only correctly populated; Pool all zeros.
- **Required fix**: Re-wire to either (a) accumulate per-month FI during walk-forward, OR (b) bind post-dispatch snapshot to last-month state. v3 reference at `run_baseline_v3.py:2730-2818`.
- **Re-eval scope after fix**: Pool Model A side only (BTC-only Model H need NOT re-run). Estimated 15-25 min targeted re-run.
- **params_persist_path parquet does NOT need regeneration** — H1 already evaluable at CONFIRMED BORDERLINE.
- **Layer A, Layer B (PASS-WITH-NOTE), Layer C, H1 falsifier carry forward as PASS.**
- **Final verdict after rerun**: focused on H2 falsifier + Check 8 re-check. Outcome ∈ {EXPLORATION-PROMISING-METHODOLOGY, EXPLORATION-NEGATIVE, BLOCK-FINAL}. NO recursion beyond single rerun.
- **NOT eligible for /022 = /027 acceleration** regardless (H1 BORDERLINE; HIGH-CONFIDENCE gate not met).
- **Engineering report**: MUST commit alongside regenerated CSVs (3rd cycle-3 incident per Section 10.4).

## Path Forward (mandatory on BLOCK)

If post-fix rerun verdict is BLOCK-FINAL or EXPLORATION-NEGATIVE, /022 alternatives from families NOT used in prior 5 EXPLORATIONs (/016-/020):

1. **R5 regime-gate trial-level integration** — family: `risk-primitive` — rolling-90d BTC vol kill switch (orthogonal to per-cohort isolation; tests /020 BTC-isolation failure bypass).

2. **N_eff PCA architectural refactor** — family: `methodology-substrate-test` — fix the n_eff=n_trials pathological ceiling (5-consecutive blocking debt). Unblocks DSR/PSR/PBO gates at /027 CONFIRMATION.

3. **3-seed inner ensemble at EXPLORATION budget** — family: `methodology-substrate-test` — break basin-lock pattern across /002-/005; ensemble_size=3 with seeds [42,123,456] at existing 2-sym Pool config.
