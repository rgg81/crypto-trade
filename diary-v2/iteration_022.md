# Iteration v2/022 Diary

**Date**: 2026-04-15
**Type**: EXPLORATION (LTCUSDT as NEAR replacement)
**Parent baseline**: iter-v2/019
**Decision**: **NO-MERGE** — LTC worse than NEAR on IS and OOS

## Results vs iter-v2/019

| Metric | iter-v2/019 (NEAR) | iter-v2/022 (LTC) | Δ |
|---|---|---|---|
| IS monthly Sharpe | +0.50 | +0.47 | −0.03 |
| OOS monthly Sharpe | +2.34 | **+1.43** | **−0.91** |
| OOS trade Sharpe | +2.45 | +1.81 | −0.64 |
| OOS MaxDD | **24.39%** | **46.12%** | **+21.7 pp** |
| IS total PnL | +116.72 | +102.46 | −14.26 |
| OOS total PnL | +125.82 | +95.94 | −29.88 |

NO-MERGE on every metric.

## Per-symbol breakdown — LTC is worse than NEAR on IS

| Symbol | iter-019 IS wpnl | iter-022 IS wpnl |
|---|---|---|
| XRPUSDT | +83.62 | +83.62 (same) |
| SOLUSDT | +31.17 | +31.17 (same) |
| DOGEUSDT | +22.43 | +22.43 (same) |
| **NEARUSDT** | **−20.50** | — |
| **LTCUSDT** | — | **−34.77** ← **worse than NEAR** |

LTC IS contribution is **−34.77** vs NEAR's −20.50. LTC takes MORE
trades (103 vs NEAR's 72) but its directional bets are equally wrong,
just at higher volume. **LTC is a worse 4th symbol than NEAR**.

## Root cause 1: LTC's 2022 wasn't that much better

I expected LTC to be "less damaged" by 2022 (drawdown −60% vs NEAR's
−92%). But the per-trade loss distribution doesn't match the
drawdown headline:
- LTC 2022 had MULTIPLE pullbacks, each losing trades
- NEAR had ONE massive crash, then tried to recover
- Total IS damage: LTC −34.77 > NEAR −20.50

The model's 2022 IS losses aren't proportional to the coin's total
drawdown — they're proportional to the number of failed signals
during the period. LTC generated more signals and failed more times.

## Root cause 2: LTC dilutes the hit-rate gate's window

iter-019's hit-rate gate tracks SL rate across the last 20 closed
trades (cross-symbol, global). When LTC's trades enter the window,
LTC had more TP hits than expected (5 TP, 12 SL, 4 timeout = 42%
SL rate, below baseline 50%). LTC's trades DILUTE the rolling SL
rate, making the gate fire LESS often:

| Metric | iter-019 | iter-022 |
|---|---|---|
| Hit-rate gate kills | 21 | **13** (−38%) |
| BTC filter kills | 39 | 38 |
| Total trades | 461 | 492 |

With the gate firing less, the July-August 2025 drawdown that
iter-017 caught via the gate now gets through partially. **OOS
MaxDD blows up to 46.12% because the defensive gate is weakened**.

## Lesson

**Adding a new symbol can weaken existing gates**. Per-symbol gates
would avoid this interaction but per-symbol brakes failed for
concentration reasons in iter-014.

The right 4th symbol needs:
- Positive IS Sharpe (doesn't hurt IS)
- Trades that don't dilute the hit-rate gate's signal
- Uncorrelated direction to existing 3 symbols

Candidates for iter-023:
- **TRX** (Tron) — stable network, modest 2022 crash
- **ADA** (Cardano) — large cap L1
- **BCH** (Bitcoin Cash) — old stable PoW
- **TON** (Open Network) — 2024 mover, less 2022 exposure

## MERGE / NO-MERGE

**NO-MERGE**. Next: iter-v2/023 with TRXUSDT as the 4th symbol.
