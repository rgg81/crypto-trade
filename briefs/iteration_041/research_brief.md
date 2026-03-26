# Research Brief: 8H LightGBM Iteration 041 — EXPLORATION

## 0. Data Split: OOS cutoff 2025-03-24. Full data range.

## 1. Change: ATR-scaled dynamic barriers (replaces fixed 4%/2%)

### Root Cause of Year-1 Failure
BTC 8h candle volatility by year:
- 2021: avg range 3.99%, 85% of candles >2% range
- 2023: avg range 1.88%, 35% of candles >2% range

With fixed SL=2%, a single 2021 candle can stop you out from normal noise. The barriers need to SCALE with volatility.

### New Approach: TP = 2×ATR(14), SL = 1×ATR(14)
- Maintains 2:1 reward/risk ratio (break-even 33.3%)
- In 2021 (ATR≈$1500 on BTC, ~4%): TP≈8%, SL≈4% → wider, fewer noise stop-outs
- In 2023 (ATR≈$500, ~2%): TP≈4%, SL≈2% → tighter, faster resolution
- Automatically adapts to any market condition

### Implementation
- **Labeling**: For each candle, compute ATR(14) at that candle. Use ATR-scaled TP/SL.
- **Backtest execution**: At trade entry, compute ATR(14). Set TP = entry ± 2*ATR, SL = entry ± 1*ATR.
- **Optuna**: Instead of optimizing fixed TP/SL percentages, optimize the ATR multipliers (tp_atr_mult, sl_atr_mult).

## 2. BTC+ETH, confidence threshold 0.50-0.85, 12mo, 50 trials, seed 42.

## Exploration/Exploitation Tracker
Last 10: [E, X, E, E, E, X, X, E, X, **E**] → 6/10 = 60%
