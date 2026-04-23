# Iteration 192 — DOT 14-day timeout (rejected, catastrophic IS collapse)

**Date**: 2026-04-23
**Type**: EXPLORATION (labeling horizon)
**Baseline**: v0.186 — unchanged
**Decision**: NO-MERGE

## TL;DR

Extending DOT's label/trade timeout from 7 days to 14 days collapsed IS
Sharpe from ~+1.3 to **+0.13** (below 1.0 floor) and cut OOS trades to
29 (2.2/month, below 10/month floor). OOS Sharpe looks great (+2.1)
but OOS/IS ratio of **16.6** is a clear overfitting signature.

## Two floor violations

1. **IS Sharpe +0.127 < 1.0 floor** — non-negotiable NO-MERGE trigger.
2. **OOS 29 trades / 13 months = 2.2/month < 10/month floor** — second
   non-negotiable NO-MERGE trigger.

Either alone would kill the merge. Both together is definitive.

## EDA predicted improvement — why the real run didn't deliver

EDA of v0.186 DOT trades showed 30% of trades hit the 7-day timeout,
with WR 78-86% and positive mean PnL. Natural intuition: longer timeout
= timeout trades convert to TP hits = higher Sharpe.

Intuition was wrong because:

1. **Training labels change when timeout changes.** 14-day labels scan
   42 future candles instead of 21. That's 2x as much label noise per
   training sample. Model's learnable signal degrades.
2. **Trade set shifts, it doesn't extend.** The model doesn't re-run
   the same predictions with longer hold — it optimizes against a
   different label set entirely.
3. **Early-training months lose samples.** Bars within 14 days of
   window-end can't be labeled. Training-sample count drops.

## Lesson

Label parameters are NOT independent of everything else. Changing
`label_timeout_minutes` cascades into CV gap size, training sample
count, label noise, and Optuna's objective surface. **Post-hoc EDA
of baseline trade characteristics does NOT predict how the system will
behave under a modified labeling regime.**

For future labeling experiments: first compute, on IS data alone,
the new label distribution and CV Sharpe estimate *before* committing
to a full walk-forward 5-seed backtest.

## Exploration/Exploitation Tracker

Window (182-192): [X, E, X, X, X, X, X, E, E, E, **E**] → **5E/6X**.
4 recent exploration iterations. Balancing toward the 70/30 target but
the hit rate is poor — v0.186 is a strong baseline and most changes
hurt.

## Next Iteration Ideas

- **Iter 193**: AFML Ch. 5 fractional differentiation features on BTC.
  Computed as displacement (one low-MDI feature → frac-diff'd close).
  This is a real new-feature direction that's well-motivated in
  quantitative finance literature, not just a parameter tweak.
- **Iter 194**: Seed robustness sweep of v0.186 — ensemble seed groupings
  [1,2,3,4,5], [11,13,17,19,23], etc. Confirms v0.186's Sharpe isn't
  seed-luck before live deployment.
- **Iter 195**: Reconsider objective. After 4 consecutive exploration
  NO-MERGEs, v0.186 looks like a local optimum across many dimensions
  (features, labels, risk mitigations). Either commit to live-shipping
  v0.186, or accept that further gains need a fundamental
  architectural change (different model class, different timeframe,
  different labeling framework).
