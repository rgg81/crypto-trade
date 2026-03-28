# Iteration 070 — Research Brief

**Type**: EXPLORATION (feature engineering — first ever in 70 iterations)
**Date**: 2026-03-28
**Previous**: Iteration 068 (MERGE — cooldown=2, OOS Sharpe +1.84)

---

## Section 0: Data Split (Verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

---

## Hypothesis

The model has used the same 106 features for all 70 iterations. Adding new feature types — cross-asset (BTC indicators for ETH) and interaction (products of existing indicators) — may provide the model with new information that improves prediction quality.

## New Features

### Interaction Features (6 new, `interaction.py`)
Products of momentum, volatility, and trend indicators. All scale-invariant.

| Feature | Formula | Rationale |
|---------|---------|-----------|
| `interact_rsi_x_adx` | (RSI-50) × ADX / 100 | Momentum × trend strength |
| `interact_stoch_x_adx` | (Stoch%K-50) × ADX / 100 | Stochastic × trend strength |
| `interact_natr_x_adx` | NATR × ADX | Volatility × trend |
| `interact_rsi_x_natr` | (RSI-50) × NATR / 100 | Momentum × volatility |
| `interact_ret1_x_natr` | Return(1) × NATR | Return × volatility |
| `interact_ret1_x_ret3` | Return(1) × Return(3) | Momentum confirmation |

### Cross-Asset Features (7 new, `cross_asset.py`)
BTC indicators as features for all symbols. BTC leads the crypto market.

| Feature | Source | Rationale |
|---------|--------|-----------|
| `xbtc_return_1` | BTC 1-candle return | Market direction |
| `xbtc_return_3` | BTC 3-candle return | Short-term momentum |
| `xbtc_return_8` | BTC 8-candle return | 1-day trend |
| `xbtc_natr_14` | BTC NATR(14) | Market volatility regime |
| `xbtc_natr_21` | BTC NATR(21) | Longer-term vol regime |
| `xbtc_rsi_14` | BTC RSI(14) | Market overbought/oversold |
| `xbtc_adx_14` | BTC ADX(14) | Market trend strength |

Total: 13 new features → ~119 features (up from 106).

## What stays the same
- Ensemble: 3 seeds [42, 123, 789]
- Training: 24 months, 50 trials, 5 CV
- Labeling: TP=8%, SL=4%, timeout=7d
- Execution: ATR barriers, cooldown=2
- Symbols: BTC+ETH

## One-variable change
Only the feature set changes (106 → ~119 columns).
