# Iteration 053 — EXPLORATION (BNB+LINK independent pair)

## NO-MERGE (EARLY STOP): IS only. IS Sharpe +1.08, WR 40.6% — decent IS but no OOS data. Early stopped.

**OOS cutoff**: 2025-03-24

## Results (IS only)

| Period | Sharpe | WR | PF | MaxDD | Trades | PnL |
|--------|--------|-----|------|-------|--------|------|
| IS | +1.08 | 40.6% | 1.18 | 79.9% | 411 | +172% |

**Per-symbol IS**: BNB 156 trades (+87%, 50.6%), LINK 255 (+85%, 49.4%) — balanced contribution

## What Happened

Tested BNB+LINK as an independent pair (separate model from BTC+ETH). IS results are decent: Sharpe +1.08, both symbols contribute equally. However, early stopped before reaching OOS period — likely failed a yearly checkpoint.

BNB+LINK's IS Sharpe (+1.08) is lower than BTC+ETH baseline IS (+1.60). The pair has some predictability at 8%/4% but not as strong as BTC+ETH.

## Decision: NO-MERGE (EARLY STOP)

No OOS validation. IS metrics below baseline. BNB+LINK doesn't match BTC+ETH predictability.

## Exploration/Exploitation Tracker

Last 10: [..., E, X, E, E] (E=explore, X=exploit)
Type: EXPLORATION (new independent symbol pair)
