# Iteration 052 — EXPLORATION (add XRP to BTC+ETH pool)

## NO-MERGE (EARLY STOP): IS only. IS Sharpe +0.54 — XRP dragged portfolio down (-42% PnL, -37% of total). Early stopped, no OOS.

**OOS cutoff**: 2025-03-24

## Results (IS only)

| Period | Sharpe | WR | PF | MaxDD | Trades | PnL |
|--------|--------|-----|------|-------|--------|------|
| IS | +0.54 | 40.1% | 1.09 | 144.6% | 531 | +114% |

**Per-symbol IS**: ETH 167 trades (+127%, 112.3%), BTC 151 (+28%, 24.7%), XRP 213 (-42%, -37.0%)

## What Happened

Added XRPUSDT to the pooled BTC+ETH model. XRP generated the most trades (213) but had net negative PnL (-42%), dragging the portfolio down. IS Sharpe dropped from +1.60 (baseline) to +0.54. MaxDD exploded to 144.6%.

XRP's volatility profile doesn't match the 8%/4% barrier structure optimized for BTC+ETH. The model generates frequent but wrong signals for XRP.

## Decision: NO-MERGE (EARLY STOP)

IS-only, no OOS data. XRP is unprofitable at this configuration.

## Exploration/Exploitation Tracker

Last 10: [..., E, E, X, E] (E=explore, X=exploit)
Type: EXPLORATION (adding new symbol to pool)
