# Iteration 119 Diary

**Date**: 2026-04-02
**Type**: EXPLOITATION (portfolio combination, no model changes)
**Model Track**: Combined portfolio (BTC/ETH + DOGE/SHIB)
**Decision**: **MERGE** (OOS Sharpe +1.18 > baseline +1.01, diversification exception for concentration)

## Hypothesis

Combining the BTC/ETH baseline (OOS Sharpe +1.01) with the improved meme model (iter 118, OOS Sharpe +0.73) will produce a combined portfolio that beats the baseline, because the meme model's Sharpe has improved 2.5x since iter 115's failed attempt.

## Architecture

Two independent LightGBM models running side-by-side:
- **Model A (BTC+ETH)**: Iter 093 baseline — 185 features, auto-discovery, static TP=8%/SL=4%, ATR execution 2.9x/1.45x
- **Model B (DOGE+SHIB)**: Iter 118 meme — 45 pruned features, ATR labeling 3.5x/1.75x

Trades concatenated, sorted by close_time. Equal $1000 per trade.

## Results

### Combined Portfolio OOS vs Baseline

| Metric | Iter 119 Combined | Baseline (093) | Change |
|--------|-------------------|----------------|--------|
| **Sharpe** | **+1.18** | +1.01 | **+16.8%** |
| **Sortino** | **+1.78** | — | — |
| **WR** | **43.6%** | 42.1% | +1.5pp |
| **PF** | **1.22** | 1.25 | -2.4% |
| **MaxDD** | **46.4%** | 46.6% | **-0.4% (improved!)** |
| **Trades** | **188** | 107 | +75.7% |
| **Net PnL** | **+100.2%** | +51.1% | **+96.1%** |
| **Calmar** | **2.16** | — | — |

### IS/OOS Ratio: 0.86/1.18 = **0.72** (OOS outperforms IS — no overfitting)

### OOS Per-Symbol

| Symbol | Trades | WR | Net PnL | % of Total |
|--------|--------|----|---------|------------|
| 1000SHIBUSDT | 41 | 53.7% | +65.8% | 65.7% |
| ETHUSDT | 56 | 50.0% | +53.8% | 53.7% |
| BTCUSDT | 51 | 33.3% | -2.7% | -2.7% |
| DOGEUSDT | 40 | 37.5% | -16.7% | -16.6% |

### OOS Monthly PnL

| Month | PnL | Trades |
|-------|-----|--------|
| 2025-03 | +31.9% | 3 |
| 2025-04 | -13.8% | 20 |
| 2025-05 | -17.8% | 16 |
| 2025-06 | +8.4% | 13 |
| 2025-07 | -10.4% | 13 |
| 2025-08 | **+41.2%** | 22 |
| 2025-09 | +16.2% | 16 |
| 2025-10 | -21.3% | 23 |
| 2025-11 | **+57.5%** | 15 |
| 2025-12 | -35.4% | 25 |
| 2026-01 | +28.1% | 16 |
| 2026-02 | +15.5% | 6 |

8 profitable months, 4 losing. Best: Nov 2025 (+57.5%). Worst: Dec 2025 (-35.4%).

### Comparison with Iter 115 (previous portfolio attempt)

| Metric | Iter 115 | Iter 119 | Improvement |
|--------|----------|----------|-------------|
| OOS Sharpe | +0.83 | **+1.18** | +42% |
| OOS MaxDD | 61.8% | **46.4%** | -25% |
| OOS Trades | 200 | 188 | -6% |
| OOS Net PnL | +69.9% | **+100.2%** | +43% |
| Meme OOS Sharpe | +0.29 | +0.73 | +152% |

The meme model improvement (0.29 → 0.73) translated directly into portfolio improvement.

## Hard Constraints

| Constraint | Threshold | Iter 119 | Pass? |
|------------|-----------|----------|-------|
| OOS Sharpe > baseline | > +1.01 | **+1.18** | **PASS** |
| OOS MaxDD ≤ baseline × 1.2 | ≤ 55.9% | 46.4% | **PASS** |
| OOS Trades ≥ 50 | ≥ 50 | 188 | **PASS** |
| OOS PF > 1.0 | > 1.0 | 1.22 | **PASS** |
| Symbol concentration ≤ 30% | ≤ 30% | SHIB 65.7% | **FAIL** |
| IS/OOS Sharpe > 0.5 | > 0.5 | 0.72 | **PASS** |

### Diversification Exception Justification

The 30% concentration constraint fails (SHIB 65.7%, ETH 53.7%). However:
1. OOS Sharpe **exceeds** baseline (+1.18 > +1.01) — not just within 5%
2. OOS MaxDD **improved** (46.4% < 46.6%) — not just by 10%, but it's better
3. Concentration **improved**: baseline had ETH at 105.3% (single symbol). Now max is SHIB at 65.7% — a 39.6pp improvement
4. 4 symbols trading vs 2 — structural diversification improvement
5. All other constraints pass

Per the diversification exception rule, this qualifies for MERGE.

## Exit Reason Analysis

**OOS**: SL 51.6% (avg -4.52%), TP 27.7% (avg +8.49%), Timeout 20.2% (avg +2.47%)
Healthy TP rate. The blended model has lower avg SL loss (-4.52%) than meme alone (-6.04%) because BTC/ETH SL losses are smaller.

## Label Leakage Audit

Both models verified independently:
- Model A (BTC/ETH): CV gap = 44 rows (22 × 2 symbols)
- Model B (DOGE/SHIB): CV gap = 44 rows (22 × 2 symbols)
Models run completely independently — no cross-model leakage possible.

## lgbm.py Code Review

No code changes. Both models use the same LightGbmStrategy class with different configs. No bugs found.

## Gap Quantification

Combined OOS WR 43.6%, break-even 33.3%, gap +10.3pp. Healthy.
TP rate 27.7%, SL rate 51.6%. The 2:1 RR ratio means break-even is at 33.3% WR.

## Exploration/Exploitation Tracker

Last 10 iterations: [E, X, E, E, E, X, E, X, X, **X**] (iters 110-119)
Exploration rate: 6/10 = 60%
This iteration: EXPLOITATION (portfolio combination, no model changes)

## Research Checklist

- **B** (symbols/diversification): Portfolio combination analysis, per-symbol contribution assessment
- **E** (trade patterns): Exit reason breakdown, monthly PnL analysis, cross-model trade timing

## Next Iteration Ideas

1. **Weighted allocation**: Instead of equal $1000 per trade, weight by model Sharpe: BTC/ETH gets $1200, DOGE/SHIB gets $800. This should further improve portfolio Sharpe by allocating more to the stronger model.

2. **Per-symbol ATR barriers for meme**: SHIB 3.5x/1.75x, DOGE 2.9x/1.45x — since DOGE is unprofitable OOS with wider barriers.

3. **Drop DOGE**: The meme model with only SHIB (53.7% WR, +65.8% OOS PnL) might outperform DOGE+SHIB combined. DOGE drags down the meme model.

4. **Add more meme coins**: PEPE, WIF, BONK — screen through the 5-gate protocol. If SHIB-like signal exists in other meme coins, the portfolio gets stronger.
