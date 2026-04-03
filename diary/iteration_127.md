# Iteration 127 Diary

**Date**: 2026-04-03
**Type**: EXPLOITATION (LINK pruned features 185→45)
**Model Track**: LINK standalone (single-model)
**Decision**: **NO-MERGE** — pruning destroyed IS (Sharpe -0.87). Wrong features selected.

## Hypothesis

Pruning LINK from 185→45 features (meme model template) would improve signal quality, as it did for the meme model (iter 117: OOS doubled).

## Results — LINK Pruned vs LINK Auto-Discovery

| Metric | Iter 126 (185 feat) | Iter 127 (45 feat) | Change |
|--------|---------------------|---------------------|--------|
| IS Sharpe | **+0.450** | -0.867 | **catastrophic** |
| IS WR | 43.2% | 32.8% | -10.4pp |
| IS Trades | 183 | 180 | -2% |
| IS Net PnL | +100.5% | -191.2% | **-292pp** |
| OOS Sharpe | +1.20 | +0.53 | -56% |
| OOS WR | 52.4% | 45.1% | -7.3pp |
| OOS Trades | 42 | **51** | +21% (passes 50!) |

## Why Template-Based Pruning Failed

1. **Wrong features for LINK.** The 45 features were copied from the meme model (DOGE/SHIB), which has different dynamics than LINK. Features important for meme coins (body_ratio, vol_spike, taker_imbalance) don't exist in LINK's parquet. The replacements I chose (aroon_osc, kurtosis, log_return) may not be what LINK actually needs.

2. **Feature pruning must be data-driven.** The meme model pruning (iter 117) succeeded because it was based on MDI feature importance from the meme model's own training. Iter 127 used a template — selecting features by category analogy, not by measured importance. This is a fundamentally different approach.

3. **colsample_bytree was doing the right thing.** Iter 126's 185 features with colsample_bytree let Optuna/LightGBM implicitly select the ~20-30 features that actually matter for LINK. Forcing 45 explicit features removed features the model was relying on.

4. **IS WR 32.8% below break-even** means the model's directional predictions are worse than random with these features. The signal that existed with 185 features (IS WR 43.2%) was destroyed.

## Key Learning

**Feature pruning is symbol-specific.** What works for DOGE/SHIB doesn't work for LINK. To prune LINK properly:
1. Train LINK with 185 features (iter 126 config)
2. Extract feature importances from the trained models
3. Keep the top 45 by MDI gain
4. Re-run with the LINK-specific pruned set

This requires implementing feature importance extraction in the backtest pipeline, which doesn't currently exist for individual iterations.

## Label Leakage Audit

CV gap = 22 (22 × 1 symbol). Correct.

## lgbm.py Code Review

No code changes. The issue is feature selection, not the pipeline.

## Gap Quantification

IS WR 32.8%, break-even ~33.3% for ATR barriers. The model has NO edge IS with these features. OOS WR 45.1% with Sharpe +0.53 suggests some residual signal but unreliable given negative IS.

## Exploration/Exploitation Tracker

Last 10 iterations: [E, X, E, X, E, E, E, E, E, **X**] (iters 118-127)
Exploration rate: 8/10 = 80%

## Research Checklist

- **A** (features): Template-based pruning 185→45 — FAILED for LINK. Need data-driven pruning.

## Next Iteration Ideas

**LINK with 185 features (iter 126) remains the best LINK config. Don't prune without data-driven importance.**

1. **Use iter 126 LINK config as Model C** (MILESTONE, combined run) — Iter 126's LINK (IS +0.45, OOS +1.20) is good enough to test in a 3-model portfolio: A (BTC/ETH) + B (DOGE/SHIB) + C (LINK). This is the rare portfolio milestone run. The combined Sharpe from 3 decorrelated models could be our breakthrough.

2. **Add cross-asset features to LINK** (EXPLOITATION, single-model) — Generate xbtc_* features for LINK and re-run iter 126 config + cross-asset. BTC leads LINK — this adds genuinely new information.

3. **Screen XRP standalone** (EXPLORATION, single-model) — XRP has different dynamics (regulatory-driven). Screen alongside to widen Model C candidate pool.
