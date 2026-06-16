# Engineering Report — iter-v1/012 (BTCUSDT) — trend-scale de-lever sizing primitive

> Wiring authored by the Quant Engineer agent; the agent died on a transient server rate-limit
> before committing / smoke-verifying. Completed (review + byte-identical proof + smoke + commit +
> launch) in the autonomous loop. RE spec: `risk_report.md` (commit `fea33bfd`).

## What was wired (NEW code; `trend_scale_enabled` default False → byte-identical everywhere else)
- **`backtest_models.py`:** 6 new `BacktestConfig` fields — `trend_scale_enabled=False`,
  `trend_scale_floor=0.25`, `trend_scale_z_lo=-0.5`, `trend_scale_z_hi=0.0`,
  `trend_scale_slope_lb=20`, `trend_scale_std_lb=250` — plus IS/OOS fire-counter doc.
- **`backtest.py`:** helpers `trend_scale_from_z` (piecewise-linear z→[floor,1.0]) +
  `build_trend_z_lookup` (past-only 200-SMA-slope z-score from `close`, `.shift(1)` everywhere).
  Init-time `trend_z_lookup` built ONLY when enabled (line 314). LONG-only composing step
  (`config.trend_scale_enabled and signal.direction > 0`, line 698) multiplies `vt_scale *= trend_scale`
  AFTER R5/vol_ceiling — composes, never replaces. NaN→1.0 (fail-open). `[TREND-SCALE/012]` IS/OOS
  fire counter + avg-multiplier → comparison.csv.
- **`run_baseline_v1.py`:** `run_model` gains the 6 params (default no-op); `_spec_*` override vars
  threaded through the universal single-symbol dispatch (defaults preserve /002–/011 byte-identical);
  `elif iteration_label == "v1-012"` branch = iter-010 config (19-col, fixed_horizon N=9, atr_tp=100
  let-winners-run) PLUS `trend_scale_enabled=True` + the RE's calibrated params. Single-axis vs /010.
- **`live/models.py`:** `LiveConfig` parity fields (default False/no-op) for a future live deployment;
  deployed runtime path unchanged.

## Byte-identical proof (the load-bearing safety property)
- Both the init lookup and the composing step are guarded by `if config.trend_scale_enabled` →
  with the default `False`, the code path is unchanged for v2/v3 and every prior v1 iteration.
- `uv run pytest tests/test_backtest.py tests/test_lookahead_embargo.py -q` → **93 passed**. The
  backtest engine + lookahead/embargo invariants hold with the wiring present.

## Smoke-verify (firing) — see commit-time evidence below
iter-012 = iter-010 + trend_scale. Expected: banner shows trend_scale enabled; `[TREND-SCALE/012]`
counter shows trend_scale<1.0 firing in down-trends + avg LONG multiplier <1.0; trade count ≈ iter-010
(floor 0.25 never gates).

## Full K=5 screen command
`PYTHONUNBUFFERED=1 uv run python run_baseline_v1.py --exploration --iteration 12 --symbols BTCUSDT --n-trials 35 --slippage-bps 2`
