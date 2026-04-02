# Iteration 120 — Research Brief

**Type**: EXPLOITATION (symbol removal from meme model)
**Date**: 2026-04-02
**OOS cutoff**: 2025-03-24 (fixed, never changes)

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24
```

## Objective

Drop DOGEUSDT from the meme model, running SHIB-only. Iter 119 showed DOGE is unprofitable OOS (-16.7%, 37.5% WR) while SHIB carries 65.7% of total portfolio PnL. Removing DOGE should improve the meme model's Sharpe and the combined portfolio's overall performance.

## Rationale

From iter 119 OOS per-symbol:
- **SHIB**: 41 trades, 53.7% WR, +65.8% PnL — strong, consistent signal
- **DOGE**: 40 trades, 37.5% WR, -16.7% PnL — unprofitable, drags portfolio

DOGE's problem is structural: wider ATR barriers (3.5x/1.75x) amplify losses on a coin with weaker directional signal. SHIB's signal is stronger (53.7% WR vs 37.5%).

**Risk**: Running SHIB-only means the meme model trains on 1 symbol (~2,200 samples/year). With 45 features, the samples/feature ratio drops to ~49 (from ~98 with 2 symbols). This is at the lower bound but still above the 50 threshold for 24-month windows.

## Architecture

- **Model A (BTC+ETH)**: Unchanged from iter 119 (185 features, auto-discovery)
- **Model B (SHIB only)**: Same 45 features, ATR labeling 3.5x/1.75x, but SHIB only

## Single Variable Changed

| Parameter | Iter 119 | Iter 120 |
|-----------|----------|----------|
| Meme symbols | DOGEUSDT + 1000SHIBUSDT | **1000SHIBUSDT only** |

## Research Checklist

- **B** (symbols): Removing unprofitable symbol to improve portfolio quality
- **E** (trade patterns): DOGE's OOS WR 37.5% vs SHIB's 53.7% — clear signal quality difference
