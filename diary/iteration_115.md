# Iteration 115 Diary

**Date**: 2026-04-01
**Type**: EXPLORATION (first multi-model portfolio)
**Merge Decision**: NO-MERGE — Combined OOS Sharpe +0.83 < baseline +1.01, MaxDD 61.8% > 55.9% constraint

**OOS cutoff**: 2025-03-24

## Combined Portfolio Results

| Metric | IS | OOS | Ratio | Baseline OOS |
|--------|-----|-----|-------|-------------|
| Sharpe | +0.51 | **+0.83** | 1.63 | +1.01 |
| WR | 42.2% | **42.5%** | 1.01 | 42.1% |
| PF | 1.11 | **1.15** | 1.04 | 1.25 |
| MaxDD | 118.3% | **61.8%** | 0.52 | 46.6% |
| Trades | 574 | **200** | — | 107 |
| Net PnL | +175.2% | **+69.9%** | 0.40 | +51.1% |

## OOS Per-Symbol

| Symbol | Trades | WR | PnL | % Total |
|--------|--------|----|-----|---------|
| ETHUSDT | 56 | 50.0% | +53.8% | 76.9% |
| DOGEUSDT | 45 | 42.2% | +11.0% | 15.8% |
| 1000SHIBUSDT | 48 | 43.8% | +7.8% | 11.1% |
| BTCUSDT | 51 | 33.3% | -2.7% | -3.9% |

## OOS Monthly PnL

| Month | PnL | Trades |
|-------|-----|--------|
| 2025-03 | +20.5% | 4 |
| 2025-04 | +14.7% | 15 |
| 2025-05 | **-24.0%** | 21 |
| 2025-06 | +15.3% | 13 |
| 2025-07 | **-30.4%** | 22 |
| 2025-08 | +21.7% | 24 |
| 2025-09 | +0.7% | 12 |
| 2025-10 | **-18.9%** | 21 |
| 2025-11 | +30.2% | 14 |
| 2025-12 | **-27.2%** | 23 |
| 2026-01 | **+50.2%** | 26 |
| 2026-02 | +17.2% | 5 |

## Architecture

Two independent LightGBM models running side-by-side:
- **Model A (BTC+ETH)**: iter 093 baseline config, 185 features, auto-discovery
- **Model B (DOGE+SHIB)**: iter 114 meme config, 67 features, ATR labeling

Trades concatenated and sorted by close_time. Equal $1000 allocation per trade.

## Why It Failed

1. **Meme model's high variance dilutes portfolio Sharpe**: DOGE+SHIB standalone has OOS Sharpe +0.29 — far below BTC+ETH's +1.01. Adding 93 low-Sharpe trades to 107 high-Sharpe trades reduces the portfolio Sharpe from +1.01 to +0.83 (-18%).

2. **MaxDD increased**: Meme model's standalone MaxDD is 78.5%. The combined portfolio MaxDD of 61.8% is better than standalone meme but worse than baseline (46.6%). The constraint is 55.9% — we exceed it.

3. **ETH still dominates**: ETH contributes 77% of total OOS PnL. Better than baseline (105%) but still far from the 30% target.

## What We Learned

- **More trades ≠ better Sharpe**: 200 OOS trades vs 107, but risk-adjusted returns are worse.
- **More absolute PnL**: +69.9% vs +51.1% — the portfolio makes 37% more money in absolute terms.
- **Diversification works partially**: ETH concentration dropped from 105% → 77%. Both meme coins are profitable.
- **The meme model needs higher Sharpe before portfolio inclusion**: A sub-model needs Sharpe ≥ ~0.7 to not dilute a Sharpe +1.0 portfolio.
- **Position sizing could help**: Instead of equal $1000/trade, allocating less to meme trades (e.g., $500) would reduce their impact on volatility while keeping the PnL contribution.

## Merge Constraint Check

| Constraint | Required | Actual | Pass? |
|------------|----------|--------|-------|
| OOS Sharpe > baseline | > +1.01 | +0.83 | FAIL |
| MaxDD ≤ baseline × 1.2 | ≤ 55.9% | 61.8% | FAIL |
| Trades ≥ 50 | ≥ 50 | 200 | PASS |
| PF > 1.0 | > 1.0 | 1.15 | PASS |
| Symbol < 30% | < 30% | 77% | FAIL |
| IS/OOS > 0.5 | > 0.5 | 1.63 | PASS |

## Exploration/Exploitation Tracker

Last 10 (iters 106-115): [E, X, E, E, E, E, E, X, E, **E**]
Exploration rate: 9/10 = 90%

## Next Iteration Ideas

1. **Weighted portfolio**: Allocate 70% to BTC+ETH, 30% to DOGE+SHIB (reduce meme impact on volatility). This could be done by scaling `weight_factor` on meme trades to 0.3.

2. **Improve meme model Sharpe**: The meme model needs OOS Sharpe > +0.7 to contribute positively. Ideas:
   - Feature pruning on meme model (67 → 40-50 features)
   - Wider confidence threshold (more selective trading)
   - Shorter timeout for meme coins (more volatile, resolve faster)

3. **Per-symbol position sizing**: Use inverse-volatility weighting — DOGE/SHIB get smaller positions proportional to their higher NATR. This naturally reduces meme MaxDD contribution.

4. **Time-gated combination**: Only run meme model during specific regimes (e.g., when BTC ADX > 25, meaning trending market where meme coins follow BTC).
