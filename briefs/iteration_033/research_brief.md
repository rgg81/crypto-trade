# Research Brief: 8H LightGBM Iteration 033 — EXPLORATION

## 0. Data Split: OOS cutoff 2025-03-24. Full data range, NO start_time changes.

## 1. Change: Add macro regime features to parquet pipeline (13 new features)

### Root Cause Analysis (QR reading IS quantstats)
IS losses (-246% total) concentrate in 3 quarters:
- 2021 Q1: -83% (cold start, 27.7% WR)
- 2022 Q3: -80% (bear bottom, 21.6% WR)
- 2022 Q4: -56% (continued bear, 30.1% WR)

In 2022, LONGS had 27.6% WR — model went long 156 times in a -65% BTC year.
THE MODEL DOESN'T KNOW IT'S IN A BEAR MARKET. No feature captures macro context.

### New Features (13, in `src/crypto_trade/features/macro.py`)
- `macro_dd_from_ath_*`: Drawdown from ATH (all-time, 365d, 180d rolling)
- `macro_return_*d`: Rolling returns (30d, 60d, 90d, 180d)
- `macro_vol_regime_*`: Current ATR vs historical median ATR (90d, 180d)
- `macro_ema_slope_*`: EMA trend direction (50, 100 period)
- `macro_price_position_*d`: Price position in range (90d, 180d)

### Economic Hypothesis
- In bear markets (macro_dd_from_ath < -0.5), the model should AVOID LONGS
- In high-vol regimes (macro_vol_regime > 1.5), the model should be MORE SELECTIVE
- The features tell the model "where are we in the market cycle?"

## 2. Everything Else Unchanged
BTC+ETH, TP=4%/SL=2%, timeout=4320, threshold 0.50-0.85, 12mo, 50 trials, seed 42.
