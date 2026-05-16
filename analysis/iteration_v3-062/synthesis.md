# iter-v3/062 EDA — DSR_relative Recalibration Synthesis

**Generated**: 2026-05-13T22:43:53.118273
**Iterations analyzed**: 028, 050, 058, 059, 060, 061
**Path selection**: **Path C (passive retrospective + defer to /069 CONFIRMATION)**

## Key findings

### Finding 1 — Input granularity mismatch confirmed (4 iterations of evidence)

The runner's `psr()` call at `run_baseline_v3.py:2296-2302` passes:
- `observed_sharpe = raw_sharpe_oos = mean(oos_wp)/std(oos_wp)×√n_trades` — TRADE-LEVEL × √n_trades
- `benchmark_sharpe = cpcv_path_sharpe_q75 = percentile(flat_path_sharpes, 75)` — CANDLE-LEVEL × √n_test_per_path
- `n_obs = len(oos_wp) = n_trades`

Trade-level Sharpe and candle-level Sharpe have DIFFERENT square-root scalings:
- /061 trade-level: 0.2070 (× √102 ≈ √102 = 10.1)
- /061 candle-level Q75: 0.8378 (× √n_test ≈ √1296 ≈ 36)

The scale ratio means the trade-level observed Sharpe is structurally smaller than the candle-level benchmark, even when the strategy has positive trade-level edge.

### Finding 2 — Path A (threshold recalibration) only partial fix

At /060/061 EXPLORATION mode: observed dsr_relative = 0.0 (BELOW any reasonable threshold).
At /059 CONFIRMATION mode (n_trials=1050): observed dsr_relative = 0.1134 (BELOW 0.55 threshold).
At /058 CONFIRMATION mode (n_trials=1050): observed dsr_relative = 0.9982 (PASS at any threshold; this is the historical "anchor" calibration).

The /058 → /059 drop (-0.885) under unified architecture is the canonical "calibrated for wrong architecture" finding. Path A at threshold 0.55 still FAILs at /059 (0.1134 < 0.55) — so threshold-only recalibration is insufficient.

### Finding 3 — Path B (granularity match) addresses root cause but breaks backward-compat

Paths B1/B2/B3/B4 all produce DIFFERENT dsr_relative values from current output. Historical /028/050/058/059 dsr_relative numbers all change. This is acceptable IF the new methodology is correct, but requires:
- Smoke test on small dataset
- 6th integration test in test suite
- Brief Section 8 traceback subsection per `feedback_v3_methodology_post_hoc_input_traceback.md`
- Backward-compat verification or explicit retirement of historical numbers

Per `feedback_v3_methodology_axis_integration_test.md`, this surface MUST be defended.

### Finding 4 — EXPLORATION mode DSR_relative is informational ONLY

Per `feedback_v3_dsr_mode_artifact.md`: EXPLORATION-mode DSR/PSR values at --exploration --seeds 3 with n_trials=315 are STRUCTURAL ARTIFACTS of the small Optuna search space. The López de Prado E[max_SR] formula:
- /060/061 EXPLORATION: E[max_SR] = √(2 ln 315) ≈ 2.41
- /059 CONFIRMATION: E[max_SR] = √(2 ln 1050) ≈ 2.64

The DSR_relative gate is a CONFIRMATION-mode concept. iter-v3/062 EXPLORATION cannot meaningfully test the recalibration because the CONFIRMATION n_trials scale isn't reached.

### Finding 5 — Path B4 (annualized both sides) is the recommended cycle 1 CONFIRMATION methodology

For iter-v3/069 cycle 1 CONFIRMATION, the QR should:
1. Use daily-Sharpe-annualized (×√252) for both observed and benchmark
2. Compute daily skew/kurt on daily PnL series (not trade-level)
3. Use n_obs = n_daily_observations (~252 × T_years)
4. Add smoke test verifying dsr_relative > 0 on small synthetic dataset
5. Add 6th integration test in `tests/strategies/ml/test_dsr_relative_recalibration.py`
6. Re-compute /058 + /059 dsr_relative under new methodology for historical comparison

## Path C deliverable (iter-v3/062)

- This EDA + 6 numerical tables (T1-T7) as `analysis/iteration_v3-062/*.csv`
- Diary entry documenting Path C selection + cycle 1 CONFIRMATION recommendation
- Memory rule capturing the input-granularity finding for /069 QR

## /060 anchor predictions for /062 backtest (if Path A or B chosen instead)

**NOTE: iter-v3/062 will NOT run a backtest under Path C.**
If Path A/B were chosen, predicted /062 metrics (data-invariant axis):
- IS monthly Sharpe: +0.8236 (identical to /061 = /060)
- OOS monthly Sharpe: +0.1551 (identical to /061 = /060)
- IS Trades: 159
- OOS Trades: 102
- frac_positive_paths: 0.6444 (architecture-invariant)
- PBO: 0.1278 (cell-level invariant)
- cpcv_path_sharpe_q75: 0.8378
- dsr_relative under new methodology: depends on path chosen (see T4/T5)

## Reproducibility

Run command: `uv run python analysis/iteration_v3-062/dsr_relative_recalibration_eda.py`
Generates: t1-t7 CSVs + this summary
Dependencies: pandas, numpy, scipy (already in environment)
