# Phase 5.5 Gate — iter-v3/077

**OVERALL: PASS**

Branch: `iteration-v3/077`
Gate date: 2026-05-15
Brief commit: `77d0b62` (backfill `e12cf99`)
EDA commit: `313d3c0` (lint fix `3b9f3ee`)
Setup commit: `30cda98`

---

## Per-Section Status

| Section | Status | Notes |
|---|---|---|
| Section 0 (Data Split) | PASS | OOS_CUTOFF_DATE=2025-03-24, training_months=24 unchanged. IS/OOS windows declared. Walk-forward lookahead-bug carry-over disclosed. |
| Section 0.5 (Iteration Type) | PASS | PASSIVE-DIAGNOSTIC, cycle 2 #7 of 10. Run mode `--exploration`, EXPLORATION_ENSEMBLE_SIZE=3, n_trials=35. Anchor=/060. 2h wall-clock target stated. |
| Section 1 (Hypothesis) | PASS | Diagnostic hypothesis, one paragraph. Bit-identical roster framing explicit. Intended classification is NULL-RESULT — acknowledged not a performance hypothesis. |
| Section 2 (IS-Only Evidence) | PASS | EDA at `313d3c0` (committed before brief). T0 anchor values byte-exact from `/060` comparison.csv. T1 regime-stratified attribution (IS: BEAR/CHOP Sharpe +1.29 vs BULL +0.41). T2 drag decomposition. T3/T4 conditional-orthogonality map (4/14 features conditionally regime-loaded). T6 escapability synthesis (directional-quality diagnosis, win/loss duration ratio 2.08). EDA self-audit AST scan for OOS-metric live identifiers returns PASS. |
| Section 3 (Proposed Changes) | PASS | Exactly two changes declared: (1) PRIMARY AXIS — `_write_conditional_orthogonality()` post-backtest report emission; (2) MANDATORY BASELINE-RESTORE — revert /076's `range_efficiency_50` (15→14 features). Single-axis discipline explicitly verified. No feature add, no labeling change, no risk-gate change. |
| Section 4 (Expected OOS Impact) | PASS | Predicted IS/OOS shifts = 0.000 (algebraic identity). Falsifier: any non-zero roster delta = Phase-6 wiring defect. Behavioral-effect predictor: 0 IS trades changed, 0 OOS trades changed (by design). Holding-time channels: both mechanical identities (0.000 candle delta). OOS/IS ratio pre-registered SUSPICIOUS gate: >3.0 (predicted ratio 0.1685 — mechanically impossible to trip). |
| Section 5 (Risk Mitigation) | PASS | No new strategy risk surface. Byte-identical gate stack at /060 config. Phase-6 wiring-defect risk addressed via Section 4.2 falsifier + pre-flight assertions. |
| Section 6 (Risk Management Design) | PASS | 7-primitive table present. All gates at /060 config — fire-rate prediction: identical to /060. Regime coverage: identical. |
| Section 7 (Failure-Mode Prediction) | PASS | Expected/intended: NULL-RESULT (~95%). SUSPICIOUS mechanically ruled out (~1%) via proof: bit-identical roster → OOS/IS ratio = algebraic copy of /060's 0.1685. Residual ~4%: benign non-determinism → INERT/NULL-RESULT, never SUSPICIOUS. Reporting-completeness risk (last-month-only CSV) explicitly named with EDA artifact as mitigation. |
| Section 8 (MERGE/NO-MERGE Criteria) | PASS | Disjunctive taxonomy with evaluation order LOCKED: SUSPICIOUS → NULL-RESULT → NEGATIVE → PROMISING → INERT. NULL-RESULT defined as bit-identical roster (IS=159, OOS=102 trades, every (symbol, open_time) matches). All thresholds numeric and pre-registered. EXPLORATION-level merge semantics stated (no BASELINE_V3.md update). |
| Section 9 (Library Stack) | PASS | Pinned versions declared (lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1). No new library added. SHAP explicitly excluded. |
| Section 10 (QR Audit Trail) | PASS | Axis selection provenance: EDA SHA `313d3c0` committed before brief. Per-parameter IS-only/a-priori disclosure table present (all 4 parameters: axis choice data-free, regime label price-only, flag ceiling a-priori constant, training window sacred constant). No OOS-metric live identifier in EDA (AST scan PASS). Setup commit SHA `30cda98` backfilled. Phase 5.5 gate SHA: to be backfilled. |

---

## Code-Readiness Verification

### Check 1 — Bit-identity claim (CRITICAL): PASS

`_write_conditional_orthogonality()` is located at `run_baseline_v3.py:2026–2154`. It is called at line 2828, **after** `_write_feature_importance` (line 2823) and **before** `_write_v3_comparison` (line 2830) — entirely in the post-backtest report-emission block. The function:

- Reads `V3_FEATURE_COLUMNS` (a module constant — no mutation).
- Iterates over `primary_model_pairs` reading `inner._models` (already-trained objects from the completed backtest).
- Reads the committed EDA artifact `analysis/iteration_v3-077/T3_conditional_orthogonality.csv` from disk.
- Writes `conditional_orthogonality.csv` to the report directory.

It does NOT touch: the model training loop, the feature set, the labeling, the risk gates (`RiskV2Config` unchanged), the Optuna search, or `ENSEMBLE_SEEDS`. The `model_pairs` list is built inside `_run_single_seed` (lines 2197–2256) and is fully populated after `run_backtest` returns — the instrumentation function is handed a completed object. **The bit-identity claim holds.**

### Check 2 — /076 revert: PASS

`V3_FEATURE_COLUMNS_TOP_N` in `src/crypto_trade/features_v3/__init__.py` contains exactly 14 entries (the BASELINE_V3 /059/060 anchor). `range_efficiency_50` is absent from the tuple (line 133–175 of `__init__.py`). The `compute_range_efficiency_50` dispatch remains in `add_engineered_v3_features` at `engineered_v3.py:926` as dead code — `range_efficiency_50` is computed and stored in the dataframe but is NOT in `V3_FEATURE_COLUMNS_TOP_N` so it is never passed as a feature column to LightGBM. This is acceptable per brief Section 3.2. The `efficiency_ratio_50` literal-name ban assertion is retained in `_verify_feature_columns` (line 346–354) and the new `range_efficiency_50`-absent assertion is also active (lines 388–395).

### Check 3 — Pre-flight assertions: PASS

`_verify_feature_columns` at `run_baseline_v3.py:217–535`:
- `ITERATION_LABEL = "v3-077"` (line 128): correct.
- Feature count assert: `n != 14` raises `RuntimeError` (lines 320–327): correct.
- `range_efficiency_50` ABSENT assert (lines 388–395): present and correct.
- `efficiency_ratio_50` ABSENT assert (lines 346–354): retained.
- `_verify_feature_columns` called at line 2388 before any backtest starts: confirmed.

### Check 4 — Test files: PASS

Five test files updated for 14-feature count:
- `tests/strategies/ml/test_v3_feature_count.py` — `test_feature_count_14()` asserts `n == 14`; `test_range_efficiency_50_absent()` asserts absence.
- `tests/features_v3/test_features_for_symbol.py` — updated to 14.
- `tests/features_v3/test_hurst_drift_50_200_universal.py` — updated.
- `tests/features_v3/test_fracdiff_d05_universal.py` — updated.
- `tests/features_v3/test_regime_momentum_signed_3d_universal.py` — updated.

### Check 5 — Tests and ruff: PASS

```
uv run pytest tests/features_v3/ tests/strategies/ml/ -q
345 passed, 3 skipped in 59.63s

uv run ruff check run_baseline_v3.py src/crypto_trade/features_v3/
All checks passed!
```

### Check 6 — Section 3.1 implementation-note finding (RESOLVED — not a BLOCK)

The runner's `model_pairs` object carries **last-month-only** models. In `LightGbmStrategy` (`lgbm.py:472–503`), `_train_for_month` clears `self._models = []` and rebuilds it at each walk-forward month boundary — so at report time `inner._models` contains only the ensemble from the final IS walk-forward month, not the full per-month history.

Consequence for the shipped `conditional_orthogonality.csv`:
- **PART A** (runner-emitted last-month gain-importance share): contains one importance vector per symbol from the final IS month's models only. This is a **degenerate** per-month map — it represents a single time point, not the full IS-month trajectory.
- **PART B** (EDA artifact `T3_conditional_orthogonality.csv` at SHA `313d3c0`): the full per-IS-month conditional-orthogonality correlations are copied verbatim from the committed EDA file into the runner-emitted CSV via `eda_corr_portfolio_pooled` / `eda_max_abs_corr` / `eda_conditionally_regime_loaded` columns. This is the complete diagnostic deliverable.

The shipped `conditional_orthogonality.csv` is therefore a **hybrid**: PART A (runner) = last-month snapshot; PART B (EDA) = full per-month map from `T3_conditional_orthogonality.csv`. The full diagnostic deliverable (the per-month correlation map the brief nominates as the primary output) lives in PART B. This matches the brief's Section 3.1 implementation note pre-disclosure and is NOT a BLOCK. The engineering report must state this explicitly.

---

## Summary

All 10 mandatory brief sections present and substantive. All 6 code-readiness checks PASS. Tests: 345 passed, 3 skipped. Ruff: clean. Bit-identity claim verified — `_write_conditional_orthogonality` is pure post-backtest report emission with no strategy-path interaction. The Section 3.1 implementation-note finding is resolved: the shipped CSV is a hybrid (PART A = last-month snapshot; PART B = full EDA per-month map from `T3_conditional_orthogonality.csv`). **Proceed to Phase 6.**

Gate SHA: `caed50d`
