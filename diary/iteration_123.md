# Iteration 123 Diary

**Date**: 2026-04-02
**Type**: EXPLORATION (new Model C: SOL standalone screening)
**Model Track**: SOL standalone (single-model, per user feedback)
**Decision**: **NO-MERGE** — SOL fails Gate 3 (IS Sharpe +0.055, essentially breakeven)

## Hypothesis

SOL could be a Model C candidate for the portfolio. Screening through the 5-gate protocol with BTC/ETH's baseline config (static TP=8%/SL=4%, 24-month training, 5-seed ensemble, auto-discovered features).

## Gate Results

| Gate | Criterion | Result | Status |
|------|-----------|--------|--------|
| 1 — Data quality | ≥1095 IS candles, no gaps >3d | 4941 candles, max gap 3.3d | **PASS** |
| 2 — Liquidity | Daily volume >$10M | $23.4M | **PASS** |
| 3 — Stand-alone IS profitability | IS Sharpe >0, WR >33.3%, ≥100 trades | Sharpe +0.055, WR 40.6%, 155 trades | **MARGINAL FAIL** |
| 4 — Pooled compatibility | N/A | — | Skipped |
| 5 — Diversification value | N/A | — | Skipped |

## Results

| Metric | IS | OOS | Ratio |
|--------|-----|-----|-------|
| Sharpe | +0.055 | -0.12 | -2.19 |
| WR | 40.6% | 35.4% | 0.87 |
| PF | 1.016 | 0.965 | 0.95 |
| MaxDD | 71.6% | 49.5% | 0.69 |
| Trades | 155 | 48 | 0.31 |
| Net PnL | +9.5% | -5.2% | -0.54 |

## Analysis

### Why SOL Failed Gate 3

1. **IS Sharpe +0.055 is noise, not signal.** Over 30 months of IS predictions, +9.5% total PnL = ~0.3%/month. This is within the range of random trading.

2. **SOL NATR ~5-8% makes static TP=8%/SL=4% suboptimal.** With SOL's higher volatility, 8% TP is reached more often by random walks, but 4% SL is also hit more often. The net effect: the model's directional signal is diluted by volatility noise. SOL may need wider barriers (TP=12%/SL=6% or ATR-based).

3. **185 features with ~2,200 training samples per year = ratio 12.** This is catastrophically low. The BTC/ETH model compensates with colsample_bytree, but SOL alone doesn't have enough data to support 185 features.

4. **OOS confirms: -0.12 Sharpe, only 48 trades.** The model didn't find enough confidence to trade OOS (48 < 50 minimum), and when it did, it lost money.

### What This Tells Us About Model C

SOL with BTC/ETH's exact config doesn't work. But this doesn't mean SOL is untradeable:
- **ATR-based labeling** (like the meme model) could adapt barriers to SOL's higher volatility
- **Feature pruning** to ~45 features would improve the samples/feature ratio from 12 to ~49
- **SOL+AVAX pooled** (2 L1 alts) would double training samples

## Label Leakage Audit

- CV gap = 22 (22 × 1 symbol). Correct for single-symbol model.

## lgbm.py Code Review

No code changes. Single-symbol auto-discovery works correctly.

## Gap Quantification

IS WR 40.6%, break-even 33.3%, gap +7.3pp. Looks decent but IS Sharpe +0.055 means the WR edge barely covers the 2:1 RR asymmetry. OOS WR 35.4% is barely above break-even.

## Exploration/Exploitation Tracker

Last 10 iterations: [E, E, E, X, E, X, X, X, E, **E**] (iters 114-123)
Exploration rate: 7/10 = 70%
This iteration: EXPLORATION (new model track)

## Research Checklist

- **B** (symbols): 5-gate screening for SOL — passed gates 1-2, marginal fail gate 3
- **A** (features): Auto-discovery used 185 features, samples/feature ratio 12 (too low)

## Next Iteration Ideas

Per user feedback: keep searching for new individual models.

1. **SOL with ATR labeling + pruned features** (EXPLORATION, single-model) — Same SOL data but with ATR labeling (3.5x/1.75x like meme model) and explicit ~45 pruned features. This addresses both problems: barriers adapted to SOL's volatility + better samples/feature ratio. Could transform SOL from marginal to profitable.

2. **SOL+AVAX pooled L1 alt model** (EXPLORATION, single-model) — Pool 2 L1 alts to double training data. Both have similar dynamics (high beta to BTC, ecosystem-driven). Screen AVAX through gates 1-2 first.

3. **Screen LINK, XRP, BNB** (EXPLORATION, single-model) — Try other high-volume symbols with the BTC/ETH config. One of them may have stronger standalone signal than SOL.

4. **Regression model for BTC/ETH** (EXPLORATION, single-model) — Instead of classification (long/short), predict forward 1-candle return as a continuous target. This is a fundamentally different approach that could capture a different signal dimension. Test on BTC/ETH first.
