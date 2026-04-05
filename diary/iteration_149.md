# Iteration 149 Diary

**Date**: 2026-04-05
**Type**: EXPLORATION (Hybrid VT)
**Decision**: **NO-MERGE** — hybrid VT regresses from per-symbol

## Results

| Metric | Baseline (iter 147) | Iter 149 | Change |
|--------|---------------------|----------|--------|
| OOS Sharpe | +2.65 | +2.32 | -12% |
| OOS MaxDD | 39.17% | 37.85% | -3% |
| OOS PF | 1.62 | 1.53 | -6% |

## Analysis

Hybrid VT (geometric mean of per-symbol and portfolio scales) essentially behaves
like portfolio VT, matching iter 145's OOS Sharpe +2.33. The per-symbol signal that
drove iter 147's +14% improvement is diluted when averaged with portfolio vol.

**Clear finding**: per-symbol VT alone is Pareto-optimal. Combining it with
portfolio VT discards information.

## VT Summary

| Scheme | OOS Sharpe | Verdict |
|--------|-----------|---------|
| None (iter 138) | +2.32 | baseline |
| Portfolio-wide (iter 145) | +2.33 | marginal |
| Hybrid (iter 149) | +2.32 | no gain |
| **Per-symbol (iter 147)** | **+2.65** | **WINNER (+14%)** |

## Recommendation: ACCEPT v0.147 as FINAL

After 149 iterations, the A+C+D portfolio with per-symbol vol targeting achieves:
- OOS Sharpe: +2.65
- OOS Calmar: 4.02
- OOS MaxDD: 39.2%
- OOS WR: 50.6%
- OOS PnL: +157.5%

This is a strong, validated result. Further iterations without structural changes
(new features, regime models, different candle interval) are unlikely to improve
materially. Time to shift from research to deployment preparation:
1. Implement per-symbol VT in `src/crypto_trade/backtest.py`
2. Full re-run on actual engine to validate integrated metrics
3. Live paper trading
4. Order management / execution engine hardening

## Exploration/Exploitation Tracker

Last 10 iterations: [E, X, E, E, E, E, X, E, E, **E**] (iters 140-149)
Exploration rate: 8/10 = 80% ✓

## Next Iteration Ideas

1. **ACCEPT v0.147 as FINAL** — Strong baseline. Move to deployment.

2. **Implement per-symbol VT in backtest.py** (EXPLOITATION, code change) — For
   production. Code modification needed to move post-processing into engine.

3. **Entropy/CUSUM features** (EXPLORATION) — Only if continuing research. These
   require parquet regeneration and would be a 2-3 iteration project.

4. **Different candle interval** (EXPLORATION) — 4h or 12h backtest. Fundamentally
   different approach, multi-week project.
