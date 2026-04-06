# Iteration 162 Diary

**Date**: 2026-04-06
**Type**: EXPLORATION (new feature generation — entropy + CUSUM)
**Decision**: **MERGE** (infrastructure — feature pipeline extension)

## Summary

Implemented entropy (AFML Ch. 18) and CUSUM structural break (AFML Ch.
17) features as a new feature group `entropy_cusum`. 11 new features,
registered in `GROUP_REGISTRY`, 6 unit tests passing, ruff clean.

## Features Added

**Entropy (4)**: Rolling Shannon entropy of discretized returns (windows
10, 20, 50) and volume changes (window 20). Quantifies market
predictability — low = patterned (exploitable), high = random (avoid).

**CUSUM (7)**: Candles since last structural break at 1σ/2σ/3σ adaptive
thresholds, normalized versions, and binary "break within 5 candles"
flag. Detects regime changes.

All scale-invariant. No lookahead. Orthogonal to existing features.

## Tests

6 new tests in `TestEntropyCusum`:
- Column count and prefix verification
- Shannon entropy bounded [0, 3.0]
- CUSUM candles-since non-negative
- Binary break column is {0, 1}
- Volume entropy present
- No rows lost

All pass. Ruff clean. No regressions in existing test suite.

## Merge Rationale

Infrastructure iteration: adds feature computation to the pipeline
without changing the strategy or retraining any model. BASELINE.md
stays at v0.152. The features exist in code but aren't in any parquet
yet — regeneration is a separate step.

## Research Checklist

- **A (Feature Contribution)**: A4 — 11 new features with AFML Ch. 17-18
  economic rationale. Genuinely novel (never tested in 162 iterations).
- **D (Feature Frequency)**: Multiple timescales (10/20/50 candle
  windows for entropy; 1σ/2σ/3σ for CUSUM).

## Exploration/Exploitation Tracker

Last 10 iterations: [X, E, E, E, X, X, X, X, X, **E**] (iters 153-162)
Exploration rate: 4/10 = 40% ✓

## Next Iteration Ideas

### 1. Regenerate feature parquets with entropy_cusum (MANDATORY before retrain)

```bash
uv run crypto-trade features \
  --symbols BTCUSDT,ETHUSDT,LINKUSDT,BNBUSDT \
  --interval 8h \
  --groups all \
  --format parquet \
  --workers 4
```

This produces updated `*_8h_features.parquet` files with the 11 new
columns. Fast (~minutes, not hours).

### 2. Retrain primary model with entropy_cusum features (STRUCTURAL)

Full walk-forward retrain of the A+C+D model portfolio with the new
features included. This is the iteration that could beat v0.152 —
genuinely new information (entropy + CUSUM) added to the model's input.

Expected runtime: ~5 hours for full walk-forward with 5-seed ensemble.

### 3. Paper trading deployment of v0.152 (concurrent)

Deploy v0.152 to paper trading while structural research continues.
