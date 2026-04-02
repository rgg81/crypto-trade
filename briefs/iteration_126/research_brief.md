# Iteration 126 — Research Brief

**Type**: EXPLORATION (Model C: LINK standalone screening)
**Date**: 2026-04-03
**OOS cutoff**: 2025-03-24 (fixed, never changes)

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24
```

## Objective

Screen LINK as a standalone model with ATR labeling. LINK is fundamentally different from L1 alts (oracle infrastructure, DeFi dependency) — potentially uncorrelated signal. Iter 125 proved pooling correlated L1 alts (SOL+AVAX) causes catastrophic overfitting; LINK offers a genuinely different market dynamic.

## Why LINK?

- **5678 IS candles** (Jan 2020 start) — more data than SOL (4941)
- **$26.2M daily volume** — passes Gate 2
- **No gaps >1 candle** — perfect data quality
- **Different dynamics**: Oracle/DeFi infrastructure, not an L1 smart contract platform. Driven by DeFi TVL, oracle integration announcements, cross-chain adoption — different drivers than SOL/AVAX.

## Architecture (same as iter 124 SOL)

- **Symbol**: LINKUSDT only (1 symbol)
- **Labeling**: ATR-based 3.5x/1.75x (proven for high-vol alts)
- **Features**: Auto-discovery (~185 features)
- **Training**: 24 months, 5 CV folds, 50 Optuna trials
- **Ensemble**: 5 seeds
- **Cooldown**: 2 candles

## Learnings Applied

- Iter 123: Static barriers fail for high-vol alts → use ATR labeling
- Iter 124: SOL standalone with ATR has marginal IS signal (+0.16)
- Iter 125: Pooling correlated symbols causes catastrophic overfitting → test standalone first
- 185 features with 1 symbol (ratio ~12) is low but colsample_bytree provides implicit pruning

## Research Checklist

- **B** (symbols): LINK standalone Gate 1-3 screening
