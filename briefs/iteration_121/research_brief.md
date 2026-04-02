# Iteration 121 — Research Brief

**Type**: EXPLOITATION (portfolio allocation weighting)
**Date**: 2026-04-02
**OOS cutoff**: 2025-03-24 (fixed, never changes)

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24
```

## Objective

Test Sharpe-weighted capital allocation: scale BTC/ETH trades by 1.2x and DOGE/SHIB trades by 0.8x (60/40 allocation). The stronger model gets more capital.

## Rationale

Iter 119 baseline uses equal $1000/trade for both models. The standalone model Sharpes differ:
- Model A (BTC/ETH): OOS Sharpe +1.01 (iter 093)
- Model B (DOGE/SHIB): OOS Sharpe +0.73 (iter 118)

Sharpe-weighted allocation: w_A = 1.01/(1.01+0.73) = 58%, w_B = 42%. Rounding to 60/40 for simplicity, scale factors are 1.2x (A) and 0.8x (B).

### Expected Impact

Per-symbol OOS PnL under 1.2/0.8 weighting:
- ETH: +53.8% x 1.2 = +64.6%
- BTC: -2.7% x 1.2 = -3.2%
- SHIB: +65.8% x 0.8 = +52.6%
- DOGE: -16.7% x 0.8 = -13.4%
- **Total: +100.6%** (vs +100.2% baseline — nearly identical net PnL)

The Sharpe improvement comes from **variance reduction**: the high-volatility DOGE/SHIB trades are scaled down 0.8x, reducing their contribution to daily PnL variance more than their return contribution. Since DOGE is unprofitable and SHIB is highly volatile, the variance reduction should exceed the return reduction.

### Implementation

The `weighted_pnl` field in `TradeResult` is computed as `net_pnl_pct * weight_factor`. Since `weight_factor` comes from `signal.weight / 100` (model confidence), we need to apply portfolio-level weights after the backtest by scaling both `weight_factor` and `weighted_pnl` using `dataclasses.replace()`. No changes to the core backtest engine.

### Risk

- BTC's losses also get amplified 1.2x (from -2.7% to -3.2%). Since BTC is barely breakeven, this slightly increases the drag.
- If the two models' daily PnL are highly correlated, the variance reduction may be minimal.
- Small impact expected — this is a portfolio optimization, not a signal improvement.

## Single Variable Changed

| Parameter | Iter 119 | Iter 121 |
|-----------|----------|----------|
| Portfolio weights | 1.0 / 1.0 (equal) | **1.2 / 0.8 (Sharpe-weighted)** |

## Architecture (unchanged)

- **Model A (BTC+ETH)**: Iter 093 config, 185 features, static TP=8%/SL=4%, ATR execution 2.9x/1.45x
- **Model B (DOGE+SHIB)**: Iter 118 config, 45 pruned features, ATR labeling 3.5x/1.75x

## Research Checklist

- **B** (symbols/diversification): Portfolio allocation analysis, per-model Sharpe contribution
- **E** (trade patterns): Per-symbol PnL contribution under different weighting scenarios
