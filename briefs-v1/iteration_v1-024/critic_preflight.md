# Phase 6.0 Critic Pre-Flight — iter-v1/024

OVERALL: BLOCK-PENDING-FIX — RegimeRoutedStrategy wrapper constructed but NEVER invoked at inference. 6 sub-models run independent backtests; regime gate never applied. Single-loop fix in `run_baseline_v1.py`.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
Past-only z30 lookup via parquet column already `.shift(1)`-derived in /023. `evaluate_regime_at_signal` reads pre-shifted cache; no in-tick computation.

### Check 13 — Anti-Pattern: PASS (A1-A13 clean); NEW candidate A14 surfaces
Anti-pattern: "Strategy wrapper constructed at dispatch site but never invoked at inference; sub-strategies run independently and their trade rosters concatenated."

### Check 8 — Hypothesis-Implementation Alignment: **FAIL** (BLOCK driver)
Brief Section 3.1 + 3.2 + 3.4 + 10.4 MANDATE: `RegimeRoutedStrategy` wraps at signal-time, computing z30 at bar t and dispatching to ONE matched sub-strategy.

Actual implementation: `_iter024_regime_wrappers` stores wrappers for stats-only purposes; each sub-model (Model_A_extreme, Model_A_normal, Model_C_extreme, Model_C_normal, Model_D_extreme, Model_D_normal) runs an independent `run_backtest()` call → 6 independent rosters concatenated. The wrapper's `get_signal()` is never reached during the backtest loop.

**Downstream consequences**:
- Trade count will trend toward 2× baseline (~1242) — over-trading defect
- F-AXIS #2 falsifier band [400, 850] structurally pre-fired
- F-AXIS #3 fire-rate stats empty (wrapper never called)
- Brief's regime-conditional hypothesis NEVER ACTUALLY TESTED

### Foundation Regression: PASS
`walk_forward.py:113` unchanged. `lgbm.py:data_filter_callback` is additive (backward-compat verified by `test_lgbm_strategy_no_filter_backward_compat`).

### Cadence + Axis Sanity: PASS
phase5p5_gate.md OVERALL=PASS. Family `model-arch` NEW 16th. Rotation VALID.

### Falsifier Presence: PASS
5 F-AXIS rows including #5 gain-share recurrence LOAD-BEARING.

## BLOCK-PENDING-FIX Rerun Protocol

**Specific defect**: `run_baseline_v1.py:1542-1774` constructs `RegimeRoutedStrategy` instances but never passes them to `run_backtest()`. Instead, 6 independent sub-models backtest in isolation.

**Required fix** (single-loop refactor): 
For each of Pool A, LINK, LTC:
1. Instantiate `_strat_X_ext` + `_strat_X_norm` with `data_filter_callback` (but DO NOT call run_backtest yet)
2. Wrap them in `RegimeRoutedStrategy(extreme=_strat_X_ext, normal=_strat_X_norm, ...)`
3. Call `run_backtest(config, _strat_X_regime, ...)` ONCE per cohort using the wrapper
4. Wrapper's `get_signal()` dispatches to matched sub-strategy per bar

DOT path unchanged (single-model dispatch preserved).

**Also missing**: integration test at `tests/test_run_baseline_v1_iter024.py` verifying V1_ITER024 dispatch routes via wrapper. The 19 unit tests cover the wrapper in isolation but not the runner-side wiring.

**Re-eval scope**: After fix + test add, Critic single-pass re-evaluation focused on Check 8 (wrapper now invoked at inference). All other PASS verdicts carry forward.

**Final verdict post-fix**: PASS → backtest cleared. BLOCK-FINAL only if fix introduces new defect.

## Path Forward (advisory if fix path exhausted)

3 alternative axes from non-recent families:
1. **Per-cohort vol-target ceiling** — risk-primitive — single-model architecture answer to same regime-edge hypothesis; cap per-cohort gross exposure.
2. **Regime-conditional triple-barrier σ_t** — labeling — ONE pool model with regime-adjusted barriers (×1.4 in EXTREME).
3. **Drop DOT from baseline universe** — universe — 4-symbol portfolio (BTC+ETH pool + LINK + LTC); tests DOT-as-drag hypothesis.

These are advisory — the wrapper-wiring fix is simpler.
