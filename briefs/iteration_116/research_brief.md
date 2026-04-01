# Iteration 116 Research Brief — Meme Model: Shorter Timeout (5 days)

**Type**: EXPLOITATION (single parameter change)
**Date**: 2026-04-01

## Section 0: Data Split (verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
IS: all data before 2025-03-24
OOS: all data from 2025-03-24 onward
```

## Objective

Improve the DOGE+SHIB meme model (iter 114: OOS Sharpe +0.29) by reducing timeout from
7 days (10080 min) to 5 days (7200 min).

## Rationale

Iter 115 OOS exit analysis for meme coins:
- SL: 55% of trades, avg PnL -4.92% — too many stops
- TP: 26% of trades, avg PnL +9.64% — good when they hit
- Timeout: 19% of trades, avg PnL +2.13% — timeouts are profitable on avg

Meme coins are more volatile than BTC/ETH (NATR ~4% vs ~2%). A 5-day timeout:
1. **Reduces label leakage gap**: 15 candles × 2 symbols = 30 rows (was 44)
2. **More labeled samples**: Shorter scan window → more decisive labels (fewer timeouts)
3. **Better matches meme tempo**: High volatility → faster resolution
4. **Less time in drawdown**: Losing trades exit sooner

## Single Variable Change

| Parameter | Iter 114 | Iter 116 |
|-----------|----------|----------|
| timeout_minutes | 10080 (7 days) | **7200 (5 days)** |
| label_timeout_minutes | 10080 | **7200** |

Everything else identical: 67 features, ATR labeling (2.9x/1.45x), 24-month window,
5-seed ensemble, 2-candle cooldown.

## Expected Impact

- IS Sharpe should improve (tighter labels, less leakage)
- SL rate should decrease (less time exposed to adverse moves)
- Timeout rate may increase (shorter window to hit TP/SL)
- Trade count may change slightly (different labels → different signals)
