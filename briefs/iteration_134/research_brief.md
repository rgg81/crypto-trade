# Iteration 134 — Research Brief

**Type**: EXPLOITATION (MILESTONE: A+C+D portfolio — BTC/ETH + LINK + BNB)
**Date**: 2026-04-03
**OOS cutoff**: 2025-03-24 (fixed, never changes)

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24
```

## Objective

MILESTONE portfolio run: combine Model A (BTC/ETH), Model C (LINK), and Model D (BNB). After screening 5 candidates (iters 130-133), LINK and BNB are the only symbols that pass all Model D gates. This tests whether adding BNB to the existing A+C baseline improves the portfolio.

## Architecture

Three independent models, trades concatenated:

| Model | Symbols | Config | IS Sharpe | OOS Sharpe | OOS Trades |
|-------|---------|--------|-----------|------------|------------|
| A (BTC/ETH) | BTCUSDT, ETHUSDT | iter 093: static 8%/4%, 196 features, ATR exec 2.9x/1.45x | +0.44* | +1.68* | 107 |
| C (LINK) | LINKUSDT | iter 126: ATR 3.5x/1.75x, 185 auto-discovery | +0.45 | +1.20 | 42 |
| D (BNB) | BNBUSDT | iter 126 template: ATR 3.5x/1.75x, 185 auto-discovery | +0.51 | +1.04 | 50 |

*Combined A+C IS/OOS from iter 129 baseline

## Expected Impact

- **More trades**: A(107) + C(42) + D(50) = ~199 OOS trades (vs 149 current baseline)
- **Better diversification**: 5 symbols across 4 different crypto niches (store of value, smart contracts, oracle, exchange)
- **Target**: Combined OOS Sharpe ≥ +1.68 (current A+C baseline)

## Research Checklist

- **B** (symbols): Portfolio-level combination of 3 validated models (A+C+D)
- **E** (trade patterns): Cross-model trade timing and diversification impact
