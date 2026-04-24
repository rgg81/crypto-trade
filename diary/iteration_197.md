# Iteration 197 — Live engine brought to v0.186 parity (MERGE)

**Date**: 2026-04-23
**Type**: Engineering / infrastructure
**Baseline**: v0.186 — unchanged; live engine now reproduces it exactly
**Decision**: MERGE

## TL;DR

The live engine had silently been stuck at **v152**. Five iterations of
merged improvements (iter 165 LTC-for-BNB, 172-176 DOT + R1 + R2, 173
R1 on altcoins, 186 R3 OOD) had never been reflected in the live code,
which meant a paper-trading run would have diverged from v0.186
immediately and catastrophically.

This iter ports all four changes into `src/crypto_trade/live/`, adds 8
unit tests, and runs a full end-to-end parity check against v0.186's
April 2026 trades:

- **14 live trades match 14 backtest trades** on symbol, open_time,
  direction, exit_reason, close_time, AND weight_factor (at CSV's own
  4-decimal precision).

## What was missing in live

| gap | source iter | fix location |
|------|-------------|--------------|
| Model D was BNB (should be LTC) | 165 | `BASELINE_MODELS` in `live/models.py` |
| Model E (DOT) not present | 176 | `BASELINE_MODELS` |
| R1 consecutive-SL cooldown | 173 | per-model fields in `ModelConfig` + engine state |
| R2 drawdown-triggered scaling | 176 | per-model fields + engine state |
| R3 OOD Mahalanobis gate | 186 | per-model fields + `ModelRunner.__init__` forwarding |
| OOD feature list duplicated in runner | 186 | `OOD_FEATURE_COLUMNS` as shared constant |

## How the live engine matches backtest

Backtest uses a single pass through the full history, accumulating per-symbol
SL streak and per-model cumulative PnL along the way. Live uses the same
per-trade math but reconstructs initial state from the SQLite trade store
on startup via `_rebuild_risk_state()` (new). During catch-up and tick,
closes flow through `_record_trade_close_for_risk()` which updates the same
state dicts. At signal-open, both paths check `_risk_cooldown_until` and
multiply `vt_scale` by `_r2_scale_for(model)`.

The parity script validated this end-to-end: after seeding the DB with 768
pre-March v0.186 trades and calling `_rebuild_*`, the live engine's R2
accumulator for Model E came to 43.72 — exactly the backtest's value at
the same point in time. 30 R1 cooldowns were armed for symbols with
recent 3-SL streaks. When catch-up then ran through March + April, it
produced the same 14 April trades as the backtest.

## Code summary

- **+559 lines / −28 lines** across 4 code files
- **8 new unit tests**, all passing
- **79/79 live tests pass**, including the v152 parity test (no regression)
- **17-minute end-to-end parity run** produces 14 live / 14 backtest,
  all matching within the CSV's own precision

## Decision

MERGE. No baseline change — v0.186 stands — but the live engine is now a
faithful reproduction of it, unblocking paper-trading.

## Exploration/Exploitation Tracker

Window (187-197): [X, E, E, E, X, V, X, E, V, E, Eng]. This iter is
engineering infrastructure, distinct from exploration/exploitation
of the strategy.

## Next Iteration Ideas

- **Iter 198**: Paper-trade v0.186 against Binance Futures testnet for
  2 weeks. Iter 196's recommendation, now unblocked.
- **Iter 199**: If paper-trading shows any divergence from backtest,
  deep-dive it. Otherwise, resume offline iteration informed by live data.
- **Iter 200**: Consider tightening `iteration_report.py:121`
  `weight_factor` format from `:.4f` to `:.6f` if downstream tooling
  benefits. Not urgent.
