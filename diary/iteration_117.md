# Iteration 117 Diary

**Date**: 2026-04-02
**Type**: EXPLOITATION (feature pruning)
**Merge Decision**: No standalone merge (tracking meme improvements for future combined portfolio)

**OOS cutoff**: 2025-03-24

## MAJOR IMPROVEMENT — Meme OOS Sharpe +0.66 (was +0.29)

| Metric | IS | OOS | Ratio | Iter 114 OOS |
|--------|-----|-----|-------|-------------|
| Sharpe | +0.93 | **+0.66** | 0.71 | +0.29 |
| WR | 44.8% | **45.2%** | 1.01 | 43.0% |
| PF | 1.28 | **1.17** | 0.91 | 1.07 |
| MaxDD | 90.5% | **53.0%** | 0.59 | 78.5% |
| Trades | 223 | **93** | — | 93 |
| Net PnL | +199.4% | **+45.9%** | 0.23 | +18.8% |

## OOS Per-Symbol

| Symbol | Trades | WR | PnL | % Total |
|--------|--------|----|-----|---------|
| SHIB | 49 | 46.9% | +26.9% | 58.5% |
| DOGE | 44 | 43.2% | +19.0% | 41.5% |

Both symbols solidly profitable with good balance.

## What Changed

Feature pruning from 67 → 45 features. Removed:
- 12 redundant lookback variants (kept best period only)
- 4 noisy microstructure features (vol_body, body_expansion, taker_accel, vol_trend)
- 4 redundant trend/cross-asset features (new_low_20, hh_ll_5, xbtc_return_10, xbtc_rsi_14)
- 2 additional low-info features

Samples-per-feature ratio improved from 65.7 to 97.8.

## Why It Worked

1. **Reduced noise**: 22 dropped features were mostly redundant lookback variants (e.g., natr_7 vs natr_14 vs natr_21). Keeping only one prevents the model from splitting on correlated noise.
2. **Better generalization**: Higher samples/feature ratio (97.8 vs 65.7) gives more robust splits.
3. **IS/OOS alignment**: IS Sharpe went from +0.11 to +0.93 — but OOS also improved from +0.29 to +0.66. The ratio of 0.71 is healthy (no overfitting).
4. **MaxDD halved**: From 78.5% to 53.0% — fewer noisy features means fewer spurious signals during drawdowns.

## Configuration

Same as iter 114 except: **45 features** (was 67). Everything else identical:
- Symbols: DOGEUSDT + 1000SHIBUSDT
- Labeling: Dynamic ATR (2.9x/1.45x)
- Training: 24 months, 5 CV folds, 50 Optuna trials
- Ensemble: 5-seed [42, 123, 456, 789, 1001]
- Timeout: 7 days, cooldown: 2 candles

## Exploration/Exploitation Tracker

Last 10 (iters 108-117): [E, E, E, E, E, X, E, E, X, **X**]
Exploration rate: 7/10 = 70%

## Next Iteration Ideas

1. **Combined portfolio test**: With meme OOS Sharpe +0.66 (up from +0.29), the combined BTC+ETH (+1.01) + DOGE+SHIB (+0.66) portfolio should be much closer to beating baseline. The higher meme Sharpe means less dilution.

2. **Further pruning**: Could try 35 features — even more aggressive removal.

3. **Wider ATR barriers**: TP=3.5x, SL=1.75x — give meme coins more room.

4. **18-month training window**: Shorter window for faster-evolving meme dynamics.
