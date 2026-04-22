# Iteration 175 Research Brief

**Date**: 2026-04-22
**Role**: QR
**Type**: **EXPLOITATION** (infrastructure — implement R2 in the engine)
**Previous iteration**: 174 (NO-MERGE — DOT(R1) addition fails diversification exception due to MaxDD regression)
**Baseline**: v0.173 (A+C(R1)+LTC(R1), OOS +1.39, IS +1.30)

## Section 0 — Data Split (verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

## Motivation

Iter 174's DOT addition was blocked by the correlated-drawdown problem: DOT's 2022 IS losses amplified Model A's concurrent drawdown, causing pooled OOS MaxDD to regress slightly from 27.74% to 28.19% and blocking the diversification exception. R1 is per-symbol and can't address this.

R2 (drawdown-triggered position scaling) is the skill's designated mitigation for correlated drawdowns. When the cumulative weighted PnL of a backtest falls below its running peak by more than `risk_drawdown_trigger_pct`, new trades are scaled down linearly toward `risk_drawdown_scale_floor`.

This iteration implements R2 in `BacktestConfig` / `run_backtest` + unit tests. It does NOT rerun the portfolio — that's iter 176. Infrastructure iter only.

## Research Analysis

No new IS-data research this iteration — R2 design is directly specified by the skill, and iter 174's analysis already motivated its necessity. Calibration of R2 parameters against IS data deferred to iter 176 when the mechanism is evaluated end-to-end on real trades.

## Code changes

`BacktestConfig`:

```python
risk_drawdown_scale_enabled: bool = False
risk_drawdown_trigger_pct: float = 10.0
risk_drawdown_scale_floor: float = 0.33
risk_drawdown_scale_anchor_pct: float = 30.0
```

`run_backtest`: track `cum_weighted_pnl` and `peak_weighted_pnl` across closed trades. On each trade-open, compute drawdown = `peak − cum`. If drawdown > `trigger`, linear-interpolate a scale between 1.0 (at trigger) and `scale_floor` (at `anchor_pct`), multiply into `vt_scale` before `create_order`.

Bug fix to `create_order`: in the non-VT path, `weight_factor = (signal.weight / 100.0) * vt_scale` so R2 scaling propagates through when VT is disabled. Previously R2 was silently dropped in the non-VT path.

Unit tests (2 new, all pass):

- `test_r2_scales_new_trades_during_drawdown` — verifies weight_factor < 1.0 after cumulative PnL passes trigger.
- `test_r2_disabled_by_default` — verifies default-off behaviour preserves v0.173.

Full test suite: 366 passed.

## Decision

This iteration is NO-MERGE (infrastructure only, no portfolio metrics change). Iter 176 will evaluate R2 on the actual portfolio and decide merge.

## Exploration/Exploitation Tracker

Window (166-175): [E, E, E, E, X, E, E, X, E, X] → 7E/3X. Balanced.
