# Phase 1: Exploratory Data Analysis — Iteration 001

## Data Scope

- **Total parquet files**: 760 symbols (8h candles)
- **Symbols with IS data** (before 2025-03-24): 517
- **Symbols with zero IS candles**: 243 (listed after OOS cutoff)
- **IS candle count**: median 626, mean 1402, max 5727 (BTCUSDT, from 2020-01-01)

### Data Availability Tiers

| Threshold | Count | Notes |
|-----------|-------|-------|
| >= 1 year (1095 candles) | 330 | Minimum for walk-forward with 12-month training |
| >= 2 years (2190 candles) | 181 | Good for meaningful IS evaluation |
| >= 4 years (4380 candles) | 93 | Full market cycle coverage |
| Active USDT, start before 2023-07 | 184 | Best candidates for walk-forward |

### Volume Distribution (IS period, per-8h-candle quote volume)

- p10: $3.3M, p50: $15M, p90: $89M, p99: $338M
- Top 5: BTCUSDT ($4.3B), ETHUSDT ($2.1B), SOLUSDT ($527M), XRPUSDT ($341M), DOGEUSDT ($322M)

## Return Distributions (8h candles, IS only)

Analyzed 20-symbol sample (top 10 + 10 mid-cap):

| Statistic | Value |
|-----------|-------|
| Mean return | +0.082% per 8h candle |
| Mean std dev | 3.43% |
| Mean skewness | +1.02 (positive, fat right tail) |
| Mean kurtosis | 20.5 (normal=0; extreme fat tails) |
| Mean autocorrelation (lag-1) | +0.035 (very weak) |
| Pct positive returns | 48.2% |

### Pooled Return Percentiles (63K observations)

| Percentile | Return |
|------------|--------|
| p1 | -8.53% |
| p5 | -4.52% |
| p25 | -1.22% |
| p50 | +0.00% |
| p75 | +1.22% |
| p95 | +4.81% |
| p99 | +10.33% |

- Extreme moves (|r| > 5%): 8.6% of candles
- Extreme moves (|r| > 10%): 1.6% of candles
- Heavy tails are a defining characteristic — TP/SL levels should accommodate this.

### Per-Symbol Variation

- BTC/ETH: lower volatility (std 1.9-2.4%), moderate kurtosis (7-10)
- DOGE: extreme kurtosis (104), skew (+5.7), autocorrelation (0.23) — driven by meme cycles
- LUNA: extreme kurtosis (57), negative skew (-4.5), autocorrelation (0.36) — collapse event
- Mid-caps generally: higher volatility (3-5% std), more positive skew

## Regime Identification

Using BTC NATR(14) and ADX(14) medians as regime boundaries:

| Regime | Candles | % | Mean Return | Std |
|--------|---------|---|-------------|-----|
| Trending-volatile | 1641 | 28.7% | +0.095% | 2.56% |
| Mean-reverting-quiet | 1641 | 28.7% | +0.054% | 1.02% |
| Trending-quiet | 1216 | 21.3% | +0.140% | 1.12% |
| Choppy-volatile | 1216 | 21.3% | -0.058% | 2.23% |

### Regime Persistence

| Regime | Mean Run | Median Run | Max Run |
|--------|----------|------------|---------|
| Trending-volatile | 15.3 candles (~5d) | 8 | 97 |
| Mean-reverting-quiet | 11.8 candles (~4d) | 5 | 102 |
| Trending-quiet | 11.2 candles (~4d) | 7 | 59 |
| Choppy-volatile | 9.2 candles (~3d) | 4 | 105 |

**Key insight**: Regimes are persistent (multi-day), which is useful for the model to learn. Choppy-volatile has negative expected return — a "don't trade" signal in this regime could be valuable.

## Cross-Symbol Correlation (IS, top 30 USDT by volume)

| Statistic | Value |
|-----------|-------|
| Mean pairwise correlation | 0.604 |
| Median | 0.626 |
| Min | 0.134 |
| Max | 0.940 (ETH/ETHBUSD duplicate) |
| Pairs > 0.7 | 47 |
| Pairs > 0.5 | 385 of 435 |

### Correlation by Regime

| Regime | Mean Correlation |
|--------|-----------------|
| Trending-volatile | 0.678 |
| Choppy-volatile | 0.687 |
| Trending-quiet | 0.553 |
| Mean-reverting-quiet | 0.578 |

**Key insight**: Correlations rise substantially in volatile regimes (0.68) vs quiet (0.55-0.58). This means diversification benefits are weakest when most needed. A pooled model is justified because symbols share significant common structure.

## Survivorship Bias

| Category | Count |
|----------|-------|
| Total symbols with IS data | 517 |
| Active at OOS cutoff | 446 |
| Delisted (ended >2 months before cutoff) | 71 |
| — BUSD pairs (Binance deprecated) | 54 |
| — SETTLED pairs | 3 |
| — Regular USDT delisted | 26 |

**Recommendation**: Exclude BUSD and SETTLED pairs entirely (they are duplicates of USDT pairs or contract rollovers). Include the 26 delisted USDT symbols in training if they have sufficient history — excluding them would introduce survivorship bias. The walk-forward approach naturally handles this: the model trains on data as it existed at each point in time.

## Forward Return Analysis (labeling prep)

| Horizon | Mean | Std | % Positive | |ret|<0.5% | Autocorr |
|---------|------|-----|------------|------------|----------|
| 1 candle (8h) | +0.061% | 1.87% | 51.4% | 37.7% | 0.035 |
| 2 candles (16h) | +0.123% | 2.68% | 51.8% | 26.9% | 0.525 |
| 3 candles (24h) | +0.185% | 3.32% | 52.4% | 21.8% | 0.662 |
| 5 candles (40h) | +0.306% | 4.22% | 52.9% | 16.4% | 0.810 |

**Key insight**: Single-candle forward returns have 37.7% of observations within ±0.5% — too noisy for classification. Multi-candle horizons improve signal-to-noise. This supports using a triple-barrier approach with TP/SL levels rather than simple directional classification.
