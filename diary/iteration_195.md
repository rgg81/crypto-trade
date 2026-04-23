# Iteration 195 — Frac-diff features (rejected by pre-test)

**Date**: 2026-04-23
**Type**: EXPLORATION (AFML Ch. 5)
**Baseline**: v0.186 — unchanged
**Decision**: NO-MERGE (pre-test negative)

## TL;DR

Implemented fractional differentiation (fixed-width, AFML Ch. 5).
Stationarity achieved at d ∈ [0.1, 0.2] for all five symbols —
remarkably mild, preserves memory well. But LINK IS CV proxy Sharpe
improved only +0.003 over baseline (within noise). **Skipped the
full walk-forward backtest** based on the pre-test signal.

## Process change: IS-only pre-test as go/no-go

Four consecutive failed exploration iterations (xbtc augment 189,
xbtc swap 190, prune 191, 14d timeout 192) cost ~9 hours of compute
each, for zero merges. From this iter forward, exploration iterations
should gate on an IS-only CV proxy test before committing to full
backtests.

The process:
1. Implement feature / change in isolation.
2. Train LightGBM on full IS data with 5-fold TimeSeriesSplit CV.
3. Compute a proxy Sharpe (conf-weighted directional accuracy).
4. Only run the full backtest if proxy improvement ≥ +0.01.

This iteration validates the process by catching a negative signal
that would have required 1.5h to confirm.

## Numbers from the pre-test (LINK IS)

| config | features | proxy Sharpe |
|--------|---------:|-------------:|
| Baseline 193 | 193 | +0.056 |
| +2 frac-diff (augment to 195) | 195 | +0.058 |
| swap 2 low-MDI for 2 frac-diff | 193 | +0.048 |

Frac-diff MDI ranks: d=0.1 → 56/195, d=0.2 → 96/195. Some signal, not
much. The augment case has lower CV std (stabilizing effect) but
the mean barely moves.

## AFML stationarity-memory tradeoff

All five symbols' raw 8h close is non-stationary (ADF p > 0.05).
All achieve stationarity at d ∈ [0.1, 0.2] — a small enough d that
considerable memory is preserved. This is a *good* property: the
frac-diff series looks much more like price than like returns.

The fact that frac-diff still doesn't improve CV Sharpe means: the
existing baseline features (RSI, BB %B, stoch, z-scores) already
capture the stationary-but-with-memory information content. Frac-diff
is theoretically elegant but empirically redundant in this feature set.

## What went right

- Implemented frac-diff correctly (ADF stationarity matches theory)
- Used IS-only pre-test to avoid burning 1.5h on a negative result
- Documented remaining frac-diff variants not tested (volume, higher d,
  cross-asset frac-diff)

## Exploration/Exploitation Tracker

Window (185-195): [X, X, X, E, E, E, E, V, X, E] → **5E/4X** + 1V.
Near 55/45 balance — healthy given the recent E streak.

## Next Iteration Ideas

- **Iter 196**: Apply frac-diff pre-test process to Model A (BTC+ETH,
  2x training samples). If pre-test delta ≥ +0.01, run full backtest.
- **Iter 197**: Stop offline feature exploration. Six failed attempts
  confirm v0.186 is near local optimum on feature engineering.
  Commit to paper-trading v0.186 as iter 197's deliverable.
- **Iter 198+**: Post-paper-trading iteration ideas driven by live data.
