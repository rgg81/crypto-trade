# Iteration 109 Diary

**Date**: 2026-04-01
**Type**: EXPLOITATION
**Merge Decision**: NO-MERGE (EARLY STOP — Year 2022: PnL=-30.8%, WR=43.5%, 23 trades)

**OOS cutoff**: 2025-03-24

## Results

| Metric | Iter 109 (DOGE only) | Iter 108 (DOGE+SHIB) |
|--------|---------------------|---------------------|
| IS Sharpe | -0.80 | +0.10 |
| IS WR | 45.8% | 38.6% |
| IS PF | 0.76 | 1.03 |
| IS MaxDD | 40.6% | 108.6% |
| IS Trades | 24 | 114 |
| Early Stop | Year 2022 | Year 2023 |

DOGE-only is dramatically worse. IS Sharpe collapsed from +0.10 to -0.80. Only 24 trades generated (vs 114).

## Critical Insight: Training Data Volume Matters More Than Per-Symbol Purity

Removing SHIB halved training samples (4,400 → 2,200). Despite SHIB losing money in execution, its ~2,200 samples provided the model with shared meme coin patterns that improved DOGE predictions. The pooled model learned cross-symbol meme dynamics that a single-symbol model cannot access.

Evidence:
- Best CV Sharpe dropped from 0.22-0.28 (DOGE+SHIB) to 0.05-0.07 (DOGE-only)
- Optuna converged to threshold=0.501 (no filtering) and training_days=50 (minimal data) — signs of no signal found
- Feature ratio 52.4 is technically above minimum 50, but the optimization landscape is too flat for Optuna to navigate

## Exploration/Exploitation Tracker

Last 10 (iters 100-109): [E, X, E, E, E, E, E, E, E, **X**]
Exploitation rate: 2/10 = 20%. Type: EXPLOITATION (symbol removal).

## Research Checklist

- **B (Symbols)**: DOGE-only fails Gate 3 with IS Sharpe -0.80. It NEEDS pooled training data.
- **E (Trade Patterns)**: Only 24 trades — too few for meaningful pattern analysis.

## Next Iteration Ideas

1. **EXPLOITATION: Return to DOGE+SHIB but with per-symbol barrier multipliers.** SHIB needs wider barriers (e.g., 3.5x/1.75x instead of 2.9x/1.45x) to fix the asymmetric RR that caused its -9.1% PnL. Keep pooled model for training, but adjust execution per symbol.

2. **EXPLORATION: Reduce features to 20-25 for DOGE-only.** If the problem is ratio, cutting to 25 features (ratio 2200/25=88) might recover the solo model. Focus on the highest-impact features only (volume, mean reversion).

3. **EXPLORATION: Shorter timeout (3 days instead of 7).** Meme coin moves resolve faster. A 3-day timeout on 8h candles = 9 candles forward scan, reducing CV gap and label overlap. This fundamentally changes the prediction task.

4. **EXPLORATION: Add BTC cross-asset features to the meme pool.** BTC dumping → meme coins dump harder. Adding `xbtc_return_1`, `xbtc_natr_14` as features (not as a trading symbol) could improve predictions without adding BTC to the training universe.
