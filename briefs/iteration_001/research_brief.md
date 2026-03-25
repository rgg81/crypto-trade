# Research Brief: 8H LightGBM Iteration 001

## 0. Data Split & Backtest Approach

- OOS cutoff date: **2025-03-24** (project-level constant, applies to all iterations)
- The researcher used ONLY IS data (before 2025-03-24) for all design decisions below
- The walk-forward backtest runs on the FULL dataset (IS + OOS) as one continuous process
- Monthly retraining with timeseries CV, 12-month minimum training window (existing approach, unchanged)
- The report layer splits backtest results at OOS_CUTOFF_DATE into two report batches
- **This is iteration 001** — first iteration, no baseline to compare against. Will merge to main if results are not broken.

## 1. Labeling

- **Method**: Triple barrier (TP / SL / timeout) — existing `labeling.py` implementation
- **Parameters**:
  - Take-profit: **4.0%**
  - Stop-loss: **2.0%** (2:1 reward/risk ratio)
  - Timeout: **4320 minutes** (3 days = 9 candles on 8h)
- **Label function**: Existing `label_trades()` in `strategies/ml/labeling.py`
  - Simulates both long and short from each candle
  - If one direction hits TP → label that direction
  - If both hit TP → label whichever hit first
  - If neither hits TP → use forward return direction
- **Weights**: Existing scheme — `weight = 1 + (|forward_return| / max_return) * 9`, range [1, 10]
- **Expected label distribution**: ~32% clear long, ~34% clear short, ~22% both-TP (resolved by first-hit), ~12% timeout
- **CRITICAL FIX**: Default `label_timeout_minutes` in `lgbm.py` is 120 (2 hours) — must be changed to **4320** for 8h candles

## 2. Symbol Universe

- **Approach**: All eligible symbols, single pooled model
- **Selection criteria** (all must pass):
  1. Ends with USDT (excludes BUSD, USDC duplicates)
  2. Does not contain "SETTLED" (contract rollovers)
  3. At least 1095 IS candles (1 year of 8h data before 2025-03-24)
  4. First candle before 2023-07-01 (sufficient walk-forward coverage)
- **Expected universe**: ~184 symbols
- **Includes delisted USDT symbols** with sufficient history (avoids survivorship bias)
- Symbol identity is NOT a feature — model must generalize

## 3. Data Filtering

- **Outlier handling**: None. Extreme candles are real events; SL=2% limits exposure.
- **Volume filter**: None. All eligible symbols have meaningful liquidity (p10 = $3.3M/candle).
- **History filter**: 1095 IS candles minimum (from symbol selection above).
- **Date exclusions**: None.
- **Feature NaN**: LightGBM native NaN handling (no imputation).
- **Pair deduplication**: USDT-only selection handles this.

## 4. Feature Candidates

- **Use existing features from the pipeline**: All 185 features across 6 groups:
  - Momentum (36): RSI, MACD, Stochastic, Williams %R, ROC, Momentum
  - Volatility (37): ATR, NATR, Bollinger Bands, range_spike, Garman-Klass, Parkinson, historical
  - Trend (30): ADX/±DI, Aroon, EMA, SMA, crosses, Supertrend, Parabolic SAR
  - Volume (25): OBV, CMF, MFI, A/D, VWAP, taker_buy_ratio, volume changes
  - Mean Reversion (25): BB %B, z-score, VWAP distance, RSI extremes, % from rolling high/low
  - Statistical (23): Returns (multi-lag), log returns, autocorrelation, skewness, kurtosis
- **New features to add**: None for iteration 001. The existing 185 features are comprehensive. Let Optuna select the most useful groups and period ranges.
- **Feature selection method**: Optuna group toggle + period range (existing `optimization.py`)

## 5. Model Spec

- **Model**: LightGBM binary classifier (existing `lgb.LGBMClassifier`)
- **Task**: Binary classification (short=0, long=1)
- **Hyperparameters**: Optuna search (existing search space in `optimization.py`):
  - n_estimators: 50-500
  - max_depth: 3-5
  - num_leaves: 15-127
  - learning_rate: 0.01-0.3 (log scale)
  - subsample: 0.5-1.0
  - colsample_bytree: 0.3-1.0
  - min_child_samples: 5-100
  - reg_alpha/lambda: 1e-8 to 10.0 (log scale)
- **Class weighting**: `is_unbalance=True` (existing)
- **Random seed**: 42 (existing default)

## 6. Walk-Forward Configuration

- **Retraining frequency**: Monthly (existing `walk_forward.py`)
- **Minimum training window**: 12 months (existing default)
- **Timeseries CV folds**: 5 (existing default)
- **Optuna trials**: 50 per month (existing default)
- **Confidence threshold**: Optimized by Optuna in range 0.50-0.55 (existing)
- **Training days trimming**: Optimized by Optuna in range 10-500 days (existing)
- **Embargo period**: None explicitly — TimeSeriesSplit provides natural forward-only splits

## 7. Backtest Requirements

- **Position sizing**: Fixed amount per trade (`max_amount_usd` from BacktestConfig)
- **Fees**: 0.1% per trade (Binance futures taker rate) — existing `fee_pct` parameter
- **Funding rate**: Excluded for iteration 001 (simplification)
- **Slippage model**: None for iteration 001 (simplification)
- **Max positions**: 1 per symbol (existing behavior — no new order if position open)
- **Risk limits**:
  - Stop-loss: 2.0% per trade
  - Take-profit: 4.0% per trade
  - Timeout: 4320 minutes (3 days)

## 8. Report Requirements

Two separate report directories split at OOS_CUTOFF_DATE (2025-03-24):

```
reports/iteration_001/
├── in_sample/              # Trades with entry_time < 2025-03-24
│   ├── quantstats.html
│   ├── trades.csv
│   ├── daily_pnl.csv
│   ├── monthly_pnl.csv
│   ├── per_regime.csv      # Performance by BTC NATR/ADX regime
│   ├── per_symbol.csv      # Top/bottom symbol attribution
│   └── feature_importance.csv
├── out_of_sample/          # Trades with entry_time >= 2025-03-24
│   ├── quantstats.html
│   ├── trades.csv
│   ├── daily_pnl.csv
│   ├── monthly_pnl.csv
│   ├── per_regime.csv
│   └── per_symbol.csv
└── comparison.csv          # Side-by-side IS vs OOS metrics with OOS/IS ratios
```

### comparison.csv Format

```csv
metric,in_sample,out_of_sample,ratio
sharpe,X.XX,X.XX,X.XX
sortino,X.XX,X.XX,X.XX
max_drawdown,X.XX%,X.XX%,X.XX
win_rate,X.XX%,X.XX%,X.XX
profit_factor,X.XX,X.XX,X.XX
total_trades,NNNN,NNNN,X.XX
calmar_ratio,X.XX,X.XX,X.XX
```

### Regime Classification for Reports

Use BTC NATR(14) and ADX(14) medians computed from IS data as fixed thresholds:
- trending_volatile: ADX > median AND NATR > median
- trending_quiet: ADX > median AND NATR ≤ median
- choppy_volatile: ADX ≤ median AND NATR > median
- mean_reverting_quiet: ADX ≤ median AND NATR ≤ median

## Engineering Notes

### What Already Exists and Works
- `labeling.py`: Triple barrier — use as-is, just change timeout parameter
- `optimization.py`: Full Optuna pipeline — use as-is
- `lgbm.py`: Walk-forward with lazy monthly retraining — use as-is, update defaults
- `walk_forward.py`: Monthly split generation — use as-is
- `feature_store.py`: Parquet I/O — use as-is
- Feature parquet files: Already generated for all 760 symbols

### What Needs to Be Built
1. **OOS_CUTOFF_DATE constant** in `config.py`
2. **Report splitting layer**: After backtest completes, split trades at OOS cutoff, generate two report sets
3. **comparison.csv generator**: Side-by-side metrics with OOS/IS ratios
4. **Per-regime report**: Tag each trade with BTC regime, aggregate performance by regime
5. **Per-symbol report**: PnL attribution by symbol
6. **Feature importance export**: From final LightGBM model per walk-forward month
7. **Symbol universe filtering**: Apply the 4 selection criteria to build the symbol list
8. **Default parameter updates**: label_timeout_minutes=4320, label_tp_pct=4.0, label_sl_pct=2.0
