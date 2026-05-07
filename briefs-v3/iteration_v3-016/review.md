# Phase 7.5 Critic Review — iter-v3/016 — FINAL (Round 2)

**OVERALL: EXPLORATION-NEGATIVE (clean)**

**Iteration Type**: EXPLORATION (single-axis: NEW model architecture LightGBM → XGBoost on iter-v3/013's 13-feature stack; first NEW model architecture in v3 catalog per `feedback_structural_over_knob_exploration.md` priority order Category 2)

**Round**: 2 FINAL (PRELIMINARY SHA `a20c54b`; QR Response SHA `06af055` accepted in full)

## QR Response Considered

QR's 5 clarifications fold cleanly into the verdict; all dispositioned with explicit pre-commits for iter-v3/017+ brief template and iter-v3/017 first commit:

1. **Clarification 1 (bit-identity disposition for §4.4 row 4 vs row 5 boundary)**: ACCEPTED. QR took resolution path (a) — verified per-symbol trade-roster non-bit-identity by inspection (BCH 92→87 = −5; LDO 22→24 = +2; TRX 95→106 = +11). No single symbol's trade count matches between iterations; bit-identity falsified by trade-count constraint alone (per-symbol count equality is necessary for bit-identity, and it fails on every symbol). §4.4 row 4 NULL-RESULT bit-identity test FAILS → row 5 NEGATIVE-clean fires unambiguously. The portfolio-aggregate +8 dilution that masks the per-symbol shifts is a coincidence of opposite-direction symbol moves; the row 5 verdict was structurally correct but textually under-justified in the engineering report. **Brief drafting weakness acknowledged**: row 5's `|Δ| ≥ 11` threshold is a saturation-falsifier artifact (`ceil(0.05 × 209)`) that misses cases like iter-v3/016 where opposite-direction per-symbol shifts mask through to portfolio aggregate. Pre-commit: row 5 condition becomes `"either |Δ| ≥ 11 OR per-symbol shift > 5 trades on any symbol"` for iter-v3/017+ brief template.

2. **Clarification 2 (importance-divergence: structural vs noise)**: ACCEPTED. QR acknowledged Critic's noise hypothesis as co-plausible alternative interpretation. Cannot fully discriminate at single-seed n_trials=10 budget where `n_eff=6` indicates sparsely-explored search region. Catalog row mandatory caveat: "importance-divergence finding NOT structurally validated; may be hyperparam-search artifact at n_trials=10 single-seed budget. Future re-test would require multi-seed XGBoost (≥5 outer seeds × ≥50 trials) where importance rankings stabilize under Optuna convergence." Structural divergence claim should NOT be propagated as established fact in iter-v3/017+ briefs without multi-seed re-validation.

3. **Clarification 3 (`_write_feature_importance` second defect)**: ACCEPTED. QR acknowledged the second defect (last-month-only aggregation) and the byte-identity of OOS↔IS importance CSVs. Pre-commit for iter-v3/017 first commit (LOAD-BEARING — cannot be deferred): adopt either Option A (modify `_train_for_month` to accumulate per-month importances; aggregate at report time) or Option B (drop OOS importance CSV, rename IS CSV to `model_importance_last_month.csv` to clarify scope). Option A preferred because it produces structurally correct artifact; Option B fast and removes misleading dual-CSV pattern. iter-v3/017 Engineer chooses A or B at first-commit time.

4. **Clarification 4 (saturation falsifier band tightening)**: ACCEPTED. QR accepted iter-v3/017+ brief template tightens to `[baseline_n_trades × 0.75, baseline_n_trades × 1.25]` (= [157, 261] for iter-v3/013 baseline 209), rounded to nearest integer. Prior `feedback_axis_saturation_predictor.md` formula `falsifier_threshold = ceil(1.2 × counterfactual_n_trades)` continues to apply for upper-bound saturation cap; lower-bound for NULL-RESULT classification tightens from "no explicit lower bound" to `floor(0.75 × baseline_n_trades)`.

5. **Clarification 5 (XGBoost catalog row scope)**: ACCEPTED. QR accepted Critic's distinction between scoped closure (n_trials=10 + cross-entropy + depth-wise growth defaults) and "all configurations". Three plausible configurations remain untested and should not be foreclosed: (a) Sharpe-objective Optuna, (b) drawdown-penalized loss, (c) `grow_policy='lossguide'` head-to-head. Catalog row text scopes the closure narrowly: "model-architecture axis closed at the tested configuration: n_trials=10 + cross-entropy objective + depth-wise growth defaults. XGBoost is NOT closed for all hyperparam configurations."

The classification flip from QE's NEGATIVE-recommended (per brief §4.4 row 5) → Critic+QR's NEGATIVE (clean) is verbatim concurrence — the QR Round 2 disposition strengthens the row 5 verdict with the missing per-symbol-count proof rather than altering it.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
Audited NEW XgboostStrategy implementation at `src/crypto_trade/strategies/ml/xgb.py` and `src/crypto_trade/strategies/ml/optimization_xgb.py` end-to-end. `_train_for_month` constructs train_indices via `(open_time >= train_start_ms) & (open_time < train_end_ms)` — strictly past of test month boundary. `_objective_xgb` uses `TimeSeriesSplit(n_splits=cv_splits, gap=cv_gap)` for sequential train/val temporal splits. `training_days` Optuna parameter trims via `cutoff_ms = val_start_time - training_days * 86_400_000` — past-only. NO new feature introduced this iteration; look-ahead audit on inherited 13-feature stack PASS.

### Check 2 — Embargo Width: PASS
Required gap = `(timeout_candles + 1) × n_symbols = (21 + 1) × 3 = 66` candles. Runner's `_verify_label_leakage_gap()` enforced; run.log line 2 records `Label-leakage gap: 66 PASS`. XGBoost path's `cv_gap = timeout_candles * n_symbols` at `xgb.py:430` (drops the `+1` margin compared to static REQUIRED_GAP but math equivalent at `22 × 3 = 66`).

### Check 3 — Multiple-Testing Correction (methodology axis): INFORMATIONAL (EXPLORATION carve-out)
DSR=0.0 (single-seed exploration artifact, expected), PBO=0.0889 (slight improvement vs iter-v3/013 0.103), PSR=0.9888, n_trials=30, n_eff=6. Per skill EXPLORATION cadence rule, edge-axis thresholds (DSR > 0.95, PSR > 0.95) are INFORMATIONAL not BLOCK. PBO 0.0889 < 0.4 PASS. n_eff dropped 7 → 6 (one Optuna dimension dropped under depthwise growth — `num_leaves` is no-op); principled and documented. Pathological per-cell PBO tails (LDOUSDT/2025-02 PBO=1.0, LDOUSDT/2026-02 PBO=0.9822, BCHUSDT/2023-06 PBO=0.904, LDOUSDT/2025-12 PBO=0.976) audit-trail-noted; cross-cell mean correctly dilutes them.

### Check 4 — IC Correlation: PASS
`ic_matrix.csv` 13×13 lower triangular reads identically to iter-v3/013 baseline (no new features introduced; 13 inherited). Maximum |IC| = `range_realized_vol_50 ↔ max_dd_window_50 = -0.685` (below 0.70 redundancy gate by 0.015 — tight margin but PASS). No NEW feature introduced this iteration.

### Check 5 — ADF Stationarity: PASS (with EXPLORATION-tolerated early-window concentration)
`adf_test.csv` reports 1657/2041 cells stationary (81.2%). 384 non-stationary cells concentrated in early IS months and at LDO listing-edge months. Pattern bit-identical to iter-v3/013/015 — same features, same windows.

### Check 6 — Pareto Dominance: PASS (vacuous, single-seed EXPLORATION)
Single seed=42 row: OOS Sharpe +0.171 / OOS MaxDD 40.62% / Calmar 0.179 / PBO 0.0889 / 112 trades / 100% concentration (single-seed-degenerate artifact when one symbol carries the entire portfolio's PnL after others go negative — TRX +18.82, BCH -2.35, LDO -9.19). EXPLORATION single-seed Pareto vacuous; per skill carve-out, PASS.

### Check 7 — Reproducibility: PASS
Engineering report stamps SHA `1aa3eb3` (setup commit), gate SHA `d5930fe` (PASS), brief SHA `10f3db9`. Critic Round 1 PRELIMINARY SHA `a20c54b`; QR Response SHA `06af055`. Runner uses explicit `feature_columns=V3_FEATURE_COLUMNS` (13 columns). Inner ensemble seed list literal: `_derive_ensemble_seeds(seed=42, size=1) = [42]`. CLI flag `--model xgboost` forwarded through `_build_v3_model`; strategy class actually used = `XgboostStrategy`. xgboost 2.1.4 in pyproject (`xgboost>=2.0,<3.0`); semver pin valid. All 4 first-commit pre-commits verified PASS by gate `d5930fe`.

### Check 8 — Hypothesis-Implementation Alignment: PASS (Clarification 1 resolved per QR Round 2)
Single-axis discipline honored. Diff vs iter-v3/013:
- `LightGbmStrategy` → `XgboostStrategy` (the one varied axis)
- `tbr_zscore_30` DROPPED (revert from iter-v3/015's 14 to 13) — pre-condition restoration
- `grow_policy='depthwise'`, `tree_method='hist'`, `n_jobs=1` PINNED
- `objective` swap; `min_child_samples → min_child_weight`; `num_leaves` Optuna param dropped (no-op)

Brief §1 hypothesis: IS Sharpe within ±0.30 of iter-v3/013 +1.0088 AND importance Spearman ρ < 0.85. REALIZED: IS Sharpe +0.5524 (Δ −0.46, OUTSIDE band by 0.15 below lower bound — PATH B fires per IS Sharpe < +0.81 threshold) AND Spearman ρ ≈ 0.56 (importance-divergence prediction CONFIRMED, but caveat-flagged per Clarification 2). Performance sub-hypothesis FALSIFIED; importance sub-hypothesis CONFIRMED-with-noise-caveat. §4.4 row 5 NEGATIVE-clean fires unambiguously per QR Clarification 1 disposition.

### Check 9 — Symbol Exclusion Enforcement: PASS
{BCH, LDO, TRX} ∩ V3_EXCLUDED_SYMBOLS = ∅. Runner enforces overlap check.

### Check 10 — Feature Isolation Enforcement: PASS
`grep -r "from crypto_trade.features " src/crypto_trade/features_v3/` returns 2 files but BOTH matches are inside DOCSTRINGS. No actual cross-track import.

### Check 11 — Forming-Candle: PASS (inherited from staleness guard)
Pre-flight staleness guard fired clean per run.log: "Pre-flight: branch OK, symbols OK, data fresh (<16h), feature-cols=13 PASS".

### Check 12 — Library Version Pinning: PASS
`pyproject.toml`: `xgboost>=2.0,<3.0` NEW dep (Apache-2.0); brief §9 declared exactly this pin. `lightgbm>=4.0` retained. xgboost 2.1.4 actually loaded.

## Recommendations to QR

1. **iter-v3/017 axis MANDATORY = NEW labeling architecture** (meta-labeling preferred per López de Prado AFML Ch. 3; fixed-horizon return labels as fallback). This is the unique untested category in the v3 axis priority hierarchy. Triple-barrier label has been fixed since iter-v3/001; only ATR multipliers tuned at iter-v3/010. Meta-labeling has slightly higher prior on PROMISING because it is structurally compoundable (the labeling change does not invalidate the existing 13-feature stack — it changes how the model uses them). Cannot be renegotiated post-hoc per new memory rule `feedback_v3_iter017_metalabeling_mandate.md`.

2. **iter-v3/016 catalog row captures 5 elements**: NEGATIVE clean verdict; worst OOS Δ in v3 history (-2.53); per-symbol collapse (BCH/LDO turned negative, only TRX carries with 258% portfolio concentration); MaxDD 4.26× inflation (40.62% OOS vs iter-v3/013 12.47%); importance-divergence-may-be-noise caveat per Clarification 2; scope-limited closure (n_trials=10 + cross-entropy + depth-wise defaults; not closed for all configurations) per Clarification 5.

3. **iter-v3/017 first commit must**:
   - Fix `_write_feature_importance` to aggregate across all walk-forward months (not last-month-only) per Critic Clarification 3 — Option A or Option B at Engineer discretion
   - Drop OOS importance CSV byte-duplication (or rename to `model_importance_last_month.csv`)
   - ITERATION_LABEL "v3-017"
   - Restore default `--model lgbm` (XGBoost remains opt-in via `--model xgboost`)
   - Implement meta-labeling architecture per López de Prado AFML Ch. 3

4. **After iter-v3/017 completes, cadence reaches 10/10 EXPLORATIONs since last CONFIRMATION → first CONFIRMATION can launch.** The PROMISING-class candidates accumulated to date for CONFIRMATION bundling are: iter-v3/007 (top-14 features minus vwap_dev_50 redundancy), iter-v3/010 (labeling ATR multipliers), iter-v3/011 (z-score OOD 2.0), iter-v3/013 (drop-MKR universe — strictly accretive baseline). NOT bundling candidates: iter-v3/009 (Falsifier 1 activated), iter-v3/012 (NULL-RESULT), iter-v3/014 (NEGATIVE clean), iter-v3/015 (NEGATIVE-no-effect), iter-v3/016 (NEGATIVE clean — this iteration). iter-v3/017's PROMISING/NEGATIVE outcome will determine whether the bundle includes a labeling-architecture component.

## Strong Prior on Classification

**EXPLORATION-NEGATIVE (clean)** per §4.4 row 5 — concur with QE recommendation and QR Round 2 acceptance. All 12 methodology checks PASS or INFORMATIONAL under EXPLORATION carve-out. Zero BLOCK conditions. The iteration tested its registered hypothesis cleanly, the model-architecture axis (at the tested configuration) is now CLOSED, and the catalog row records the worst OOS delta in v3 history (Δ -2.53). All 4 first-commit pre-commits verified PASS at QE setup; all 5 Round 1 clarifications dispositioned cleanly at QR Round 2; iter-v3/017 axis pre-committed via new memory rule.

iter-v3/017 axis = **NEW labeling architecture (Category 3)**; meta-labeling preferred for structural compoundability per López de Prado AFML Ch. 3.
