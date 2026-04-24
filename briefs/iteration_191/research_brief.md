# Iteration 191 — LINK feature pruning (rejected)

**Date**: 2026-04-23
**Type**: EXPLORATION (reduce feature count to improve samples/feature ratio)
**Baseline**: v0.186
**Decision**: NO-MERGE

## Motivation

After iter 189/190 both showed xbtc features hurt LINK, the question
remained: **is LINK's 193-feature set itself excessive?** LINK inherited
the feature list from BTC+ETH co-optimization; it has never been
explicitly pruned. Samples/feature ratio is 22 — well below the skill's
50-floor.

Iter 117's meme-model pruning (67 → 45 features) doubled OOS Sharpe.
Perhaps LINK has the same headroom.

## Method

`analysis/iteration_191/full_importance.py` trains 5 LightGBM classifiers
on LINK IS data (seeds 42, 123, 456, 789, 1001) and averages MDI per
feature. Produces pruned candidate lists at 120, 130, 150, 160 features.

Chose **130** as the test target (samples/feature ratio 27.8 — a modest
improvement without being so aggressive that the skill's co-optimization
warning applies).

## Result

| metric | v0.186 LINK | **iter 191 (130 feat)** | Δ |
|--------|------------:|-------------------------:|--------:|
| IS Sharpe | +1.011 | **+1.049** | +0.04 |
| IS trades | 134 | 141 | +7 |
| IS PnL | +128.37% | +133.92% | +5.55 pp |
| IS MaxDD | — | 38.66% | — |
| OOS Sharpe | +1.440 | **+1.198** | **−0.24** |
| OOS trades | 40 | 41 | +1 |
| OOS PnL | +49.19% | +39.23% | −9.96 pp |
| OOS MaxDD | — | 14.30% | — |
| OOS WR | 50.0% | 56.1% | +6.1 pp |
| OOS PF | — | 1.65 | — |

## Finding

Pruning to 130 features produces a counter-intuitive trade-off:

- **OOS WR improves** (50.0% → 56.1%) — the model picks cleaner setups
- **OOS MaxDD improves** (presumably — no baseline comparator but 14.30%
  is low)
- **OOS Sharpe DEGRADES** (+1.44 → +1.20) — smaller wins, fewer large
  moves captured

The pruned model is more *conservative*: it wins more often but the wins
are proportionally smaller. Sharpe suffers because Sharpe rewards
expected-return magnitude, not just hit-rate.

This matches the intuition: low-MDI features in LightGBM capture
**interaction effects** that enable the model to identify high-conviction
setups. Removing them smooths out the prediction distribution — fewer
aggressive long/short calls, more middle-of-the-road decisions.

## Why iter 117 worked but iter 191 didn't

Iter 117 pruned a *new* model (meme, 67 features → 45). That model was
under-trained, and pruning helped by reducing overfitting.

LINK is a *mature co-optimized* model (193 features, tuned through iter
068 → iter 186). Its feature interactions are already load-bearing. The
skill specifically warns: "For mature co-optimized models: Explicit
pruning destroys co-optimization."

Iter 191 now has empirical confirmation of that rule on LINK.

## Summary of iter 189/190/191 on LINK features

| config | features | IS Sharpe | OOS Sharpe |
|--------|---------:|----------:|-----------:|
| v0.186 baseline | 193 | **+1.011** | **+1.440** |
| iter 189 augment (+7 xbtc) | 200 | +0.683 | +1.660 |
| iter 190 swap (7 for xbtc) | 193 | +0.423 | +0.993 |
| iter 191 prune to 130 | 130 | +1.049 | +1.198 |

**v0.186's 193-feature LINK model is Pareto-optimal.** No
modification — augmenting, swapping, or pruning — improves both IS and
OOS. The feature list is a local optimum.

## Decision

NO-MERGE. LINK stays at 193 features.

## Exploration/Exploitation Tracker

Window (181-191): [X, E, X, X, X, X, X, X, E, E, **E**] → **4E/7X**.
Three straight exploration iterations on feature engineering for LINK.
Ratio slowly correcting toward the 70/30 target.

## Next Iteration Ideas

- **Iter 192**: Pivot away from LINK features. Try **xbtc features on
  Model A (BTC+ETH pooled)**. Model A has 2x samples (ratio 44 at 193
  features → 42 at 200), so feature-dilution effect is weaker. Also
  xbtc features ARE BTC's own state, which gives BTC's model its own
  historical context.
- **Iter 193**: Generate in-house features — AFML fractional
  differentiation on close/volume. Start with d=0.4 and d=0.6 computed
  on 200-bar windows; test as displacement for a low-MDI baseline
  feature in Model A.
- **Iter 194**: Expand the labeling horizon. Current 7-day timeout
  (21 candles) may be too short for DOT/LTC where trades move slowly.
  Test 14-day timeout on DOT only — might unlock more trades.
