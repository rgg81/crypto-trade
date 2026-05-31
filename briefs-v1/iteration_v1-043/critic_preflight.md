# Phase 6.0 Critic Pre-Flight — iter-v1/043

OVERALL: PASS

## Pre-Flight Checks

### Check A — Look-Ahead Audit: PASS
Brief Section 4 falsifiers + EDA reference past-only data. Trend-scanning Wald-t labels at train time slope-scan the labeling window (not the test window); walk_forward.py:113 carries `train_end_ms = test_start_ms - embargo_ms` (verified via grep, unchanged). No new ML code paths in src/ — only `run_baseline_v1.py` dispatch elif + regime helper. No forward-window std, no fit_transform(combined), no future feature reads.

### Check B — Dispatch wiring: PASS
`run_baseline_v1.py:4924` elif `iteration_label == "v1-043" and set(symbols) == set(V1_ITER043_UNIVERSE)` precedes catch-all. Catch-all exclusion contains `"v1-043"` (line 5034). 5 pre-flight asserts present: label_mode, universe, optuna_objective, model lgbm, vol_ceiling_mode none (last one is /038 guard — defensive add, no harm). Banner emitted with model name + grid + cycle position.

### Check C — Wiring + Universe: PASS
`V1_ITER043_UNIVERSE = ("LINKUSDT",)` at `features_v1/__init__.py:268`, exported at 307. Single-cohort (Model_C_LINK_trend_scan_only) only, no DOT/BTC/LTC/ETH dispatch in /043 block per test 11.

### Check D — Configuration: PASS
Single-seed=42, ENSEMBLE_SIZE=3, n_trials=18, LINK-only — matches v1 EXPLORATION standard. Optuna objective default sharpe (Sortino-contamination assert defends). Label_mode trend_scanning grid (5,8,13,21) inherited from /035. R1 ON, R3 ON. Sacred constants untouched.

### Check E — Test suite: PASS
12 tests in `tests/test_iteration_v1_043.py` (10 mandated by brief §3.5 + regime schema test + foundation regression). Test 12 covers `build_regime_attribution_csv` schema directly: all 8 required columns + ≥5 rows + boolean in_sample + non-negative counts. Foundation regression test verifies walk_forward embargo line literal.

### Check F — Anti-Pattern Static Scan (A1–A14): PASS
A1 train_end_ms = test_start_ms - embargo_ms intact (line 113). A2 forward-window std: zero matches. A3 fit_transform(combined): zero matches. A6 (Optuna study contamination), A12 (DSR/PSR granularity), A13 (read-before-write): no new code paths. Regime helper writes via `.to_csv(out_path, ...)` after parent mkdir — proper write semantics.

### Check 14 — Axis Family Validation: PASS
Declared `per-cohort-specialization × labeling` REPEAT-COMBO. Counter = 3 each across cycle-5 history, well below 5+ saturation trigger. Prior-5 disperses across 5 distinct families (model-arch/labeling/feature-family/HYBRID/risk-primitive). REPEAT-COMBO load-bearing justification non-vacuous (/044 substrate-composition diagnostic, /018 precedent reframed honestly). src/ diff matches declared axis (universe restriction LINK-only, no new feature/label module).

### Mini-Check K — Strategy attribute symmetry: PASS
V1_ITER043_UNIVERSE referenced consistently: tuple definition, __all__ export, runner import, elif guard, set-equality assert, test imports. Single-source-of-truth maintained.

### Mini-Check L — Wall-clock plausibility: PASS
~18 min modal (12-25 min band) anchored on /036 ~25 min × 0.5 cohort coverage with sub-linear per-cohort Optuna scaling. 5-step derivation in §3.6 explicit. Well inside 2h cap.

### NEW-SKILL CHECK — regime_attribution.csv natively enforced: PASS
`build_regime_attribution_csv()` helper at `run_baseline_v1.py:1787-1892`. Schema: `regime_tag, in_sample, candidate_sharpe, candidate_max_dd, candidate_trade_count, baseline_sharpe, baseline_max_dd, baseline_trade_count` — EXACT match to skill §QE deliverable spec. Helper invoked unconditionally for `iteration_label == "v1-043"` at line 6076-6134 (BTC kline load fallback to "other" regime). Writes 6 regimes × IS/OOS = 12 rows. Brief Section 10 Regime Attribution Plan present (target regimes bull-2025-08, recovery-2025-11; mechanism; off-regime drag; bundle role REGIME-SPECIALIST-IS; regime-aware falsifier). Section 4 falsifier regime-aware (target-regime Sharpe Δ vs σ_R, NOT bundle OOS Sharpe alone). Section 11.6 reframed to per-regime Pareto.

### Foundation Regression: PASS
`walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` (verbatim grep hit). QE's /043 commits did not touch foundation files.

### Cadence + Axis Sanity: PASS
Phase 5.5 gate OVERALL=PASS. Section 0.6 declares axis family + VALID rotation status. Cycle-5 EXP 10/10 = CADENCE COMPLETE; /044 CONFIRMATION authorized post-closeout.

### Falsifier Presence: PASS
Section 4 F-AXIS #1 through #5 all bands and falsifier triggers explicit. Section 10 regime-aware falsifier explicit (target-regime Sharpe Δ vs σ_R band). 9-band canonical verdict matrix with per-band probability table.

---

**Acknowledgment**: /043 is the FIRST /043+ iteration where the new-skill `regime_attribution.csv` mandate is **NATIVELY ENFORCED** at QE Phase 6 (NOT post-hoc by the orchestrator as at /042's transition exception). The helper is wired unconditionally for `iteration_label == "v1-043"` and writes the schema-exact CSV inline during the backtest closeout. Brief Section 10 Regime Attribution Plan + Section 4 regime-aware falsifier + Section 11.6 per-regime Pareto criteria are all present in the refreshed brief (commit `0485ea1`). Phase 7.4 LM Master Item-0 Regime Attribution Table + Phase 7.5 Critic Check 3c (mandatory regime decomposition coherence) have a real artifact to read at closeout — the methodology debt from /042 transition is RETIRED.

---

## Approved Launch Invocation
