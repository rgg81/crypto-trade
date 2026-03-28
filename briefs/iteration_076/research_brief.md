# Research Brief: 8H LightGBM Iteration 076

**Type: EXPLORATION** — ATR-aligned dynamic labeling

## 0. Data Split & Backtest Approach

- OOS cutoff date: 2025-03-24 (project-level constant, applies to all iterations)
- The researcher used ONLY IS data (before 2025-03-24) for all design decisions below
- The walk-forward backtest runs on the FULL dataset (IS + OOS) as one continuous process
- Monthly retraining with timeseries CV, 24-month training window, 5 CV folds, 50 Optuna trials
- The report layer splits backtest results at OOS_CUTOFF_DATE into two report batches

## Research Analysis (Mandatory — 7 consecutive NO-MERGE)

### Category A: Feature Contribution Analysis

Single LightGBM trained on full IS period (11,454 samples, 106 features):

**Per-group importance:**
| Group | Importance % | Features | Avg Importance |
|-------|-------------|----------|----------------|
| volatility | 52.4% | 45 | 44 |
| statistical | 23.9% | 24 | 38 |
| mean_reversion | 15.9% | 16 | 38 |
| momentum | 7.3% | 19 | 15 |
| trend | 0.5% | 2 | 9 |

**Top 10 features:**
1. vol_vwap (8.0%) — VWAP level
2. vol_ad (6.2%) — Accumulation/Distribution
3. vol_obv (5.6%) — On Balance Volume
4. stat_autocorr_lag5 (3.9%) — 5-lag autocorrelation
5. mr_dist_vwap (3.4%) — distance from VWAP
6. mr_pct_from_low_100 (3.0%) — position vs 100-candle low
7. vol_atr_21 (2.9%) — ATR 21-period
8. stat_skew_50 (2.8%) — 50-period skewness
9. stat_autocorr_lag1 (2.8%) — 1-lag autocorrelation
10. stat_kurtosis_30 (2.5%) — 30-period kurtosis

**Key finding:** Volatility + statistical features dominate (76.3%). Momentum is minimal (7.3%), trend is negligible (0.5%). The model trades volatility patterns, not momentum or trend. Only 3 features have zero importance.

### Category C: Labeling Analysis

- **Label distribution:** 54.4% long / 45.6% short (8.8% imbalance — acceptable)
- **Label flip rate:** 19.4% (well below 60% noisy threshold — predictions are stable)
- **Exit reasons:** TP 32.2%, SL 51.2%, timeout 16.6%
- **Timeout analysis:** 42/62 timeouts profitable (68%), avg PnL +1.64%. Only 18 with |return| < 1% — insufficient for ternary labeling
- **Break-even WR:** ~33% for 2:1 RR. Actual WR 43.4% → 10.1pp edge

**Prediction stability finding (disproves iter 075 idea #1):**
- BTC: 12% flip rate, flips have WR 42.9% vs consistent 42.0% (no difference)
- ETH: 17% flip rate, flips have WR **58.8%** vs consistent 41.6% (flips are BETTER)
- **Prediction smoothing would HURT performance** — when the model changes direction, it's a genuine regime change signal

### Category E: Trade Pattern Analysis

- **SHORT >> LONG:** SHORT WR 46.5% vs LONG 40.9% (+5.6pp), SHORT PnL 215.8% vs LONG 48.6%
- **ETH SHORT best combo:** 51.1% WR. ETH LONG worst: 38.5% WR
- **Monthly balance:** 18/36 positive months (50%), largest draw: Jun 2024 (-25.4%), best: Jun 2022 (+68.5%)
- **TP PnL distribution:** median +6.44%, max +25.39% (dynamic ATR creates variance)
- **SL PnL distribution:** median -3.66%, std 1.48% (also varies due to ATR)
- **Holding time:** TP median 72h, SL median 56h, timeout always 168h

### Category F: Statistical Rigor

- **Bootstrap WR 95% CI:** [38.6%, 48.5%] — doesn't include break-even (33.3%)
- **Binomial test WR > break-even:** p = 3.1e-05 (highly significant)
- **Per-trade Sharpe CI:** [0.025, 0.222] — doesn't include zero
- **Mean PnL 95% CI:** [0.13%, 1.28%]
- **Signal is REAL but noisy.** The strategy has genuine edge, but the per-trade variance is high.

## Core Hypothesis: Label-Execution Barrier Mismatch

The baseline has a structural mismatch between training and execution:
- **Training:** Fixed TP=8%, SL=4% triple barrier labels
- **Execution:** Dynamic ATR barriers — TP=2.9×NATR_21, SL=1.45×NATR_21

NATR_21 distribution across IS candles:
| Percentile | NATR_21 | Exec TP (×2.9) | Exec SL (×1.45) |
|-----------|---------|----------------|-----------------|
| P10 | 1.63% | 4.73% | 2.37% |
| P25 | 2.11% | 6.13% | 3.06% |
| **P50** | **2.78%** | **8.05%** | **4.03%** |
| P75 | 3.71% | 10.77% | 5.38% |
| P90 | 4.98% | 14.45% | 7.23% |

**49.4% of candles have execution barriers tighter than training labels.** In quiet markets (P10), the execution TP is only 4.73% but the model learned 8%. The model's confidence about an 8% TP is irrelevant when the barrier is only 5%.

**Proposed fix:** Use ATR-aligned dynamic barriers during BOTH labeling and execution. The model learns the actual risk/reward profile for each candle's volatility environment.

## 1. Labeling

- Method: Triple barrier with **dynamic ATR barriers** (NOT fixed percentages)
- Parameters:
  - TP = 2.9 × NATR_21 (matches execution barrier exactly)
  - SL = 1.45 × NATR_21 (matches execution barrier exactly)
  - Timeout = 7 days (10,080 minutes, unchanged)
  - Fee = 0.1% (unchanged)
- Implementation: Compute raw ATR from NATR: `atr_raw = close * natr_21 / 100`. Pass to `label_trades()` with `atr_values=atr_raw, tp_pct=2.9, sl_pct=1.45`
- The existing `label_trades()` ATR mode handles this correctly

## 2. Symbol Universe

- Unchanged: BTCUSDT + ETHUSDT only
- Rationale: Previous attempts to expand (iter 071) catastrophically failed

## 3. Data Filtering

- Unchanged from baseline
- Minimum history: 24 months training window
- No outlier removal, no volume filter

## 4. Feature Candidates

- Unchanged: 106 features from global intersection across 760 parquet files
- No new features (iter 070 showed adding features hurts with current sample size)
- No feature pruning (iter 073 showed removing features hurts)

## 5. Model Spec

- Model: LightGBM binary classification (unchanged)
- Ensemble: 3 models with seeds [42, 123, 789]
- Hyperparameters: Optuna-optimized per month (50 trials, 5 CV folds)
- Confidence threshold: Optuna range [0.50, 0.85]
- Class weighting: is_unbalance=True

## 6. Walk-Forward Configuration

- Training window: 24 months
- Retraining: monthly
- CV folds: 5 (TimeSeriesSplit)
- Optuna trials: 50
- No embargo period

## 7. Backtest Requirements

- Position sizing: fixed $1000 per trade
- Fees: 0.1% (Binance futures taker)
- Execution: Dynamic ATR barriers (TP=2.9×NATR_21, SL=1.45×NATR_21)
- Cooldown: 2 candles (16h)
- Timeout: 7 days

## 8. Report Requirements

Standard IS/OOS split at 2025-03-24:
- in_sample/ and out_of_sample/ report directories
- comparison.csv with side-by-side metrics
- trades.csv, daily_pnl.csv, monthly_pnl.csv, per_symbol.csv, per_regime.csv
- quantstats.html tearsheets

## Key Change from Baseline

| Aspect | Baseline (068) | Iteration 076 |
|--------|---------------|---------------|
| **Labeling TP** | Fixed 8% | Dynamic: 2.9 × NATR_21 |
| **Labeling SL** | Fixed 4% | Dynamic: 1.45 × NATR_21 |
| Execution TP | 2.9 × NATR_21 | 2.9 × NATR_21 (same) |
| Execution SL | 1.45 × NATR_21 | 1.45 × NATR_21 (same) |
| Everything else | — | Unchanged |

Single variable change: labeling barrier type (fixed → dynamic ATR). This creates consistency between training labels and execution barriers.
