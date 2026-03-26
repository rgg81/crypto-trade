# Research Brief: 8H LightGBM Iteration 026 — EXPLORATION

## 0. Data Split
- OOS cutoff: 2025-03-24. Walk-forward on full dataset.

## 1. Change: Add Calendar + Interaction Features (NEW FEATURE GENERATION)

### Evidence (IS, iter 016 — Checklist E)
- **Hour-of-day**: 07:00 UTC WR=37.8% (+26.3% PnL), 23:00 WR=32.7% (-145.2% PnL). 5.1pp spread.
- **Day-of-week**: Wednesday WR=39.8% (+48.6%), Tuesday WR=30.9% (-76.1%). 8.9pp spread.
- These are strong calendar signals — the model currently has NO access to time-of-day or day-of-week information.

### New Features to Generate (injected during training, not in parquet)

**Calendar (3 features):**
- `hour_of_day`: 0, 8, or 16 (mapped from UTC hours 23, 7, 15)
- `day_of_week`: 0-6 (Monday=0, Sunday=6)
- `is_weekend`: 0 or 1

**Interaction (4 features, using top features from Checklist A):**
- `vol_vwap_x_trend_adx_21`: vol_vwap × trend_adx_21 (volume-price × trend strength)
- `stat_autocorr_lag1_x_vol_natr_14`: autocorrelation × volatility
- `mr_dist_vwap_x_trend_sma_cross_20_100`: mean reversion distance × trend cross
- `vol_taker_buy_ratio_sma_50_x_mom_rsi_14`: buy pressure × momentum

### Implementation
Inject these 7 features in `_train_for_month()` after loading features from parquet. Compute from master DataFrame (calendar) and from loaded features (interactions).

## 2. Everything Else Unchanged
BTC+ETH, classification, TP=4%/SL=2%, timeout=4320, threshold 0.50-0.85, 12mo, 50 trials, seed 42.

## Exploration/Exploitation Tracker
Last 10: [X, X, X, X, E, X, X, X, X, **E**] → 2/10 = 20% (still below 30%, needs more exploration)
