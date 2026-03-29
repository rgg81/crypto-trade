# Iteration 078 — Engineering Report

**Status**: EARLY STOP (Year 2022 PnL = -54.2%, WR = 38.2%)
**Runtime**: 1764 seconds (~29 minutes)

## Implementation

Added `per_symbol=True` parameter to `LightGbmStrategy`. When enabled:
- `compute_features()`: discovers features per symbol independently (no cross-symbol intersection)
- `_train_per_symbol()`: trains separate 3-seed ensembles per symbol, each with own Optuna (50 trials, 5 CV folds)
- `_predict_per_symbol()`: routes predictions to symbol-specific models with symbol-specific confidence thresholds
- Backward compatible — `per_symbol=False` (default) preserves original pooled behavior

## Key Finding: Feature Count Mismatch

**Critical issue discovered**: Per-symbol feature discovery yields **185 features** per symbol instead of the baseline's **106 features** (global intersection).

- Baseline: 106 features = intersection across BTCUSDT + ETHUSDT parquet files
- Per-symbol: 185 features = all features in each symbol's parquet file (no intersection needed)
- The 79 extra features are likely symbol-specific or have missing values in the other symbol's file

**Impact**: 185 features with ~2,200 training samples per symbol (feature/sample ratio ~12) vs 106 features with ~4,400 pooled samples (ratio ~41). This 3.4x worse ratio causes overfitting.

## Backtest Results: In-Sample Only (Early Stopped)

| Metric | Iter 078 | Baseline (068) |
|--------|----------|----------------|
| Sharpe | **-0.61** | +1.22 |
| WR | **38.6%** | 43.4% |
| PF | **0.88** | 1.35 |
| MaxDD | **90.4%** | 45.9% |
| Trades | 132 | 373 |

### Per-Symbol Breakdown

| Symbol | Trades | WR | Direction Split |
|--------|--------|-----|-----------------|
| BTCUSDT | 74 | **32.4%** (below break-even) | 38 long / 36 short |
| ETHUSDT | 58 | **46.6%** (above baseline 44.3%) | 34 long / 24 short |

**ETH model improved** (46.6% vs 44.3% baseline). **BTC model collapsed** (32.4% vs 42.4% baseline).

## Trade Execution Verification

Sampled 5 trades from trades.csv:

| Symbol | Dir | Entry | Exit | PnL | Reason | Correct? |
|--------|-----|-------|------|-----|--------|----------|
| ETHUSDT | SHORT | 3714.77 | 3870.83 | -4.20% | SL | Yes (SL = entry × 1.042) |
| BTCUSDT | SHORT | 47186.83 | 43215.87 | +8.42% | TP | Yes (TP ≈ entry × 0.916) |
| BTCUSDT | SHORT | 43080.01 | 42538.72 | +1.26% | timeout | Yes (partial) |
| ETHUSDT | LONG | 3130.02 | 3276.93 | +4.69% | timeout | Yes (partial) |
| BTCUSDT | SHORT | 43207.81 | 40331.39 | +6.66% | TP | Yes (TP ≈ entry × 0.933) |

Trade execution is correct. PnL calculations match expected values for each exit reason.

## Architecture Notes

The per-symbol code works correctly. The failure is a research design issue (feature count), not an engineering bug. To fix in next iteration:
1. Force per-symbol models to use the global 106-feature intersection
2. Or add feature selection within per-symbol Optuna (permutation pruning)
