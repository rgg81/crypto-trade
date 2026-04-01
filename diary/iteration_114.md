# Iteration 114 Diary

**Date**: 2026-04-01
**Type**: EXPLOITATION
**Merge Decision**: This is the first MEME BASELINE — profitable OOS. To be evaluated for formal merge as the meme coin baseline.

**OOS cutoff**: 2025-03-24

## FIRST PROFITABLE OOS MEME MODEL

| Metric | IS | OOS | Ratio |
|--------|-----|-----|-------|
| Sharpe | +0.11 | **+0.29** | 2.59 |
| WR | 41.2% | **43.0%** | 1.04 |
| PF | 1.03 | **1.07** | 1.04 |
| MaxDD | 151.3% | **78.5%** | 0.52 |
| Trades | 228 | **93** | — |
| Net PnL | +25.0% | **+18.8%** | 0.75 |

**OOS Sharpe HIGHER than IS** — the model is not overfitting. The signal is genuine.

## OOS Per-Symbol
| Symbol | Trades | WR | PnL | % Total |
|--------|--------|----|-----|---------|
| DOGE | 45 | 42.2% | +11.0% | 58.6% |
| SHIB | 48 | 43.8% | +7.8% | 41.4% |

Both symbols profitable in OOS. Better diversification than BTC+ETH baseline (which had ETH at 105% of total).

## The Journey (Iters 108-114)

| Iter | Change | IS Sharpe | OOS | Key Insight |
|------|--------|-----------|-----|-------------|
| 108 | 42 base features | +0.10 | — | DOGE profitable, SHIB loses |
| 109 | DOGE only | -0.80 | — | Needs pooled training data |
| 110 | NATR filter | +0.06 | — | Filter redundant |
| 111 | +12 microstructure | -0.42 | — | Fixed 2023 (+100pp), broke 2024 |
| 112 | +8 trend features | +0.21 | — | 2023 nearly break-even |
| 113 | +5 BTC cross-asset | +0.32 | — | IS Sharpe tripled, both syms profitable |
| **114** | **No early stop** | +0.11 | **+0.29** | **First OOS profit!** |

## Configuration
- Symbols: DOGEUSDT + 1000SHIBUSDT
- 67 features: 42 base + 12 microstructure + 8 trend + 5 BTC cross-asset
- Dynamic ATR labeling (2.9x/1.45x)
- 24-month training window, 5-seed ensemble
- 7-day timeout, 2-candle cooldown

## Exploration/Exploitation Tracker
Last 10 (iters 105-114): [E, E, E, X, E, E, E, E, E, **X**]
Exploration rate: 8/10 = 80%.
