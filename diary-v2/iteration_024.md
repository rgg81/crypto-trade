# Iteration v2/024 Diary

**Date**: 2026-04-15
**Type**: EXPLORATION (5-symbol portfolio, add TRX alongside NEAR)
**Parent baseline**: iter-v2/019
**Decision**: **NO-MERGE** — primary metrics strong but 10-seed OOS monthly just below 1.0

## Results

**Primary seed 42** (best primary result of iters 021-024):
| Metric | iter-v2/019 | iter-v2/024 |
|---|---|---|
| Total trades | 461 | **601** (+30%) |
| IS monthly Sharpe | +0.50 | +0.56 |
| OOS monthly Sharpe | +2.34 | **+2.60** (+11%) |
| IS trade Sharpe | +0.57 | +0.66 (+15%) |
| OOS trade Sharpe | +2.45 | +2.68 (+9%) |
| OOS MaxDD | 24.39% | **21.39%** (−12%, best yet) |
| Max concentration | 41.39% | **37.00%** (best yet) |

**10-seed mean**:
| Metric | Value |
|---|---|
| Mean IS monthly Sharpe | **+0.6429** |
| Mean OOS monthly Sharpe | **+0.9723** (just below 1.0) |
| Mean OOS trade Sharpe | +1.2184 |
| Profitable seeds | **9/10** (seed 456 negative at −0.22) |
| Balance ratio | **1.51x** |

## Per-symbol (primary seed)

**IS**:
| Symbol | Trades | PnL | Note |
|---|---|---|---|
| XRPUSDT | 103 | +83.62 | dominant positive |
| SOLUSDT | 85 | +31.17 | |
| TRXUSDT | 103 | **+27.54** | **strong positive contributor** |
| DOGEUSDT | 84 | +22.43 | |
| NEARUSDT | 72 | **−20.50** | drag remains |
| **Total** | **447** | **+144.26** (vs iter-019 +116.72) |

**OOS**:
| Symbol | Trades | PnL | Share |
|---|---|---|---|
| XRPUSDT | 27 | +52.08 | 37.0% |
| DOGEUSDT | 31 | +49.70 | 35.3% |
| SOLUSDT | 37 | +37.50 | 26.6% |
| NEARUSDT | 22 | **+13.88** | 9.9% (flipped positive!) |
| TRXUSDT | 37 | −12.42 | −8.8% |
| **Total** | **154** | **+140.75** | max 37% |

Interesting: NEAR's OOS went from −2.20 (iter-019) to **+13.88** in iter-024.
The 5-symbol composition changes the hit-rate gate's rolling SL window
composition, so NEAR's OOS trades that were killed in iter-019 now pass
through. TRX pays the price, dropping to −12.42 OOS.

## Why NO-MERGE

Two failed conditions vs user's criteria:
1. 10-seed mean OOS monthly +0.9723 **below** 1.0 target
2. 1 seed (456) negative → 9/10 profitable (still passes but weak)

Primary seed looks great but the mean reveals seed variance:
- Best seed: 42 (IS +0.56 / OOS +2.60) — the reference
- Worst seed: 456 (IS +0.50 / OOS −0.22) — a real tail risk

## Lesson — trade count isn't the full answer

iter-023 (4 symbols, TRX replacing NEAR): 507 trades, 1.14x balance
iter-024 (5 symbols, add TRX keep NEAR): 601 trades, 1.51x balance

Adding 94 trades (TRX) didn't proportionally improve IS monthly
Sharpe (+0.64 vs +0.61). The seed variance dominates over trade
density improvements at this scale. To push IS mean above 1.0
across all 10 seeds, we need either:
- Fundamentally better per-trade signal (feature engineering / retraining)
- Much more trades (600 → 1000+)
- Lower variance per seed (hyperparameter search improvements)

## Next iteration (iter-v2/025)

Try TONUSDT (The Open Network) replacing NEAR:
- Launched 2021 Q4 but mostly illiquid in 2022 (low exposure to the bear)
- Smaller 2022 drawdown in IS distribution
- Different narrative (Telegram blockchain, not a standard L1)
- Features exist

Expected: NEAR's IS drag (−20.50) goes away, replaced by TON's
potentially cleaner IS contribution. Keep 4-symbol structure
(cleaner than 5-symbol for fair comparison).

## MERGE / NO-MERGE

**NO-MERGE**. 10-seed mean OOS monthly +0.97 just below 1.0,
and seed 456 went negative. Balance goal achieved but absolute
threshold not met.
