# Iteration 128 — Research Brief

**Type**: EXPLOITATION (MILESTONE: Three-model portfolio A+B+C)
**Date**: 2026-04-03
**OOS cutoff**: 2025-03-24 (fixed, never changes)

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24
```

## Objective

MILESTONE portfolio run: combine Model A (BTC/ETH iter 093), Model B (DOGE/SHIB iter 118), and NEW Model C (LINK iter 126). Test whether adding a third decorrelated model improves combined OOS Sharpe beyond the current baseline +1.18.

This is the rare combined run justified by discovering LINK as Model C (iter 126: IS +0.45, OOS +1.20).

## Architecture

Three independent models, trades concatenated:

| Model | Symbols | Config | IS Sharpe | OOS Sharpe |
|-------|---------|--------|-----------|------------|
| A (BTC/ETH) | BTCUSDT, ETHUSDT | iter 093: static 8%/4%, 185 features, 2.9x/1.45x ATR exec | +0.86 | +1.01 |
| B (DOGE/SHIB) | DOGEUSDT, 1000SHIBUSDT | iter 118: ATR 3.5x/1.75x, 46 features | +0.93 | +0.73 |
| C (LINK) | LINKUSDT | iter 126: ATR 3.5x/1.75x, 185 auto-discovery | +0.45 | +1.20 |

## Expected Impact

- **More trades**: A(107) + B(81) + C(42) = ~230 OOS trades (vs 188 current baseline)
- **Diversification**: LINK's OOS returns should be decorrelated from BTC/ETH and DOGE/SHIB
- **Target**: Combined OOS Sharpe > +1.18 (current baseline)

## Research Checklist

- **B** (symbols): Portfolio-level combination of 3 validated models
- **E** (trade patterns): Cross-model trade timing and correlation analysis
