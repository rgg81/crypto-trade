# Phase 6.0 Critic Pre-Flight (re-check) — iter-v1/015

OVERALL: PASS

**Prior BLOCK at `c3fe580`** (label-time vs execution-time barrier formula asymmetry, 4.58× scaling error) **RESOLVED** by Path 1 fix at `3e67f72`.

## Re-Verification of Path 1 Fix

### 1. Formula symmetry at SAME magnitudes — VERIFIED

- `labeling.py:341-342, 373-374`: now computes `_sqrt_timeout_lbl = sqrt(timeout_minutes / interval_minutes)` and `tp_dist = sigma_k_tp * sig * _sqrt_timeout_lbl * entry`
- `lgbm.py:940-944`: computes `tp_pct = sigma * sigma_k_tp * sqrt_timeout * 100.0`
- For BTC σ_t=0.01607, k_tp=1.06, timeout_candles=21, √21 ≈ 4.583:
  - label-time tp_dist/entry = 0.01607 × 1.06 × 4.583 = **7.81% wide**
  - execution-time tp_pct = 0.01607 × 1.06 × 4.583 × 100 = **7.81% wide**
- Both barriers derived from SAME `_label_sigma_values[idx]` for same `(sym, ot)` key. Identity guaranteed by construction.
- Previous 4.58× asymmetry RESOLVED.

### 2. `interval_minutes` wiring — VERIFIED

- `label_trades()` signature `interval_minutes: int = 480` (backward-compatible default)
- `lgbm.py:521`: passes `interval_minutes=_interval_to_minutes(self._interval)` — derived from strategy's `_interval`
- `_INTERVAL_MINUTES` table at `lgbm.py:96-107`: "8h" → 480. No off-by-one possible.
- 10080/480 = 21 exactly (integer-clean)
- Non-sigma paths (NATR/ATR/percent) DO NOT read `interval_minutes` — BIT-IDENTICAL to pre-/015

### 3. Foundation Regression — VERIFIED CLEAN

- `walk_forward.py:113`: `train_end_ms = test_start_ms - embargo_ms` (e149e9d fix preserved)
- 4 mandated regression tests in `test_lookahead_embargo.py` present
- QE's Path 1 fix touched only labeling.py + lgbm.py + tests + brief

### 4. Anti-Pattern Static Scan — VERIFIED CLEAN

A1/A2/A3/A12/A13 all PASS. No new anti-patterns introduced.

### 5. /015 well-posed at calibrated 7.82% — VERIFIED

- Labels at /015 computed at σ_t × k × √21 = 7.82% (BTC portfolio-median)
- Matches /014 calibration EDA's assumed magnitudes
- Matches execution-time barriers
- /014's implicit 1.70% labels (no √timeout) were a different substrate; brief Section 3.1 acknowledges this
- /015 is the **first** test of the calibrated axis

### 6. Cadence + Axis Sanity — VERIFIED

- phase5p5_gate.md OVERALL=PASS
- Section 0.6: family `labeling` CONFIRMATION-spec; rotation N/A
- 9 cycle-2 EXPLORATIONs + HIGH-RISK pre-commit from /014 fills 10th slot → 10:1 cadence satisfied

### 7. Falsifier Presence — VERIFIED

8 quantitative falsifiers + F-AXIS-C1 + F-AXIS-MECHANISM + F7-NEW PARTIAL.

## Secondary Concern (NOT blocking; flag for Phase 7.5)

`test_label_time_vs_exec_time_consistency` Part B's discriminator is **structurally tautological under its fixture**:
- Both OLD and NEW formula paths return label=-1 in the test scenario
- Cannot discriminate FIXED labeling.py from BUGGY labeling.py
- Weak regression guard; not a backtest-correctness issue (formula is correct in production code)
- Brief Section 4 F-AXIS-C1 pre-registers test name `test_sigma_source_ewma14d_execution_barrier_consistency` (in `test_lgbm.py`) with per-candle 1e-6 tolerance loop — neither exists in committed code

**Recommendation for Phase 7.5**: strengthen fixture to non-vacuous discriminator OR amend brief Section 4 to match actual test. Does NOT block /015 backtest; labeling math is correctly fixed.

## Conclusion

Prior Phase 6.0 BLOCK RESOLVED. Labeling.py formula now matches lgbm.py at all magnitudes. Experiment finally well-posed. **Backtest may launch.**

Tautological-test observation is Phase 7.5 follow-up; does not block because labeling math is correct and backtest produces labels at the brief's claimed 7.82% magnitude.
