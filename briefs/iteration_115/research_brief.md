# Iteration 115 Research Brief — Unified Portfolio: BTC+ETH + DOGE+SHIB

**Type**: EXPLORATION (portfolio combination — first multi-model portfolio)
**Date**: 2026-04-01

## Section 0: Data Split (verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
IS: all data before 2025-03-24
OOS: all data from 2025-03-24 onward
```

## Objective

Combine the BTC+ETH baseline model (iter 093, OOS Sharpe +1.01) and DOGE+SHIB meme model
(iter 114, OOS Sharpe +0.29) into a unified 4-symbol portfolio. The combined portfolio must
beat the BTC+ETH baseline OOS Sharpe (+1.01) to merit a merge.

**Rationale**: BTC-DOGE correlation is ~0.66. The two models trade different market dynamics
on different symbols. Portfolio-level Sharpe should improve through diversification:
- BTC+ETH: 107 OOS trades, $1000/trade
- DOGE+SHIB: 93 OOS trades, $1000/trade
- Combined: ~200 OOS trades, 4 symbols, better statistical robustness

## Architecture: Two Separate Models

This is NOT a pooled 4-symbol model. It runs two independent LightGBM strategies:

### Model A: BTC+ETH (iter 093 baseline config)
- Symbols: BTCUSDT + ETHUSDT
- Features: 185 (auto-discovery, symbol-scoped)
- Labeling: Fixed TP=8%, SL=4%, timeout=7 days
- Execution: Dynamic ATR (TP=2.9×NATR_21, SL=1.45×NATR_21)
- Training: 24 months, 5 CV folds, 50 Optuna trials
- Ensemble: 5-seed [42, 123, 456, 789, 1001]
- Cooldown: 2 candles

### Model B: DOGE+SHIB (iter 114 meme config)
- Symbols: DOGEUSDT + 1000SHIBUSDT
- Features: 67 (42 base + 12 microstructure + 8 trend + 5 BTC cross-asset)
- Labeling: Dynamic ATR (TP=2.9×NATR_21, SL=1.45×NATR_21)
- Execution: Fixed TP=8%, SL=4%, timeout=7 days
- Training: 24 months, 5 CV folds, 50 Optuna trials
- Ensemble: 5-seed [42, 123, 456, 789, 1001]
- Cooldown: 2 candles

### Portfolio Combination
Run both models independently. Concatenate trade results. Sort by close_time.
Generate unified reports with all 4 symbols. Each model allocates $1000/trade (equal sizing).

## Expected Outcomes

**Optimistic**: Combined OOS Sharpe > 1.01 (diversification benefit outweighs meme model's lower Sharpe)
**Realistic**: Combined OOS Sharpe 0.7-1.0 (meme model dilutes, but more trades + lower MaxDD)
**Pessimistic**: Combined OOS Sharpe < 0.7 (meme model drags down portfolio)

The key question: does adding 93 lower-Sharpe trades improve or dilute the 107 high-Sharpe trades?
Diversification theory says yes if correlation < 1.0. Let's verify empirically.

## No Research Changes

Both models run with their exact original configurations. Zero parameters changed.
This iteration tests the COMBINATION, not the individual models.

## Seed Validation

If the combined portfolio beats baseline: run seed validation (10 seeds on the MEME model
only, since BTC+ETH baseline is already validated). The BTC+ETH model is deterministic
with the same config.

## Merge Criteria

- **Primary**: Combined OOS Sharpe > +1.01 (baseline)
- **Hard constraints**:
  - Combined OOS MaxDD ≤ 46.6% × 1.2 = 55.9%
  - Combined OOS Trades ≥ 50 (will be ~200)
  - Combined OOS PF > 1.0
  - No single symbol > 30% of combined OOS PnL
  - IS/OOS Sharpe ratio > 0.5
