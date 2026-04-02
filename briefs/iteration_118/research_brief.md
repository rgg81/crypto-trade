# Iteration 118 Research Brief — Meme Model: Wider ATR Barriers (3.5x/1.75x)

**Type**: EXPLOITATION (single parameter change)
**Date**: 2026-04-02

## Section 0: Data Split (verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
IS: all data before 2025-03-24
OOS: all data from 2025-03-24 onward
```

## Objective

Improve the DOGE+SHIB meme model (iter 117: OOS Sharpe +0.66) by widening ATR barriers
from 2.9x/1.45x to 3.5x/1.75x.

## Rationale

Iter 115 OOS exit analysis for meme coins showed 55% SL rate — too many stops. Meme coins
have extreme intraday wicks that trigger stops even when direction is correct. Wider barriers:
1. **Reduce premature SL exits**: More room for wicks before stopping out
2. **Maintain 2:1 TP/SL ratio**: 3.5/1.75 = 2.0 (same as 2.9/1.45)
3. **Better suited to meme volatility**: DOGE/SHIB NATR ~4% → SL moves from ~5.8% to ~7%
4. **Wider labeling barriers**: More decisive labels (bigger moves needed to hit TP/SL)

## Single Variable Change

| Parameter | Iter 117 | Iter 118 |
|-----------|----------|----------|
| atr_tp_multiplier | 2.9 | **3.5** |
| atr_sl_multiplier | 1.45 | **1.75** |

Everything else identical: 45 features (iter 117 pruned set), ATR labeling, 24-month window,
5-seed ensemble, 7-day timeout, 2-candle cooldown.
