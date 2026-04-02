# Iteration 122 — Research Brief

**Type**: EXPLORATION (novel entropy features for meme model)
**Date**: 2026-04-02
**OOS cutoff**: 2025-03-24 (fixed, never changes)

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24
```

## Objective

Add 3 entropy features to the meme model (DOGE+SHIB). These capture market "randomness" — a signal dimension not represented by any existing feature. Replace 3 weakest existing features to keep net count at 45.

## Rationale: Why Entropy?

**Existing features capture magnitude, not predictability.** Volatility (NATR, BB bandwidth, Garman-Klass) measures how big price moves are. Momentum (RSI, ROC) measures their direction. But neither measures whether the market is *patterned* or *random*.

**Example**: A trending market with large moves has HIGH volatility but LOW entropy (predictable direction). A choppy market with random large moves has HIGH volatility AND HIGH entropy. The model should trade the first but avoid the second. Entropy discriminates between these regimes.

**AFML Ch. 18 connection**: Lopez de Prado recommends entropy-based features as market microstructure indicators. Shannon entropy of discretized returns is the simplest and most interpretable variant.

## New Features

| Feature | Description | Window | Economic rationale |
|---------|-------------|--------|-------------------|
| `ent_shannon_20` | Shannon entropy of 20-candle discretized returns | 20 (~7 days) | Short-term regime: low entropy = trending, tradeable |
| `ent_shannon_50` | Shannon entropy of 50-candle discretized returns | 50 (~17 days) | Medium-term regime stability |
| `ent_approx_50` | Approximate entropy (pattern regularity) | 50 | Low ApEn = repeating patterns exploitable by model |

## Features Removed (to keep net count at 45)

Based on iter 117 importance analysis, remove the 3 lowest-importance features from the meme model:

| Removed | Reason |
|---------|--------|
| `stat_skew_10` | Lowest statistical feature importance. Captured by skew_20 (higher importance) |
| `stat_autocorr_lag1` | Low importance, correlated with other statistical features |
| `meme_indecision` | Doji detection — low signal, high noise for meme coins |

**Net feature count**: 45 → 45 (no change)
**Samples-per-feature ratio**: 4,400 / 45 = 97.8 (unchanged, healthy)

## Architecture (unchanged except feature list)

- **Model A (BTC+ETH)**: Unchanged — 185 auto-discovered features (entropy features now in parquet but not used since auto-discovery will include them automatically)
- **Model B (DOGE+SHIB)**: 45 features — replace 3 weakest with 3 entropy features

**Note**: Model A uses auto-discovery (`feature_columns=None`), so the 3 new entropy features will be automatically discovered and added. This means Model A now has 188 features (185 + 3 entropy). This is an acceptable increase since the BTC/ETH model's samples-per-feature ratio stays above 50.

## Single Variable Changed

| Parameter | Iter 119 | Iter 122 |
|-----------|----------|----------|
| Meme features | 45 (iter 117 set) | **45 (swap 3 → entropy)** |
| BTC/ETH features | 185 (auto-discovery) | **~188 (auto + entropy)** |

## Research Checklist

- **A** (features): Entropy features as novel signal dimension, replacing lowest-importance features
- **D** (feature frequency): Window sizes 20 and 50 chosen to match existing statistical feature lookbacks
