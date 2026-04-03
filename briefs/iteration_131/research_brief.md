# Iteration 131 — Research Brief

**Type**: EXPLORATION (Model D candidate screening: XRP standalone)
**Date**: 2026-04-03
**OOS cutoff**: 2025-03-24 (fixed, never changes)

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24
```

## Objective

Screen XRP as a potential Model D candidate. ADA failed in iter 130 (IS Sharpe -0.73). XRP has fundamentally different price drivers from the current portfolio (BTC/ETH/LINK):
- **Regulatory catalysts** (Ripple vs SEC lawsuit outcomes)
- **Payment-focused utility** (unlike smart contract platforms)
- **Idiosyncratic volatility spikes** around legal/partnership news
- **Less correlated** with ETH ecosystem projects

Using the proven iter 126 config template (ATR 3.5x/1.75x, 185 auto-discovery).

## Architecture

Single model, iter 126 config template:
- **Symbol**: XRPUSDT (standalone)
- **Labeling**: ATR-based — TP=3.5xNATR, SL=1.75xNATR, timeout=7 days
- **Features**: 185 auto-discovery (symbol-scoped)
- **Ensemble**: 5 seeds [42, 123, 456, 789, 1001]
- **Walk-forward**: monthly, 5 CV folds, 50 Optuna trials
- **CV gap**: 22 rows (22 × 1 symbol)
- **Data**: Jan 2020 — Feb 2026, 6722 8h candles

## Success Criteria (Model D qualification)

1. IS Sharpe > 0
2. OOS Sharpe > 0
3. OOS WR > 33%
4. OOS Trades ≥ 20
5. IS/OOS Sharpe ratio > 0.3

## Research Checklist

- **A** (data quality): XRP has 6722 8h candles (Jan 2020 — Feb 2026). Sufficient.
- **B** (symbols): New symbol screening — XRP has not been tested in any iteration. Payment-focused utility coin with regulatory-driven dynamics, different from smart contract platforms (ETH, LINK).
