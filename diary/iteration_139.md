# Iteration 139 Diary

**Date**: 2026-04-05
**Type**: EXPLORATION (ETH standalone screening)
**Model Track**: ETH standalone
**Decision**: **NO-MERGE** — ETH fails Gate 3. IS Sharpe -0.46, OOS WR 33.3%. Standalone destroys ETH's signal.

## Results

| Metric | IS | OOS |
|--------|-----|-----|
| Sharpe | -0.46 | -0.63 |
| WR | 35.6% | 33.3% |
| PF | 0.88 | 0.83 |
| Trades | 222 | 51 |
| Net PnL | -60.8% | -17.8% |

## Analysis

### ETH standalone collapses — pooling is essential

ETH achieves 55.9% OOS WR within Model A but only 33.3% standalone — a catastrophic 22.6pp drop. This is the strongest evidence that pooling BTC+ETH provides critical regularization.

**Why pooling helps**: With 196 features and only ~2,200 standalone samples (ratio 11.2), the model overfits to noise. BTC's ~2,200 additional samples bring the ratio to 22.4 — still low, but enough for LightGBM's regularization to find signal. The shared crypto patterns between BTC and ETH provide genuine cross-symbol information.

### Why LINK/BNB work standalone but ETH doesn't

LINK and BNB have similar sample counts (~2,200) and feature counts (185). Yet they achieve IS Sharpe +0.45 and +0.51 respectively. Possible explanations:
1. **Wider ATR barriers**: LINK/BNB use 3.5x/1.75x vs ETH's 2.9x/1.45x. Wider barriers are more forgiving of noise.
2. **Market efficiency**: ETH is the #2 most efficient crypto market. LINK/BNB are less institutional, more retail-driven, with more exploitable patterns.
3. **Feature relevance**: LINK/BNB parquet features may capture different, more predictive signals than ETH's auto-discovered features.

### Updated standalone screening scorecard

| Symbol | Config | IS Sharpe | OOS Sharpe | Verdict |
|--------|--------|-----------|------------|---------|
| **LINK** | ATR 3.5x/1.75x | **+0.45** | **+1.20** | **PASS** |
| **BNB** | ATR 3.5x/1.75x | **+0.51** | **+1.04** | **PASS** |
| SOL | ATR 3.5x/1.75x | +0.16 | +0.47 | MARGINAL |
| ETH | ATR 2.9x/1.45x | -0.46 | -0.63 | **FAIL** |
| BTC | ATR 3.5x/1.75x | -0.90 | -1.41 | FAIL |
| ADA | ATR 3.5x/1.75x | -0.73 | +0.31 | FAIL |
| XRP | ATR 3.5x/1.75x | -0.03 | +2.03 | FAIL |
| DOT | ATR 3.5x/1.75x | -0.02 | +1.10 | FAIL |

BTC and ETH both fail standalone. They MUST remain pooled. This definitively closes the per-symbol architecture question for Model A.

### Gap quantification

ETH standalone: WR 35.6% IS, break-even 33.3% (2:1 RR assumed). Gap +2.3pp — barely above break-even and not enough for profitability given PF < 1.0.

## Label Leakage Audit

- CV gap = 22 (22 × 1 symbol). Verified.

## Research Checklist

- **B (Symbol/Architecture)**: Tested ETH standalone (Option B). Result: fails. Model A must stay pooled.
- **E (Trade Pattern)**: 222 IS trades at 35.6% WR — model trades more often but much worse than pooled version.

## Exploration/Exploitation Tracker

Last 10 iterations: [X, E, E, E, E, X, E, X, X, **E**] (iters 130-139)
Exploration rate: 5/10 = 50%

## Next Iteration Ideas

1. **Feature pruning for Model A via colsample_bytree** (EXPLOITATION) — Instead of explicit pruning, tighten colsample_bytree range in Optuna to 0.3-0.5 (from 0.3-1.0). This forces the model to use fewer features per tree without removing them from the pool. Safer than explicit pruning.

2. **ETH with wider barriers** (EXPLOITATION) — Test ETH standalone with 3.5x/1.75x (LINK/BNB config) instead of 2.9x/1.45x. The wider barriers might be what LINK/BNB need to succeed standalone.

3. **Cross-asset features for Model A** (EXPLORATION) — Add LINK/BNB returns as features. Since these models produce genuine signal, their recent performance could inform BTC/ETH predictions.

4. **Model A with fewer Optuna trials** (EXPLOITATION) — Reduce from 50 to 25 Optuna trials. With ratio 22.4, Optuna might be overfitting hyperparameters. Fewer trials = more regularization.
