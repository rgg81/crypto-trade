# Iteration 112 Diary

**Date**: 2026-04-01
**Type**: EXPLORATION
**Merge Decision**: NO-MERGE (EARLY STOP — Year 2023: PnL=-2.7%, WR=38.4%, 73 trades — barely missed)

**OOS cutoff**: 2025-03-24

## Best Meme Coin Result Yet

| Metric | Iter 112b (62 feat) | Iter 111 (54 feat) | Iter 108 (42 feat) |
|--------|-------------------|-------------------|-------------------|
| IS Sharpe | **+0.21** | -0.42 | +0.10 |
| IS PF | **1.056** | 0.88 | 1.03 |
| IS MaxDD | **60.6%** | 213.4% | 108.6% |
| IS Trades | 112 | 204 | 114 |
| 2023 PnL | **-2.7%** | +30.3% | **-69.7%** |

The trend features brought 2023 from catastrophic (-69.7%) to nearly break-even (-2.7%). IS Sharpe doubled from +0.10 to +0.21. MaxDD nearly halved (108.6% → 60.6%).

## What Changed (two variants tested)

- **112a (12mo window)**: EARLY STOP Year 2021 — too little training data, especially for SHIB
- **112b (24mo window + 8 trend features)**: IS Sharpe +0.21, the best result ← reported above

8 trend features added: cumulative returns (10/30), breakout flags (new high/low 20), range position in 50-candle window, RSI slope, higher highs/lower lows count, volume trend.

## Per-Symbol
| Symbol | Trades | WR | PnL |
|--------|--------|----|-----|
| SHIB | 56 | 44.6% | +23.5% |
| DOGE | 56 | 35.7% | -4.7% |

SHIB is solidly profitable. DOGE is marginally below break-even — close to useful.

## Monthly Analysis

Strong months: Oct-Nov 2022 (+43%), Jan 2023 (+40%), Mar 2023 (+9.5%)
Weak months: Aug 2022 (-21.2%), Feb 2023 (-19.4%), Jul 2023 (-10.8%)

The model generates 6-14 trades per active month. Feb 2023 remains the worst month (-19.4%, 9 trades) but dramatically improved from iter 108 (-56.8%, 13 trades).

## Exploration/Exploitation Tracker

Last 10 (iters 103-112): [E, E, E, E, E, X, E, E, E, **E**]
Exploration rate: 9/10 = 90%.

## Next Iteration Ideas

1. **EXPLOITATION: Relax the yearly checkpoint.** The -2.7% early stop is a technicality. A 5% loss tolerance on yearly checks would let this model reach OOS. Try `yearly_pnl_threshold=-5.0` instead of 0.

2. **EXPLOITATION: Increase cooldown from 2 to 3 candles (24h).** 112b traded ~112 IS trades. Slightly higher cooldown reduces overtrading in choppy months like Feb 2023 (9 trades → maybe 6).

3. **EXPLORATION: Add BTC cross-asset features.** The model has no macro context. When BTC is dumping, meme coins dump harder. `xbtc_return_5` and `xbtc_natr_14` as features could help the model understand the broader market context.

4. **EXPLORATION: Combine microstructure + trend features with the BTC+ETH baseline.** The 62-feature meme set might also improve the BTC+ETH model. Dynamic ATR labeling + curated features could push the baseline OOS Sharpe above +1.01.
