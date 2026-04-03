# Iteration 132 — Research Brief

**Type**: EXPLORATION (Model D candidate screening: BNB standalone)
**Date**: 2026-04-03
**OOS cutoff**: 2025-03-24 (fixed, never changes)

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24
```

## Objective

Screen BNB as a potential Model D candidate. ADA (iter 130) and XRP (iter 131) both failed. BNB has unique characteristics:
- **Exchange-native token** — structural demand from Binance fee discounts, launchpad participation
- **Burn mechanism** — quarterly BNB burns create predictable supply shocks
- **Less correlated** with general alt market due to exchange-specific catalysts
- **High liquidity** — consistently top-5 by trading volume

Using the proven iter 126 config template (ATR 3.5x/1.75x, 185 auto-discovery).

## Architecture

Single model, iter 126 config template:
- **Symbol**: BNBUSDT (standalone)
- **Labeling**: ATR-based — TP=3.5xNATR, SL=1.75xNATR, timeout=7 days
- **Features**: 185 auto-discovery (symbol-scoped)
- **Ensemble**: 5 seeds [42, 123, 456, 789, 1001]
- **Walk-forward**: monthly, 5 CV folds, 50 Optuna trials
- **CV gap**: 22 rows (22 × 1 symbol)
- **Data**: Feb 2020 — Feb 2026, 6632 8h candles

## Success Criteria (Model D qualification)

1. IS Sharpe > 0
2. OOS Sharpe > 0
3. OOS WR > 33%
4. OOS Trades ≥ 20
5. IS/OOS Sharpe ratio > 0.3

## Research Checklist

- **A** (data quality): BNB has 6632 8h candles (Feb 2020 — Feb 2026). Sufficient.
- **B** (symbols): Third candidate screening after ADA and XRP failures. BNB chosen for exchange-native structural demand drivers.
