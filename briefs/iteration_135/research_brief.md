# Iteration 135 — Research Brief

**Type**: EXPLORATION (Model E candidate screening: SOL standalone)
**Date**: 2026-04-04
**OOS cutoff**: 2025-03-24 (fixed, never changes)

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24
```

## Objective

Screen SOL as a potential Model E candidate. SOL is the highest-volume alt not yet tested with the iter 126 config template (ATR 3.5x/1.75x, 185 auto-discovery). Previous SOL attempts (iter 123-124) used different configs and failed. The current template has proven successful for LINK (iter 126) and BNB (iter 132).

SOL characteristics:
- **Highest volume L1 alt** after ETH — massive liquidity
- **High volatility** — NATR typically 2-3x BTC's
- **Different ecosystem** (Solana) from all current portfolio symbols
- **Data since Sep 2020**, 5967 8h candles

## Architecture

Single model, iter 126 config template:
- **Symbol**: SOLUSDT (standalone)
- **Labeling**: ATR-based — TP=3.5xNATR, SL=1.75xNATR, timeout=7 days
- **Features**: 185 auto-discovery (symbol-scoped)
- **Ensemble**: 5 seeds [42, 123, 456, 789, 1001]
- **Walk-forward**: monthly, 5 CV folds, 50 Optuna trials
- **CV gap**: 22 rows (22 x 1 symbol)

## Research Checklist

- **A** (data quality): SOL has 5967 8h candles (Sep 2020 — Feb 2026). Sufficient.
- **B** (symbols): SOL screening with proven config template. Previous attempts used different configs.
