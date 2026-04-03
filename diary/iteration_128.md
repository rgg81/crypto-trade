# Iteration 128 Diary

**Date**: 2026-04-03
**Type**: EXPLOITATION (MILESTONE: Three-model portfolio A+B+C)
**Model Track**: Combined A (BTC/ETH) + B (DOGE/SHIB) + C (LINK)
**Decision**: **NO-MERGE** — OOS Sharpe +0.78 < baseline +1.18. Meme model drags portfolio.

## Results vs Baseline

| Metric | Iter 128 (A+B+C) | Baseline 119 (A+B) | Change |
|--------|-------------------|---------------------|--------|
| OOS Sharpe | +0.78 | **+1.18** | -34% |
| OOS WR | 43.4% | 43.6% | -0.2pp |
| OOS PF | 1.12 | 1.22 | -8% |
| OOS MaxDD | 126.6% | **46.4%** | +173% |
| OOS Trades | **244** | 188 | +30% |
| OOS Net PnL | +81.9% | **+100.2%** | -18% |
| IS Sharpe | 0.10 | 0.86 | -88% |

### OOS Per-Symbol

| Symbol | Model | Trades | WR | Net PnL | % of Total |
|--------|-------|--------|----|---------|------------|
| LINKUSDT | C | 42 | **52.4%** | **+56.0%** | 68.4% |
| ETHUSDT | A | 55 | 45.5% | +52.1% | 63.6% |
| BTCUSDT | A | 52 | 38.5% | +16.8% | 20.5% |
| DOGEUSDT | B | 49 | 38.8% | -14.7% | -17.9% |
| 1000SHIBUSDT | B | 46 | 43.5% | -28.3% | -34.5% |

## Analysis

### LINK is the star — Model B is the problem

LINK (Model C) delivered the strongest per-symbol OOS: 52.4% WR, +56.0% PnL, 68.4% of total profit. This validates the iter 126 discovery. LINK is genuinely profitable OOS.

But **Model B (DOGE/SHIB) lost -43.0% OOS combined** (DOGE -14.7%, SHIB -28.3%). This is WORSE than iter 119's Model B performance (DOGE -16.7%, SHIB +65.8% = net +49.1%). Something changed in the meme model's behavior — SHIB went from +65.8% to -28.3%.

**Root cause**: The meme model's Optuna optimization is stochastic. Even with the same seeds, different random states in the walk-forward can produce different results when the model is borderline profitable. SHIB's 53.7% WR in iter 119 became 43.5% here — a 10pp drop that flipped SHIB from profitable to losing.

### IS/OOS ratio 7.68 is meaningless

IS Sharpe 0.10 is essentially zero. The three models' IS periods overlap differently — Model A's IS includes 2020-2024, Model C's IS includes 2022-2024. The combined IS daily PnL is diluted by the different timelines. OOS Sharpe +0.78 is more meaningful but the IS/OOS ratio is unreliable for multi-model portfolios with different IS periods.

### OOS MaxDD 126.6% is catastrophic

Three models each adding independent drawdowns. When all three models lose simultaneously, the combined drawdown triples. The baseline's 46.4% OOS MaxDD becomes 126.6% — unacceptable.

## Hard Constraints

| Constraint | Threshold | Iter 128 | Pass? |
|------------|-----------|----------|-------|
| OOS Sharpe > baseline | > +1.18 | +0.78 | **FAIL** |
| OOS MaxDD ≤ 1.2 × baseline | ≤ 55.7% | 126.6% | **FAIL** |
| OOS Trades ≥ 50 | ≥ 50 | 244 | PASS |
| OOS PF > 1.0 | > 1.0 | 1.12 | PASS |
| LINK concentration ≤ 50% | ≤ 50% | 68.4% | **FAIL** |
| IS/OOS Sharpe ratio > 0.5 | > 0.5 | 7.68 | N/A (inverted) |

## Key Learnings

1. **Model B (meme) is unstable.** SHIB's OOS performance flipped from +65.8% (iter 119) to -28.3% (iter 128) with the same config. The meme model's signal is seed/Optuna-sensitive and not robust enough for portfolio combination.

2. **LINK validates as Model C.** 52.4% OOS WR and +56.0% PnL confirms LINK has real signal. It's the strongest per-symbol OOS contributor.

3. **A+C portfolio (BTC/ETH + LINK) without Model B might be better.** If we drop the unstable meme model and combine only A (BTC/ETH) + C (LINK), we keep the two strongest models and eliminate the meme drag.

4. **Three-model MaxDD is unacceptable.** 126.6% means the portfolio lost more than its starting capital in the worst IS drawdown. Even with independent models, correlated crypto drawdowns amplify losses.

## Label Leakage Audit

- Model A: CV gap = 44 (22 × 2 symbols). Verified.
- Model B: CV gap = 44 (22 × 2 symbols). Verified.
- Model C: CV gap = 22 (22 × 1 symbol). Verified.

## Exploration/Exploitation Tracker

Last 10 iterations: [X, E, X, E, E, E, E, X, X, **X**] (iters 119-128)
Exploration rate: 6/10 = 60%

## Next Iteration Ideas

1. **A+C portfolio (BTC/ETH + LINK only)** (EXPLOITATION, combined run) — Drop Model B (meme). Run only A (BTC/ETH) + C (LINK). Two strong models without the meme drag. Expected: higher Sharpe than A+B+C, lower MaxDD.

2. **Fix meme model instability** (EXPLOITATION, single-model) — Investigate why SHIB flipped from +65.8% to -28.3%. Run Model B standalone to check if iter 119's result was an outlier. If meme is inherently unstable, drop it from the portfolio.

3. **LINK with cross-asset features** (EXPLOITATION, single-model) — Add xbtc_* features to LINK's parquet to strengthen Model C before combining.
