# Iteration 125 — Research Brief

**Type**: EXPLORATION (Model C: SOL+AVAX pooled L1 alt model)
**Date**: 2026-04-02
**OOS cutoff**: 2025-03-24 (fixed, never changes)

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24
```

## Objective

Build a pooled SOL+AVAX model (Model C candidate) with ATR labeling. Pooling doubles training data vs SOL-only (iter 124's biggest weakness: samples/feature ratio 12).

## Why SOL+AVAX?

| Property | SOL | AVAX | Compatibility |
|----------|-----|------|---------------|
| IS candles | 4941 | 4929 | Similar (both Sep 2020 start) |
| Daily volume | $23.4M | $12.8M | Both pass Gate 2 |
| Max gap | 3.3d | 0.3d | AVAX better |
| NATR range | ~5-8% | ~5-10% | Similar volatility (within 2x) |
| Category | L1 smart contract | L1 smart contract | Same sector |

Pooling rationale: SOL and AVAX are both L1 smart contract platforms with similar volatility profiles. Pooling doubles training samples from ~2,200/yr to ~4,400/yr, improving the samples/feature ratio from 12 to ~24 (with 185 features via auto-discovery).

## Architecture

- **Symbols**: SOLUSDT + AVAXUSDT (pooled)
- **Labeling**: ATR-based 3.5x/1.75x NATR (proven for high-vol symbols in iter 118/124)
- **Features**: Auto-discovery (~185 features)
- **Training**: 24 months, 5 CV folds, 50 Optuna trials
- **Ensemble**: 5 seeds [42, 123, 456, 789, 1001]
- **Cooldown**: 2 candles
- **CV gap**: 44 rows (22 candles × 2 symbols)

## Expected Improvement over Iter 124

- Double training samples → better generalization
- 2 symbols → more trades (IS 141 → ~280, OOS 32 → ~64)
- Diversification within model: if SOL and AVAX have different profitable regimes, pooling captures both

## Risk

- If SOL and AVAX are too correlated, pooling adds no information — just double-counts the same signal
- AVAX may dilute SOL's signal if AVAX is unprofitable standalone
- 185 features with ~4,400 samples is still ratio 24 (below 50 target)

## Research Checklist

- **B** (symbols): SOL+AVAX pooled screening, AVAX Gate 1-2 verified
- **C** (labeling): ATR labeling 3.5x/1.75x proven for high-vol symbols
