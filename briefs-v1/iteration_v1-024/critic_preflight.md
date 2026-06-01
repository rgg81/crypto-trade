# Phase 6.0 Critic Pre-Flight — iter-v1/024 — POST-FIX RE-EVALUATION

OVERALL: PASS — backtest cleared to launch.

## Prior Verdict
BLOCK-PENDING-FIX — RegimeRoutedStrategy wrapper bypassed at inference.

## Fix Applied (commit 8664bbe)
- NEW factory functions in `run_baseline_v1.py`: `build_lgbm_strategy()`, `build_backtest_config()`, `run_regime_cohort()`
- /024 dispatch rewritten: Pool A, LINK, LTC each route via `run_regime_cohort` (calls run_backtest ONCE on wrapper)
- DOT path unchanged (single-model dispatch via run_model)
- `RegimeRoutedStrategy.compute_features()` propagates to both inner strategies
- 13 NEW integration tests verifying: wrapper IS invoked, inner strategies NEVER independent run_backtest, routing semantics correct, compute_features propagated
- 32/32 tests pass

## Re-Evaluation

### Defect Axis: PASS
`grep run_backtest(` returns only TWO call sites: `run_model` line 432 (DOT + non-/024) and `run_regime_cohort` line 626 (wrapper). The pre-fix 6-independent-backtest pattern is GONE. No dead code.

### Foundation Regression: PASS
`walk_forward.py:113` unchanged. `labeling.py` untouched. `lgbm.py` additions minimal and additive (data_filter_callback ctor param + instance store + filter applied AFTER train window slicing, BEFORE labeling — past-only invariant preserved).

### Anti-Pattern Static Scan on Fix Diff: PASS
A1-A13 all clean. data_filter_callback reads `_master.iloc[train_indices]` already bounded by embargo. funding_rate_zscore_30 pre-shifted at /023 feature time.

### Past-Only Invariance: PASS
`RegimeRoutedStrategy.get_signal()` reads z30 from `_month_features` cache populated at month-boundary training. Pre-shifted parquet column. No real-time z30 computation.

### Check 8 Re-Check: PASS
Brief Section 1 H_AXIS hypothesis now actually realizable:
- Training partition via data_filter_callback at lgbm.py:524-526
- Inference routing via RegimeRoutedStrategy.get_signal() at regime_gate_v1.py:294
- DOT excluded per LM Master §1 mitigation

## Non-Blocking Risks (record-only)

1. Both inner sub-models train every month regardless of routing → doubles per-cohort training cost. Estimate 55-78 min plausible but tight against 2h cycle-3 cap.
2. Extreme partition thin (Pool A 1573, LINK 709, LTC 802 bars). Skip-month fallback to normal should be surfaced in engineering report.

## Verdict
PASS. Phase 6 backtest cleared to launch.
