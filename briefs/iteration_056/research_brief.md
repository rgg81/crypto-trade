# Iteration 056 — Research Brief

## Type: EXPLOITATION

## Section 0: Data Split (verbatim, never changes)

```
OOS_CUTOFF_DATE = 2025-03-24
```

- **In-sample (IS)**: all data before 2025-03-24
- **Out-of-sample (OOS)**: all data from 2025-03-24 onward
- The walk-forward backtest runs on ALL data (IS + OOS) as one continuous process
- The reporting layer splits trade results at OOS_CUTOFF_DATE

---

## Section 1: Motivation

After 8 consecutive NO-MERGE iterations (048–055), we conducted mandatory full research (4 categories). The key finding: **the model uses redundant class-balancing mechanisms** — both LightGBM's internal `is_unbalance=True` AND external sample weights from labeling (scaled to [1, 10] by PnL magnitude). This double-correction was flagged in iter 055's code review but never tested in isolation.

The proposal: **remove `is_unbalance=True`** from LightGBM parameters, keeping sample weights active. This is a clean, single-variable exploitation test.

### Why this matters

- `is_unbalance=True` tells LightGBM to internally reweight classes by inverse frequency (e.g., if 40% long / 60% short, longs get 1.5x weight)
- Sample weights already encode PnL magnitude: high-profit trades get 10x weight, low-profit trades get 1x
- Using both mechanisms together over-corrects: a minority-class trade with high PnL gets boosted by BOTH systems simultaneously
- Iter 055 proved that adding MORE class balancing (`_balance_weights()`) hurt OOS by -0.63 Sharpe. The natural hypothesis: less class balancing may help OOS
- The model's WR is already balanced long/short (42.2% / 44.6%), so aggressive class rebalancing is unnecessary

---

## Section 2: Research Analysis (4 categories completed)

### Category A — Feature Contribution Analysis

**Per-group cumulative importance:**

| Category | Gain % | # Features | Gain/Feature |
|----------|--------|------------|--------------|
| trend | 28.73% | 39 | 0.74% |
| volume | 23.64% | 25 | 0.95% |
| volatility | 18.78% | 35 | 0.54% |
| statistical | 15.91% | 24 | 0.66% |
| mean_reversion | 8.49% | 26 | 0.33% |
| momentum | 4.45% | 36 | 0.12% |

**Top-10 features:**

| Rank | Feature | Gain % | Scale-Invariant? |
|------|---------|--------|------------------|
| 1 | vol_vwap | 8.25% | NO (cumulative price) |
| 2 | vol_ad | 5.27% | NO (cumulative) |
| 3 | vol_obv | 3.65% | NO (cumulative) |
| 4 | trend_ema_100 | 3.25% | NO (price-level) |
| 5 | trend_sma_100 | 3.18% | NO (price-level) |
| 6 | mr_dist_vwap | 2.82% | YES |
| 7 | vol_taker_buy_ratio_sma_50 | 2.74% | YES |
| 8 | trend_sma_50 | 2.60% | NO (price-level) |
| 9 | stat_kurtosis_50 | 2.45% | YES |
| 10 | stat_autocorr_lag1 | 2.30% | YES |

**Critical finding:** 6 of the top 8 features are price-level features. The model uses VWAP, OBV, A/D, EMA/SMA to distinguish BTC from ETH price ranges — acting as symbol identifiers rather than learning generalizable patterns. The 4 scale-invariant features in the top-10 (dist_vwap, taker_buy_ratio, kurtosis, autocorrelation) are the genuine signals.

**55 features have <0.05% importance** — candidates for removal in a future exploration iteration. Momentum features (36 features = largest group) contribute only 4.45% total — the weakest group by far.

### Category D — Feature Frequency & Lookback Analysis

**15 of 25 feature types lack ANY lookback exceeding 10 days.** On 8h candles, 3 candles = 1 day.

| Feature Type | Max Period (candles) | Max Period (days) | Daily Equivalent Missing |
|-------------|---------------------|-------------------|-------------------------|
| RSI | 30 | 10d | Daily RSI-14 would need period=42 |
| ADX | 21 | 7d | Daily ADX-14 would need period=42 |
| ATR/NATR | 21 | 7d | Daily ATR-14 would need period=42 |
| Stochastic | 21 | 7d | Daily Stoch-14 would need period=42 |
| Supertrend | 14 | 4.7d | Daily Supertrend needs period=21+ |
| MFI | 21 | 7d | Daily MFI-14 would need period=42 |

The model has never seen a proper daily-scale RSI, ADX, or ATR. The feature importance confirms this: long-period features (period 50+) consistently outrank short-period variants of the same indicator. This is the #1 structural gap for a future exploration iteration.

### Category E — Trade Pattern Analysis

**Hour-of-day performance (8h candles):**

| Open Hour (UTC) | Trades | WR | Total PnL | Avg PnL |
|-----------------|--------|----|-----------|---------|
| 07:00 | 187 | 41.2% | +73.5% | +0.39% |
| 15:00 | 171 | 38.0% | +17.7% | +0.10% |
| 23:00 | 216 | 49.5% | +296.7% | +1.37% |

The 23:00 UTC session produces **76% of total PnL** at 49.5% WR. The 15:00 session is nearly breakeven. This is a strong candidate for a future time-of-day filter.

**Year-over-year degradation:**

| Year | Avg PnL/Trade | WR |
|------|--------------|-----|
| 2022 | +1.26% | 46.8% |
| 2023 | +0.52% | 46.4% |
| 2024 | +0.23% | 38.5% |
| 2025 | +0.31% | 38.0% |

The model's edge has compressed ~5x from 2022 to 2024. The 2022 bear market (high volatility, strong trends) was the golden period. The model learned directional patterns that weaken in lower-volatility regimes.

**Direction split:** Shorts outperform longs (PF 1.36 vs 1.26). ETH accounts for 79% of total PnL despite 55% of trades.

### Category F — Statistical Rigor

| Metric | Value | 95% CI |
|--------|-------|--------|
| WR | 43.4% | [39.4%, 47.4%] |
| Sharpe | 1.60 | [0.53, 2.61] |
| Profit Factor | 1.31 | [1.10, 1.56] |
| P(WR > break-even) | >99.99% | — |
| P(negative total PnL) | 0.11% | — |

**The IS edge is statistically real** (p < 0.000002 for WR vs 34.2% break-even). However:
- Minimum detectable WR improvement: ~4 percentage points at 574 trades
- Trades are NOT independent (runs test p = 0.011), so true uncertainty is slightly wider
- 8 consecutive NO-MERGE is statistically expected — improvements below ~4pp WR or ~1.0 Sharpe are undetectable at this sample size

**Implication:** Incremental parameter tuning is futile. Only structural changes large enough to move WR by 4+ pp or Sharpe by 1+ unit will be measurably different from baseline noise.

---

## Section 3: Proposed Change

### Remove `is_unbalance=True` from LightGBM parameters

**What changes:**
- In `optimization.py`: remove `"is_unbalance": True` from `lgb_params`
- Everything else stays identical: same features, same labels, same sample weights, same symbols, same TP/SL/timeout

**What stays:**
- Sample weights from labeling (PnL-magnitude scaled [1, 10]) remain active
- All other LightGBM hyperparameters unchanged
- Same walk-forward, Optuna, CV setup

**Hypothesis:** Removing the redundant class-balancing mechanism will produce a cleaner loss landscape. The model will rely solely on PnL-magnitude sample weights, which encode economic significance rather than just class frequency. This should improve OOS generalization — the opposite direction of iter 055 (which added MORE class balancing and degraded OOS by -0.63 Sharpe).

**Risk:** If the training data has severe class imbalance (e.g., 30/70 split in some months), removing is_unbalance could cause the model to ignore the minority class. However, the label analysis shows long/short split is 46/54% — close to balanced — so this risk is low.

**Success criteria:**
- Seed validation: mean OOS Sharpe > 0, at least 4/5 seeds profitable
- Primary: OOS Sharpe > +1.16 (baseline)
- Constraints: OOS MaxDD ≤ 91.1%, OOS trades ≥ 50, OOS PF > 1.0

---

## Section 4: Configuration

```
Symbols:          BTCUSDT, ETHUSDT
Interval:         8h
Training window:  24 months
TP / SL:          8% / 4%
Timeout:          7 days (10,080 minutes)
Fee:              0.1%
Optuna trials:    50
CV folds:         5
Confidence range: 0.50–0.85
Seed:             42 (first run), then 123, 456, 789, 1001 if first seed passes
is_unbalance:     False  ← THE CHANGE
```

---

## Section 5: Next Steps for QE

1. Modify `optimization.py` to remove `is_unbalance=True` (or set to False)
2. Run full walk-forward backtest with seed=42
3. If year-1 checkpoint fails → EARLY STOP
4. If seed=42 OOS is profitable → run 4 more seeds
5. Generate IS/OOS reports and comparison.csv
6. Write engineering report
