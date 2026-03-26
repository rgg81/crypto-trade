# Research Brief: 8H LightGBM Iteration 037 — EXPLORATION

## 0. Data Split: OOS cutoff 2025-03-24. Full data range.

## 1. Change: Add slow features (3x lookback multiplier) for ALL symbols

### Rationale (user feedback)
On 8h candles, standard features (RSI_14, SMA_100) capture 4.7-day and 33-day trends. By using 3x periods (RSI_42, SMA_300), we capture 14-day and 100-day trends — equivalent to daily indicators. These are more stable and less noisy.

### Critical: regenerated for ALL 760 symbols
Iter 036 proved that the global intersection (106 features) outperforms symbol-scoped (185 features). Slow features must be in ALL parquets to survive the intersection.

### New features (~18 slow features added per symbol):
- slow_rsi_14d, slow_rsi_21d, slow_rsi_30d (RSI at daily equivalent)
- slow_sma_20d, slow_sma_50d, slow_sma_100d (SMA at daily equivalent)
- slow_ema_21d, slow_ema_50d
- slow_atr_14d, slow_adx_14d, slow_plus_di_14d, slow_minus_di_14d
- slow_bb_bandwidth_20d, slow_bb_pctb_20d
- slow_return_5d, slow_return_10d, slow_return_20d

## 2. Everything Else: Baseline config (BTC+ETH, 4%/2%, 0.85 threshold, 106+slow features from global intersection).
