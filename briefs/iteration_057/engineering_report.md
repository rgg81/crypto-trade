# Engineering Report: Iteration 057

## Implementation Summary

Added 56 daily-equivalent slow features (3x lookback multiplier) to all 6 feature modules per the research brief. Also modified `_discover_feature_columns()` to scope feature discovery to backtest symbols only (previously intersected ALL parquets in the directory, limiting to old 106-feature schema).

## Changes Made

### Feature Pipeline (6 files)
- `momentum.py`: RSI 42/63, MACD (21,63,9), Stochastic 42, Williams 42, ROC 42/63, MOM 42/63
- `volatility.py`: ATR 42/63, NATR 42/63, BB 42/60, Garman-Klass 63/90, Parkinson 63/90, HistVol 63/90
- `trend.py`: ADX 42 (+DI/-DI), Aroon 75, Supertrend (42,3.0), EMA 150, SMA 150, EMA cross (21,100), SMA cross (50,150)
- `volume.py`: CMF 42, MFI 42, Taker SMA 90, Vol pctchg 42/63, Vol relative 90
- `mean_reversion.py`: BB%B 42/60, Z-score 150, RSI extreme 42, high/low 150, dist SMA 100
- `statistical.py`: Returns 42/63, Log returns 42, Skew 63/90, Kurtosis 63/90

### LightGBM Strategy
- `lgbm.py`: `_discover_feature_columns()` now accepts `symbols` param; `compute_features()` passes the backtest symbol list to avoid stale parquet intersections.

## Feature Count
- Before: 106 (intersection across ~800 symbol parquets, old schema)
- After: 242 (intersection scoped to BTCUSDT + ETHUSDT only)
- New slow features: 56
- Features already present but excluded by old intersection: 80

## Backtest Results

**EARLY STOP** — Year 2024 PnL = -23.5% (WR 37.2%, 180 trades). Fail-fast triggered.

| Metric | IS (iter 057) | IS (baseline 047) |
|--------|--------------|-------------------|
| Sharpe | +0.35 | +1.60 |
| WR | 41.8% | 43.4% |
| PF | 1.07 | 1.31 |
| MaxDD | 79.3% | 64.3% |
| Trades | 479 | 574 |

No OOS data (early stopped before OOS period).

## Trade Execution Verification

Sampled 10 trades from trades.csv:
- Entry/exit prices correct (matched candle close prices)
- SL trades PnL = -4.1% (including 0.1% fee) ✓
- TP trades PnL = +7.9% (including 0.1% fee) ✓
- Timeout trades have variable PnL ✓

## Per-Symbol Breakdown (IS)
- BTC: 211 trades, 47.4% WR, +118.5% PnL
- ETH: 268 trades, 37.3% WR, -43.8% PnL

ETH was the primary drag. BTC remained modestly profitable but weaker than baseline.

## Deviations from Brief

None. Implementation followed the brief exactly. The total feature count is 242 (higher than expected ~150) because the symbol-scoped discovery also picked up ~80 features that were already in BTC/ETH parquets but excluded by the old all-symbol intersection.

## Root Cause Analysis

The 242-feature model significantly underperformed the 106-feature baseline. Likely causes:
1. **Curse of dimensionality**: 242 features with ~4400 training samples gives a features-to-samples ratio of ~18:1. Too high for reliable tree splits.
2. **Correlated features**: Slow features (RSI_42, RSI_63) are highly correlated with existing ones (RSI_21, RSI_30), adding noise without new signal.
3. **Optuna instability**: With 242 features, the hyperparameter search space is effectively larger. Most trials produced near-zero or negative Sharpe. Best first-month Sharpe was only 0.23 vs typically 0.5+ with 106 features.
4. **The 80 "extra" features**: Scoping discovery to BTC+ETH exposed ~80 features that were NOT in the baseline's 106-feature intersection. These include price-level features (raw EMA/SMA values, OBV, A/D, VWAP) that may hurt the pooled BTC+ETH model due to different price scales.
