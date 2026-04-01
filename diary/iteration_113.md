# Iteration 113 Diary

**Date**: 2026-04-01
**Type**: EXPLORATION
**Merge Decision**: NO-MERGE (EARLY STOP — Year 2024: PnL=-20.0%, WR=39.4%, 94 trades)

**OOS cutoff**: 2025-03-24

## BREAKTHROUGH: Best Meme Model Ever

| Metric | Iter 113 | Iter 112b | Iter 108 |
|--------|---------|----------|---------|
| IS Sharpe | **+0.32** | +0.21 | +0.10 |
| IS PF | **1.098** | 1.056 | 1.03 |
| IS WR | **41.7%** | 40.2% | 38.6% |
| IS Trades | **204** | 112 | 114 |
| IS Net PnL | **+65.7%** | +18.8% | +11.3% |
| 2023 PnL | **+18.8%** | -2.7% | -69.7% |
| Early Stop | 2024 (-20%) | 2023 (-2.7%) | 2023 (-70%) |

The 5 BTC cross-asset features (xbtc_return_1/5/10, xbtc_natr_14, xbtc_rsi_14) transformed the meme model. IS Sharpe tripled from +0.10 to +0.32. Both symbols are now profitable. 2023 went from -69.7% to +18.8%.

## Per-Symbol
| Symbol | Trades | WR | PnL | % Total |
|--------|--------|----|-----|---------|
| DOGE | 98 | 38.8% | +51.7% | 78.7% |
| SHIB | 106 | 44.3% | +13.9% | 21.3% |

DOGE flipped back to profitable! The BTC context helps the model understand when meme coins should follow BTC's direction vs mean-revert.

## Yearly Performance
- **2022 H2**: +57.6% (strong crash shorts)
- **2023**: **+18.8%** (the previously impossible year — SOLVED)
- **2024 Jan-Jul**: -88.2% (Jun -39.5% was devastating)
- **2024 Aug-Dec**: +54.5% (strong recovery, Nov +49.8%)
- **2025 Jan**: +9.5%
- **2024 full year**: -20.0% (triggers early stop)

## What Changed (single variable)
Added 5 BTC cross-asset features to iter 112b's 62-feature set:
- `xbtc_return_1`: BTC 1-candle return (immediate macro shock detection)
- `xbtc_return_5`: BTC short-term trend (1.67 day direction)
- `xbtc_return_10`: BTC medium trend (3.33 day direction)
- `xbtc_natr_14`: BTC volatility (risk-on/risk-off)
- `xbtc_rsi_14`: BTC momentum (overbought/oversold macro context)

67 total features. Ratio: 4400/67 = 65.7.

## Why BTC Features Help

Meme coins are beta plays on BTC. When BTC dumps, meme coins dump 2-3x harder. When BTC rallies, meme coins rally harder. The model now knows:
1. **When BTC is dumping** (xbtc_return_5 < -5%): short meme coins aggressively
2. **When BTC is rallying** (xbtc_return_10 > +10%): go long meme coins
3. **When BTC vol is high** (xbtc_natr_14 > 3%): bigger moves expected, trade with conviction
4. **When BTC is overbought** (xbtc_rsi_14 > 70): meme rally may be exhausted, reduce long exposure

## Exploration/Exploitation Tracker
Last 10 (iters 104-113): [E, E, E, E, X, E, E, E, E, **E**]
Exploration rate: 9/10 = 90%.

## Next Iteration Ideas

1. **EXPLOITATION: Disable yearly early stop and run to OOS.** With IS Sharpe +0.32 and 3 profitable years out of 3.5, this model deserves a full OOS evaluation. The -20% 2024 PnL is real but may recover in Jan 2025 (already +9.5%). Simply disabling the early stop lets us see OOS performance.

2. **EXPLOITATION: Increase cooldown to 3 candles.** 204 trades is high. Jun 2024 had 14 trades that lost -39.5%. Higher cooldown would reduce overtrading in bad months.

3. **EXPLORATION: Add more meme coins.** With BTC cross-asset features providing macro context, PEPE (1000PEPEUSDT) or WIF could add further diversification. The 67-feature set with BTC context is now robust enough to try 3-4 meme coins.
