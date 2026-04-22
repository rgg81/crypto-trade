# Iteration 175 Engineering Report

**Role**: QE
**Config**: Code-only iteration — R2 drawdown-triggered position scaling
**Status**: COMPLETED (infrastructure only)

## What landed

Two commits on `iteration/175`:

1. `feat(iter-175): R2 drawdown-triggered position scaling in backtest engine` — `BacktestConfig` gained 4 fields; `run_backtest` tracks cumulative weighted PnL and running peak; trade-open applies a linear-interpolated scale when drawdown exceeds the trigger.

2. Test file extended with `TestR2DrawdownScaling` (2 tests) — both pass.

## Bug fix caught in passing

`create_order`'s non-VT path silently dropped the `vt_scale` argument (used only when VT was enabled). R2 passes its scale factor through `vt_scale` as the integration point, so the non-VT branch needed to apply it. Fix:

```python
# non-VT branch
weight_factor = (signal.weight / 100.0) * vt_scale
```

When no risk control fires (`vt_scale=1.0`), behaviour is unchanged. When R2 (or any future risk control) passes a sub-1.0 scale, it propagates correctly.

## Test suite

366 tests pass (was 364 before this iteration; 2 new R2 tests).

## Label Leakage Audit / Feature Reproducibility Check

N/A — infrastructure-only iteration, no model or data changes.

## Next steps

Iter 176: re-run the A+C(R1)+LTC(R1)+DOT(R1,R2) portfolio with R2 active. Calibrate trigger / anchor / floor on IS data first (QR Phase 1-5). Evaluate against v0.173 baseline.
