# Research Brief: 8H LightGBM Iteration 057

**Type**: EXPLORATION (new feature generation — daily-equivalent slow features)

## 0. Data Split & Backtest Approach
- OOS cutoff date: 2025-03-24 (project-level constant, applies to all iterations)
- The researcher used ONLY IS data (before 2025-03-24) for all design decisions below
- The walk-forward backtest runs on the FULL dataset (IS + OOS) as one continuous process
- Monthly retraining with timeseries CV, 24-month training window
- The report layer splits backtest results at OOS_CUTOFF_DATE into two report batches

## 1. Hypothesis

The current 106 features max out at short lookback periods (most ≤ 10 days on 8h candles). Standard daily indicators (RSI-14, ADX-14, ATR-14) require period=42 on 8h candles (3 candles/day × 14 days). The model has never seen daily-equivalent indicators.

Iter 056's feature importance analysis found that **long-period features consistently outrank short-period ones** (e.g., autocorrelation and kurtosis at period 50 are genuine signals). By adding daily-equivalent lookback periods (3x multiplier), the model gains access to stable, trend-level signals that reduce noise and capture multi-day patterns.

This is the #1 untested structural improvement identified across iters 048-056.

## Research Analysis (from iter 056, categories A + D)

### A. Feature Contribution Analysis
- Top features are price-level (VWAP 8.25%, A/D 5.27%, OBV 3.65%)
- Momentum group is weakest: 36 features contribute only 4.45% total importance
- Autocorrelation and kurtosis at period 50 are genuine signals
- 55 features have near-zero importance (<0.05%)
- Long-period features consistently outrank short-period variants within each group

### D. Feature Frequency & Lookback Analysis
- 15/25 feature types lack lookbacks > 10 days (30 candles on 8h)
- Current max RSI period is 30 (≈ daily RSI-10). Standard daily RSI-14 = period 42
- ADX max 21 (7 days), ATR max 21 (7 days), NATR max 21 (7 days)
- MACD max (12,26,9) — no daily-equivalent variant
- The model sees only intra-day oscillations, missing multi-day trend structure

## 2. What Changes

Add daily-equivalent lookback periods (3x multiplier) to ALL 6 feature groups. ~45 new features.

### Momentum (add 10 features)
| Feature | Current max | Add periods | Daily equivalent |
|---------|------------|-------------|-----------------|
| RSI | 30 | 42, 63 | daily 14, 21 |
| MACD | (12,26,9) | (21,63,9) | daily ~(7,21,3) |
| Stochastic | 21 | 42 | daily 14 |
| Williams %R | 21 | 42 | daily 14 |
| ROC | 30 | 42, 63 | daily 14, 21 |
| MOM | 20 | 42, 63 | daily 14, 21 |

### Volatility (add 10 features)
| Feature | Current max | Add periods | Daily equivalent |
|---------|------------|-------------|-----------------|
| ATR | 21 | 42, 63 | daily 14, 21 |
| NATR | 21 | 42, 63 | daily 14, 21 |
| BB bandwidth/%B | 30 | 42, 60 | daily 14, 20 |
| Garman-Klass | 50 | 63, 90 | daily 21, 30 |
| Parkinson | 50 | 63, 90 | daily 21, 30 |
| Hist vol | 50 | 63, 90 | daily 21, 30 |

### Trend (add 9 features)
| Feature | Current max | Add periods | Daily equivalent |
|---------|------------|-------------|-----------------|
| ADX (+DI, -DI) | 21 | 42 | daily 14 |
| Aroon (up, down, osc) | 50 | 75 | daily 25 |
| Supertrend | (14, 3.0) | (42, 3.0) | daily 14 |
| EMA cross | (12, 50) | (21, 100) | slow cross |
| SMA cross | (20, 100) | (50, 150) | slow cross |

Note: EMA 150 and SMA 150 added for the crossover signals.

### Volume (add 7 features)
| Feature | Current max | Add periods | Daily equivalent |
|---------|------------|-------------|-----------------|
| CMF | 20 | 42 | daily 14 |
| MFI | 21 | 42 | daily 14 |
| Taker buy SMA | 50 | 90 | daily 30 |
| Volume %chg | 30 | 42, 63 | daily 14, 21 |
| Volume relative | 50 | 90 | daily 30 |

### Mean Reversion (add 7 features)
| Feature | Current max | Add periods | Daily equivalent |
|---------|------------|-------------|-----------------|
| BB %B | 30 | 42, 60 | daily 14, 20 |
| Z-score | 100 | 150 | daily 50 |
| RSI extreme | 21 | 42 | daily 14 |
| % from high/low | 100 | 150 | daily 50 |
| Dist SMA | 50 | 100 | daily ~33 |

### Statistical (add 6 features)
| Feature | Current max | Add periods | Daily equivalent |
|---------|------------|-------------|-----------------|
| Returns | 30 | 42, 63 | daily 14, 21 |
| Log returns | 20 | 42 | daily 14 |
| Skew | 50 | 63, 90 | daily 21, 30 |
| Kurtosis | 50 | 63, 90 | daily 21, 30 |

## 3. What Does NOT Change

- Labeling: triple barrier TP=8%, SL=4%, timeout=7 days
- Symbols: BTCUSDT + ETHUSDT only
- Training window: 24 months
- Walk-forward: monthly, 5 CV folds, 50 Optuna trials
- Confidence threshold: Optuna 0.50-0.85
- is_unbalance=True + PnL sample weights (confirmed optimal in iters 055-056)
- Seed: 42

## 4. Model Spec
- Model: LightGBM classification
- is_unbalance: True
- Hyperparameters: Optuna-optimized
- Random seed: 42

## 5. Expected Outcome

The model gains ~45 new features at daily-equivalent timescales. These capture multi-day trends, momentum regimes, and volatility structure that the current short-period features miss. Expected impact:
- More stable predictions (less flip-flopping between candles)
- Better trend-following: daily RSI-14 and ADX-14 are standard institutional signals
- Potentially higher feature importance for slow features, confirming the hypothesis

## 6. Risk

- More features could increase noise if slow features are redundant with existing ones. LightGBM's built-in feature importance should handle this (low-importance features get few splits).
- Longer lookback periods mean more NaN rows at the start of each symbol's history. This reduces training data slightly for early months.
- ~150 total features is still well within LightGBM's capability for this dataset size.
