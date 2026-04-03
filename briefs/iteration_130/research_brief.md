# Iteration 130 — Research Brief

**Type**: EXPLORATION (Model D candidate screening: ADA standalone)
**Date**: 2026-04-03
**OOS cutoff**: 2025-03-24 (fixed, never changes)

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24
```

## Objective

Screen ADA (Cardano) as a potential Model D candidate for portfolio expansion. Using the proven iter 126 config template (ATR labeling, 185 auto-discovery features) which produced Model C (LINK, OOS Sharpe +1.20).

ADA is chosen because:
- **Longest data history** among candidates (Jan 2020, 6662 8h candles)
- **Different ecosystem** (Cardano) — less correlated with ETH-based smart contract platforms (ETH, LINK)
- **High volume** — consistently top-15 by trading volume
- **Different price dynamics** — ADA has unique catalysts (Cardano upgrades, staking dynamics)

This is a single-model standalone run — no portfolio combination.

## Architecture

Single model, identical to iter 126 (LINK discovery) config:
- **Symbol**: ADAUSDT (standalone)
- **Labeling**: ATR-based — TP=3.5xNATR, SL=1.75xNATR, timeout=7 days
- **Features**: 185 auto-discovery (symbol-scoped)
- **Ensemble**: 5 seeds [42, 123, 456, 789, 1001]
- **Walk-forward**: monthly, 5 CV folds, 50 Optuna trials
- **CV gap**: 22 rows (22 × 1 symbol)
- **Cooldown**: 2 candles

## Success Criteria (Model D qualification)

For ADA to qualify as Model D:
1. IS Sharpe > 0 (not negative)
2. OOS Sharpe > 0 (profitable OOS)
3. OOS WR > 33% (above break-even for 2:1 RR)
4. OOS Trades ≥ 20
5. IS/OOS Sharpe ratio > 0.3 (relaxed for screening)

If ADA passes, it goes to portfolio combination testing in a future iteration.

## Research Checklist

- **A** (data quality): ADA has 6662 8h candles (Jan 2020 — Feb 2026). Sufficient for 24-month training + 12-month OOS.
- **B** (symbols): New symbol screening — ADA has not been tested before in any iteration.
