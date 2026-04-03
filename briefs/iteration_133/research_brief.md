# Iteration 133 — Research Brief

**Type**: EXPLORATION (Model D/E candidate screening: DOT standalone)
**Date**: 2026-04-03
**OOS cutoff**: 2025-03-24 (fixed, never changes)

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24
```

## Objective

Screen DOT (Polkadot) as a potential Model D/E candidate. After BNB passed screening in iter 132 (IS +0.51, OOS +1.04), continue screening to maximize the pool of qualified symbols before portfolio combination.

DOT has unique characteristics:
- **Interoperability-focused L1** — different use case from BTC (store of value), ETH (smart contracts), LINK (oracle), BNB (exchange)
- **Parachain auction cycles** — create predictable demand/supply patterns around slot lease events
- **Staking dynamics** — ~50% of DOT is staked, creating supply constraints during auctions

Using the proven iter 126 config template (ATR 3.5x/1.75x, 185 auto-discovery).

## Architecture

Single model, iter 126 config template:
- **Symbol**: DOTUSDT (standalone)
- **Labeling**: ATR-based — TP=3.5xNATR, SL=1.75xNATR, timeout=7 days
- **Features**: 185 auto-discovery (symbol-scoped)
- **Ensemble**: 5 seeds [42, 123, 456, 789, 1001]
- **Walk-forward**: monthly, 5 CV folds, 50 Optuna trials
- **CV gap**: 22 rows (22 × 1 symbol)
- **Data**: Aug 2020 — Feb 2026, 6051 8h candles

## Research Checklist

- **A** (data quality): DOT has 6051 8h candles (Aug 2020 — Feb 2026). Sufficient.
- **B** (symbols): Fifth candidate screening. DOT chosen for interoperability niche and parachain auction dynamics.
