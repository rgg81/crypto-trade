# Iteration 196 — Frac-diff on Model A + exit-criterion analysis

**Date**: 2026-04-23
**Type**: EXPLORATION + META-ANALYSIS
**Baseline**: v0.186
**Decision**: NO-MERGE (pre-test below threshold). **Recommendation: stop
offline iteration; ship v0.186 to paper-trading.**

## Pre-test result

Applied iter 195's IS-only CV-proxy process to Model A (BTC+ETH pool,
5303 training samples, 2x more than LINK).

| config | features | proxy Sharpe | Δ vs baseline |
|--------|---------:|-------------:|--------------:|
| (A) Baseline 193 | 193 | −0.0387 ± 0.0105 | — |
| (B) +3 frac-diff | 196 | −0.0355 ± 0.0039 | **+0.0032** |
| (C) swap 1 low-MDI for fracdiff_close_d02 | 193 | −0.0426 ± 0.0149 | −0.0038 |

**Δ is below the +0.01 pre-test merge threshold.** Full backtest would
likely produce the same lukewarm result as LINK's iter 189/190.

Frac-diff MDI ranks in config B:
- fracdiff_close_d02: rank 35/196 (top 18%) — significant
- fracdiff_close_d04: rank 90/196 (top 46%) — moderate
- fracdiff_volume_d02: MDI=0 — useless

## The 7-iteration exploration pattern

| iter | direction | decision | reason |
|------|-----------|----------|--------|
| 178 | AVAX/ATOM/AAVE with R1+R2 | NO-MERGE | year-1 fail-fast |
| 180 | APT screen | NO-MERGE | insufficient IS history |
| 183 | XLM screen | NO-MERGE | year-1 PnL −4.5% |
| 189 | LINK + xbtc augment | NO-MERGE | IS Sharpe crashed 1.01 → 0.68 |
| 190 | LINK swap 7 for xbtc | NO-MERGE | IS Sharpe 0.42 (both fail) |
| 191 | LINK prune 193 → 130 | NO-MERGE | OOS Sharpe 1.44 → 1.20 |
| 192 | DOT 14d timeout | NO-MERGE | IS +0.13, OOS 2.2 tr/mo (both fail) |
| 195 | LINK frac-diff | NO-MERGE | pre-test Δ +0.003 < threshold |
| 196 | Model A frac-diff | NO-MERGE | pre-test Δ +0.003 < threshold |

**Nine consecutive NO-MERGEs on exploration**, across all feature-engineering
directions attempted (cross-asset, pruning, augmentation, fractional
differentiation, label horizon, new symbols). v0.186's 193-feature /
4-symbol / R1+R2+R3 configuration is a **robust local optimum** across
the iteration plan's explorable axes.

## Why further offline iteration is poor-ROI

1. **All cheap-to-test directions have been tried.** Hyperparameter
   tweaks, feature add/swap/prune, risk mitigation additions — all
   have been exhausted. Remaining ideas (meta-labeling, different
   timeframes, different base learners) require major engineering
   investment (days, not hours) with unknown payoff.

2. **The baseline is statistically sound** (iter 193 bootstrap:
   P(OOS Sharpe > 1.0) = 79%, combined IS+OOS = 86%). Shipping is
   justified.

3. **Live data is the missing input.** The backtest framework is a
   bounded environment; it can't produce novel information. Paper-trading
   provides:
   - Observation of slippage, fill rates, exchange outages
   - Real correlations among the 5 symbols in a forward-looking window
   - Feedback on R3's OOD cutoff behaviour on genuinely-out-of-distribution
     market events
   - A real DOT standalone signal measurement (vs. bootstrap's +0.05
     with wide CI)

4. **Post-paper-trading iterations will be higher-signal.** After 2-4
   weeks of live data, any iteration has:
   - A real-world anchor for "did X work?"
   - New trade samples to retrain on
   - Ground-truth for R3 cutoff tuning

## Recommendation

**Iter 197 should be: ship v0.186 to paper-trading.** Use the existing
live engine (`src/crypto_trade/live/`). Log all decisions (signals,
R1/R2/R3 gates, trade outcomes) for post-analysis. After 2 weeks,
revisit iteration direction with live-data-informed hypotheses.

Until that paper-trading window closes, **offline iteration is unlikely
to produce merges and will burn session time on increasingly-marginal
improvements**.

## Exploration/Exploitation Tracker

Window (186-196): [X, X, E, E, E, E, V, X, E, E, **E**] — **6E/4X** +
1 validation. Exploration ratio near the 70/30 target, but the hit rate
has been zero.

## Decision

NO-MERGE on iter 196. v0.186 stands. **STOP offline iteration after
this diary entry; pivot to paper-trading in iter 197.**
