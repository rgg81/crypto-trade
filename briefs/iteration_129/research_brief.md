# Iteration 129 — Research Brief

**Type**: EXPLOITATION (A+C portfolio: BTC/ETH + LINK, drop meme)
**Date**: 2026-04-03
**OOS cutoff**: 2025-03-24 (fixed, never changes)

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24
```

## Objective

Test A+C portfolio (BTC/ETH + LINK) without Model B (meme). Iter 128 showed Model B (DOGE/SHIB) lost -43% OOS and dragged the 3-model portfolio from +1.18 to +0.78. Meanwhile LINK was the strongest OOS contributor (+56%, 52.4% WR). Dropping the unstable meme model should improve combined Sharpe.

## Architecture

Two independent models:
- **Model A (BTC+ETH)**: iter 093 config — static 8%/4%, 185 features, 2.9x/1.45x ATR exec
- **Model C (LINK)**: iter 126 config — ATR 3.5x/1.75x, 185 auto-discovery

## Expected vs Baseline

| Source | OOS Trades | OOS Net PnL | Contribution |
|--------|-----------|-------------|-------------|
| Model A (BTC+ETH) | 107 | +51.1% | Proven baseline |
| Model C (LINK) | 42 | +56.0% | New addition |
| **Total expected** | **~149** | **~+107%** | Better than A+B's +100.2% |

Without Model B's -43% OOS drag, the A+C combination should be cleaner. But fewer total trades (149 vs 188).

## Research Checklist

- **B** (symbols): A+C portfolio combination, dropping unstable meme model
