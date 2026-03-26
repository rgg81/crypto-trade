# Research Brief: 8H LightGBM Iteration 029 — EXPLORATION

## 0. Data Split: OOS cutoff 2025-03-24.

## 1. Change: Long-Period Features Only (period ≥ 20)

### Rationale (user feedback)
8h candles have 3 candles/day. Short-period features (RSI_5, Stoch_5, ROC_3) capture intra-day noise. Features with period ≥ 20 represent 7+ days of lookback — they capture weekly/monthly trends which are more stable and predictable.

### Implementation
Use `feature_columns` parameter (from iter 003) to pass only the 93 features with period ≥ 20 or no period. Drops 92 noisy short-period features.

### Expected Impact
- Less noise → more stable predictions (fewer direction flips)
- Model focuses on trend-level signals, not hourly oscillations
- Aligns with the finding that BTC/ETH predict LARGER moves better (iter 027: 46% WR at 8%/4%)

## 2. Everything Else Unchanged
BTC+ETH, classification, TP=4%/SL=2%, timeout=4320, threshold 0.50-0.85, 12mo, 50 trials, seed 42.
