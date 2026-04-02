# Iteration 108 Research Brief

**Type**: EXPLORATION
**Date**: 2026-04-01
**Theme**: Meme coin dedicated model (DOGE + SHIB) with curated features

## Section 0: Data Split

- OOS cutoff: `2025-03-24` (fixed, never changes)
- IS period: all data before 2025-03-24
- OOS period: all data from 2025-03-24 onward
- Walk-forward runs on ALL data; reports split at cutoff

## Strategic Context

After 14 consecutive NO-MERGE iterations on BTC+ETH, the user has directed a pivot to **meme coin diversification**. The goal is NOT to beat the BTC+ETH baseline — it's to build a **separate profitable meme coin model** that can later be combined with BTC+ETH for portfolio diversification.

This is a standalone meme coin exploration. BTC and ETH are excluded from this iteration entirely.

## Data Availability

| Symbol | IS Candles | Start Date | Daily Volume | NATR | Gate 1 | Gate 2 |
|--------|-----------|------------|-------------|------|--------|--------|
| DOGEUSDT | 5,153 | 2020-07-10 | $970M | 5.02% | PASS | PASS |
| 1000SHIBUSDT | 4,240 | 2021-05-10 | $509M | 5.03% | PASS | PASS |

Correlation: DOGE-SHIB 0.64 (moderate), DOGE-BTC 0.66, SHIB-BTC 0.54.

## Two Key Changes

### 1. Dynamic ATR Labeling

Fixed 8%/4% barriers are too tight for meme coins (DOGE hits TP on 81% of candles within 7 days). Dynamic ATR labeling scales barriers per candle using NATR:
- DOGE avg: TP=14.6%, SL=7.3% (2.9x and 1.45x NATR)
- SHIB avg: TP=14.6%, SL=7.3% (similar NATR)

Labels now match execution barriers. Already implemented in `lgbm.py`.

### 2. Curated 42-Feature Set for Meme Coins

Discard all 189 features. Select 42 scale-invariant features focused on meme coin dynamics:
- Volume-driven (pumps, taker flow, liquidity shifts)
- Mean reversion (meme coins snap back after spikes)
- Short-term momentum (fast RSI, 3-5 period ROC)
- Volatility regime (when to trade vs when to sit out)

**Ratio**: 4,400 samples / 42 features = 104.8 (healthy, above 50 minimum)

### Feature Selection

| Category | Count | Rationale |
|----------|-------|-----------|
| Volume & Microstructure | 12 | Meme coins are volume-driven. Taker buy ratio, CMF, MFI detect institutional vs retail flow |
| Volatility Regime | 8 | NATR, BB width, Garman-Klass, range spikes identify volatility expansion/contraction |
| Mean Reversion | 8 | Z-scores, %B, distance from highs/lows. Meme coins mean-revert strongly after spikes |
| Momentum | 8 | Short RSI, fast ROC, Stochastic. Detect pumps early, time entries |
| Statistical | 4 | Returns (1,3,5), autocorrelation. Basic price dynamics |
| Trend | 2 | ADX (trend strength only), PSAR direction |
| **Total** | **42** | |

#### Full Feature List

**Volume (12)**: `vol_taker_buy_ratio`, `vol_taker_buy_ratio_sma_5`, `vol_taker_buy_ratio_sma_10`, `vol_volume_pctchg_3`, `vol_volume_pctchg_5`, `vol_volume_pctchg_10`, `vol_volume_rel_5`, `vol_volume_rel_10`, `vol_cmf_10`, `vol_cmf_14`, `vol_mfi_7`, `vol_mfi_14`

**Volatility (8)**: `vol_natr_7`, `vol_natr_14`, `vol_natr_21`, `vol_bb_bandwidth_10`, `vol_bb_bandwidth_20`, `vol_garman_klass_10`, `vol_range_spike_12`, `vol_range_spike_24`

**Mean Reversion (8)**: `mr_zscore_10`, `mr_zscore_20`, `mr_zscore_50`, `mr_bb_pctb_10`, `mr_bb_pctb_20`, `mr_pct_from_high_5`, `mr_pct_from_high_20`, `mr_pct_from_low_20`

**Momentum (8)**: `mom_rsi_5`, `mom_rsi_14`, `mom_roc_3`, `mom_roc_5`, `mom_roc_10`, `mom_stoch_k_5`, `mom_stoch_d_5`, `stat_return_1`

**Statistical (4)**: `stat_return_3`, `stat_return_5`, `stat_autocorr_lag1`, `stat_skew_10`

**Trend (2)**: `trend_adx_14`, `trend_psar_dir`

### What Was Dropped (and Why)

- **All raw price features** (SMA, EMA, VWAP, ATR, OBV, A/D): Not scale-invariant. DOGE at $0.17 and SHIB at $0.000024 would create split-point issues.
- **All EMA/SMA cross features**: Binary crosses are scale-invariant but too trend-focused for meme dynamics.
- **Aroon, Williams %R, Supertrend**: Redundant with ADX, RSI, PSAR.
- **Long-period features** (RSI_30, MACD, ROC_30): Meme coins trade on shorter timeframes.
- **Kurtosis**: Marginal signal, redundant with skew.
- **Parkinson volatility**: Redundant with NATR and Garman-Klass.
- **Multiple BB %B variants**: Kept 10 and 20 period, dropped 15 and 30.

## Research Analysis (Categories A, B, C, F)

### Category A: Feature Pruning

Reduced from 189 to 42 features (78% reduction). All selected features are scale-invariant. Selection based on:
1. Economic relevance to meme coin dynamics
2. Correlation dedup (no feature pair with |corr| > 0.90 retained)
3. Priority on volume/microstructure (meme coins are volume-driven, not trend-driven)

### Category B: Symbol Universe

DOGE + SHIB selected as the meme coin pool:
- Both pass Gate 1 (data quality) and Gate 2 (liquidity)
- DOGE-SHIB correlation 0.64 (moderate — genuine diversification within the meme sector)
- Both have NATR ~5% (same volatility regime — good for pooled model)
- Gates 3-5 will be evaluated from backtest results

### Category C: Labeling

Dynamic ATR labeling with 2.9x/1.45x multipliers. Expected TP hit rate ~50-60% (down from 81% with fixed barriers), creating meaningful labels.

### Category F: Statistical Significance

42 features with 4,400 samples gives ratio 104.8 (well above 50 minimum). With 2 symbols at similar NATR, the pooled model should learn shared meme patterns without dilution.

## Implementation Spec

### Runner Configuration
```python
SYMBOLS = ("DOGEUSDT", "1000SHIBUSDT")
strategy = LightGbmStrategy(
    training_months=24,
    n_trials=50,
    cv_splits=5,
    label_tp_pct=8.0,
    label_sl_pct=4.0,
    label_timeout_minutes=10080,
    fee_pct=0.1,
    atr_tp_multiplier=2.9,
    atr_sl_multiplier=1.45,
    use_atr_labeling=True,
    ensemble_seeds=[42, 123, 456, 789, 1001],
    feature_columns=[...42 features...],
)
```

### CV Gap
- timeout_candles = 10080/480 = 21
- gap = (21+1) × 2 = 44 rows (same as BTC+ETH baseline)

### Evaluation Criteria (NOT baseline comparison)

This is a standalone meme model. Success criteria:
1. IS Sharpe > 0.0 (any profitability)
2. IS WR > 33.3% (above break-even for 2:1 RR)
3. At least 100 IS trades
4. OOS Sharpe > 0.0 (generalizes)

If these pass, this model becomes the MEME BASELINE for future meme iterations.
