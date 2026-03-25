# Phase 2: Labeling Strategy — Iteration 001

## Approaches Evaluated

### 1. Fixed-Horizon Return (sign of forward N-candle return)

- **1-candle (8h)**: 37.7% of returns within ±0.5%, extremely noisy. Autocorrelation 0.035 — effectively random walk at this horizon.
- **3-candle (24h)**: 21.8% within ±0.5%, better signal-to-noise. But still a poor classifier — forces a label on every candle regardless of market clarity.
- **Problem**: Does not account for the path taken. A candle that goes +5% then retraces to +0.1% gets labeled the same as one that gently drifts +0.1%.

**Verdict**: Rejected. Too noisy, ignores path-dependent reality of trading with stops.

### 2. Triple Barrier Method (TP/SL/timeout)

Existing implementation in `labeling.py` already supports this. Tested on IS data across 10 major symbols:

| TP / SL | Resolution Rate | Clear Long | Clear Short | Ambiguous (both TP) | Timeout |
|---------|-----------------|------------|-------------|---------------------|---------|
| 2% / 1% | 98.7% | 22.5% | 24.6% | 51.6% | 1.3% |
| 3% / 1.5% | 94.0% | 29.0% | 31.2% | 33.9% | 6.0% |
| 4% / 2% | 87.2% | 31.6% | 33.6% | 21.9% | 12.8% |
| 5% / 2.5% | 78.6% | 31.6% | 32.9% | 14.1% | 21.4% |

All tested with 9-candle timeout (3 days on 8h candles).

**Analysis**:
- **TP=2%/SL=1%**: Nearly all candles resolve, but 51.6% hit BOTH TP directions (ambiguous). These get labeled by which TP hit first, which is noisy.
- **TP=4%/SL=2%**: Sweet spot. 87% resolution. Only 22% ambiguous. Good long/short balance (32/34%). 2:1 reward/risk matches the asymmetry we want.
- **TP=5%/SL=2.5%**: Too many timeouts (21.4%), wasting data.

**Key advantage**: Labels are aligned with actual trade outcomes. The model learns to predict "will price move 4% in one direction before moving 2% against" — which is exactly what we trade.

**Verdict**: Selected.

### 3. Trend-Following Labels

Would label based on detected trend continuation. However:
- Trend detection on 8h candles requires significant lookback (50+ candles = 17+ days)
- Creates circular dependency with trend features
- Labels would be heavily concentrated (long in bull markets, short in bear)

**Verdict**: Rejected. Creates feature leakage and severe class imbalance across regimes.

## Decision: Triple Barrier with TP=4%, SL=2%, Timeout=4320 minutes

### Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| TP | 4.0% | Achievable in 3 days on 8h candles (p95 return is 4.8%). Clear enough to filter noise |
| SL | 2.0% | 2:1 reward/risk. SL at ~p30 of return distribution — reasonable stop level |
| Timeout | 4320 min (3 days, 9 candles) | Balances resolution rate (87%) with data retention. Longer timeouts waste data on timeouts that get weak labels anyway |
| Ambiguity resolution | First-to-hit direction | Already implemented in `labeling.py`. When both TP hit, picks whichever was first |
| Timeout resolution | Forward return direction | Already implemented. Timeout labels are noisy but low-weighted |

### Label Distribution (expected across universe)

- ~32% clear long, ~34% clear short, ~22% ambiguous (resolved by first-hit), ~12% timeout
- Near-balanced classes → no severe class imbalance issue
- `is_unbalance=True` in LightGBM handles minor imbalance

### Weight Scheme

Existing implementation: `weight = 1 + (|forward_return| / max_return) * 9`, producing weights in [1, 10].

This is adequate for iteration 001. High-conviction labels (large moves) get 10x the weight of marginal ones.

### Critical Fix Required

The existing default `label_timeout_minutes=120` in `lgbm.py` is **far too short for 8h candles** — 120 minutes is just 2 hours, less than a single candle. Must be changed to 4320 (3 days).
