# Iteration 124 Diary

**Date**: 2026-04-02
**Type**: EXPLORATION (SOL with ATR labeling — meme-proven architecture)
**Model Track**: SOL standalone (single-model)
**Decision**: **NO-MERGE** — standalone screening iteration, not a portfolio run. SOL marginally passes Gate 3.

## Hypothesis

SOL with ATR labeling (3.5x/1.75x) adapts barriers to SOL's higher volatility, improving on iter 123's near-zero IS Sharpe with static 8%/4% barriers.

## Results — SOL ATR vs SOL Static (iter 123)

| Metric | Iter 123 (static) | Iter 124 (ATR) | Change |
|--------|-------------------|----------------|--------|
| IS Sharpe | +0.055 | **+0.162** | **+194%** |
| IS WR | 40.6% | **42.6%** | +2.0pp |
| IS PF | 1.016 | **1.051** | +3.4% |
| IS Trades | 155 | 141 | -9% |
| IS Net PnL | +9.5% | **+31.2%** | **+228%** |
| IS MaxDD | 71.6% | 124.1% | worse |
| OOS Sharpe | -0.12 | **+0.47** | dramatic improvement |
| OOS WR | 35.4% | **46.9%** | +11.5pp |
| OOS Trades | 48 | 32 | -33% (thinner) |
| OOS Net PnL | -5.2% | **+19.0%** | green vs red |

## Gate 3 Assessment

| Criterion | Threshold | Result | Status |
|-----------|-----------|--------|--------|
| IS Sharpe > 0 | > 0 | +0.162 | **PASS** (weak but real) |
| IS WR > 33.3% | > 33.3% | 42.6% | **PASS** |
| IS Trades ≥ 100 | ≥ 100 | 141 | **PASS** |

**Gate 3: PASS (marginal).** ATR labeling transformed SOL from a noise-level IS Sharpe (+0.055) to a weak but real signal (+0.162). IS Net PnL tripled from +9.5% to +31.2%.

## Key Findings

1. **ATR labeling is the critical enabler for SOL.** Static TP=8%/SL=4% was wrong for SOL's volatility. ATR 3.5x/1.75x scales barriers to ~17.5%/8.75% during typical SOL NATR (~5%), giving the model room to work. This mirrors the meme model discovery.

2. **OOS is suspiciously good.** OOS Sharpe +0.47 with 46.9% WR but only 32 trades. The IS/OOS ratio of 2.92 (OOS 3x better than IS) suggests the OOS period was favorable for SOL, not that the model has exceptional skill. Need more OOS data to validate.

3. **IS MaxDD 124% is concerning.** The IS drawdowns are deep — the model loses big before recovering. This is partly because ATR-scaled SL losses are larger in absolute terms.

4. **Trade count dropped with ATR.** 141 IS trades (down from 155) and only 32 OOS (down from 48). The wider ATR barriers reduce trade resolution, and the model becomes more selective. OOS 32 trades is below the 50 minimum for portfolio inclusion.

## What SOL Needs to Become Model C

1. **More training data** — Pool with AVAX to double samples (ratio 12 → ~24). Still low but better.
2. **Cross-asset features** — Add xbtc_return_1, xbtc_return_5, xbtc_natr_14 (BTC leads SOL).
3. **Feature pruning** — 185 auto-discovered features with ~2,200 annual samples is ratio 12. Need explicit pruning to ~45 features (ratio 49).
4. **Higher confidence threshold** — OOS 32 trades suggests the model should trade MORE, not less. The confidence threshold may be too aggressive.

## Label Leakage Audit

CV gap = 22 (22 × 1 symbol). Correct for single-symbol SOL model.

## lgbm.py Code Review

No code changes. ATR labeling works correctly for SOL — barriers scale with SOL's NATR.

## Gap Quantification

IS WR 42.6%, break-even for ATR-adjusted barriers varies by trade (not fixed 33.3%). Average SL is larger with ATR, so break-even WR is higher. IS PF 1.051 confirms the edge is thin.

## Exploration/Exploitation Tracker

Last 10 iterations: [E, E, X, E, X, X, X, E, E, **E**] (iters 115-124)
Exploration rate: 7/10 = 70%

## Research Checklist

- **B** (symbols): SOL re-screening with ATR labeling — marginal Gate 3 pass
- **C** (labeling): ATR vs static comparison shows ATR is necessary for higher-vol symbols

## Next Iteration Ideas

1. **SOL+AVAX pooled model with ATR labeling** (EXPLORATION, single-model) — Pool 2 L1 alts to double training data. Both have similar dynamics. Use ATR labeling 3.5x/1.75x. This addresses the samples/feature ratio and trade count issues simultaneously.

2. **Screen LINK standalone with ATR labeling** (EXPLORATION, single-model) — LINK has different dynamics (oracle/DeFi infra). If it passes Gate 3, it becomes a candidate for a DeFi infrastructure model.

3. **Regression model for BTC/ETH** (EXPLORATION, single-model) — Fundamentally different approach: predict forward return magnitude instead of direction. Could capture a different signal dimension.

4. **Meme model with cross-asset features for SOL** (EXPLOITATION, single-model) — Generate xbtc_* features for SOL's parquet. BTC leads SOL by ~1 candle. Adding cross-asset features could boost SOL's thin signal.
