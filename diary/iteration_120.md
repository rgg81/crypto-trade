# Iteration 120 Diary

**Date**: 2026-04-02
**Type**: EXPLOITATION (drop DOGE from meme model)
**Model Track**: Combined portfolio (BTC/ETH + SHIB only)
**Decision**: **NO-MERGE** — IS/OOS Sharpe ratio 0.34 < 0.50 (researcher overfitting gate fails)

## Hypothesis

Dropping DOGE (unprofitable OOS at -16.7%) and running SHIB-only should improve combined portfolio Sharpe.

## Results

### Combined OOS vs Baseline (iter 119)

| Metric | Iter 120 | Baseline (119) | Change |
|--------|----------|----------------|--------|
| OOS Sharpe | **+2.08** | +1.18 | +76% |
| OOS WR | **47.0%** | 43.6% | +3.4pp |
| OOS PF | **1.48** | 1.22 | +21% |
| OOS MaxDD | **36.5%** | 46.4% | -21% (better) |
| OOS Trades | **151** | 188 | -20% |
| OOS Net PnL | **+141.2%** | +100.2% | +41% |
| IS Sharpe | +0.71 | +0.86 | -17% |
| IS/OOS Ratio | **0.34** | 0.72 | **FAIL (<0.5)** |

### OOS Per-Symbol

| Symbol | Trades | WR | Net PnL | % of Total |
|--------|--------|----|---------|------------|
| 1000SHIBUSDT | 44 | **59.1%** | +90.1% | 63.8% |
| ETHUSDT | 56 | 50.0% | +53.8% | 38.1% |
| BTCUSDT | 51 | 33.3% | -2.7% | -1.9% |

### OOS Monthly PnL

10 profitable months, 2 losing. Best: Nov 2025 (+44.2%), Feb 2026 (+44.2%). Worst: Aug 2025 (-14.6%).

## Why NO-MERGE Despite Impressive Numbers

The IS/OOS Sharpe ratio of **0.34** is the critical failure. This means:

1. **OOS is 3x better than IS** — this is not normal. Healthy models have OOS ≈ IS or slightly worse.
2. **SHIB-only OOS WR 59.1%** (vs 53.7% when pooled with DOGE in iter 119). The single-symbol model without DOGE's diluting effect is more selective — 44 trades vs 41. But WR jumped from 53.7% to 59.1%, which is suspicious.
3. **Regime dependency**: The OOS period (Mar 2025 → Feb 2026) may simply be SHIB's best period. The IS period includes SHIB's difficult 2022-2023 phase where the model struggles. A model that underperforms IS but thrives in OOS is relying on favorable conditions, not skill.
4. **Training data halved**: SHIB-only trains on ~2,200 samples/year (vs ~4,400 with 2 symbols). With 45 features, the samples/feature ratio is ~49 — at the lower bound. This makes the model more sensitive to Optuna's random search.

The IS/OOS gate exists precisely to catch this pattern. Per the skill rules: "IS/OOS Sharpe ratio > 0.5 (researcher overfitting gate)" — this is a hard constraint, not subject to exception.

## What We Learned

1. **SHIB-only model overfits differently** than DOGE+SHIB pooled. The single-symbol model has less regularization from data diversity.
2. **Per-symbol models remain problematic** for meme coins. Iter 099 and 109 showed per-symbol BTC/ETH fails. Now iter 120 shows per-symbol SHIB fails the IS/OOS gate despite strong headline OOS.
3. **The iter 119 baseline (DOGE+SHIB) is more robust**. Even though DOGE is unprofitable OOS, its presence during training provides regularization that prevents SHIB-only overfitting.

## Hard Constraints

| Constraint | Threshold | Iter 120 | Pass? |
|------------|-----------|----------|-------|
| OOS Sharpe > baseline | > +1.18 | +2.08 | PASS |
| OOS MaxDD ≤ 1.2 × baseline | ≤ 55.6% | 36.5% | PASS |
| OOS Trades ≥ 50 | ≥ 50 | 151 | PASS |
| OOS PF > 1.0 | > 1.0 | 1.48 | PASS |
| Symbol concentration ≤ 30% | ≤ 30% | SHIB 63.8% | FAIL |
| **IS/OOS Sharpe ratio > 0.5** | > 0.5 | **0.34** | **FAIL** |

## Label Leakage Audit

- Model A (BTC/ETH): CV gap = 44 (22 × 2 symbols). Verified.
- Model B (SHIB only): CV gap = **22** (22 × 1 symbol). Verified in logs.
- The reduced gap with 1 symbol is correct by construction.

## lgbm.py Code Review

No code changes. SHIB-only means `_discover_feature_columns()` runs on 1 symbol — features from SHIB parquet only. Cross-asset features (`xbtc_*`) still work since they reference BTC data separately. No bugs.

## Exploration/Exploitation Tracker

Last 10 iterations: [E, X, E, E, E, X, E, X, X, **X**] (iters 111-120)
Exploration rate: 6/10 = 60%

## Next Iteration Ideas

1. **Keep DOGE+SHIB pooled** — iter 119's architecture (4-symbol combined) is more robust. SHIB-only overfits.
2. **Per-symbol DOGE barriers** — Instead of dropping DOGE, try DOGE at 2.9x/1.45x (narrower) while SHIB stays at 3.5x/1.75x. Requires code change for per-symbol barrier multipliers.
3. **Weighted allocation** — BTC/ETH gets $1200/trade, DOGE/SHIB gets $800/trade. Weights proportional to model Sharpe.
4. **Add PEPE or WIF** — Screen additional meme coins through the 5-gate protocol. If profitable, they replace DOGE's diversification role.
