# Iteration 192 — DOT 14-day timeout (rejected, below multiple floors)

**Date**: 2026-04-23
**Type**: EXPLORATION (labeling horizon)
**Baseline**: v0.186
**Decision**: NO-MERGE

## Motivation

EDA of DOT trades in v0.186:
- 30% of DOT trades hit the 7-day (168h) timeout
- Timeout trades have **WR 78-86%** and mean PnL +2.9-4.7%
- Timeouts are profitable trades that moved slowly

Hypothesis: extending timeout from 7d (21 candles) to 14d (42 candles)
converts timeout trades into TP hits (8% ATR-scaled), yielding higher
Sharpe.

## Method

Full walk-forward DOT backtest with:
- `label_timeout_minutes=20160` (14 days)
- `timeout_minutes=20160` (same)
- R1, R2, R3 unchanged from v0.186

Both label and trade timeouts must match to avoid labeling/execution drift.

## Result

| metric | v0.186 DOT (7d) | **iter 192 DOT (14d)** | verdict |
|--------|-----------------:|-----------------------:|:--------|
| IS Sharpe | ~+1.3 (from iter 176) | **+0.127** | **catastrophic** |
| IS trades | ~130 | 83 | −36% |
| OOS Sharpe | ~+1.94 | +2.105 | flat (+0.17) |
| OOS trades | 40 | **29** | **−28%, below 10/mo floor** |
| OOS WR | 50.0% | 55.2% | up |
| OOS MaxDD | ~25% | 20.07% | improved |
| OOS PF | — | 2.98 | high |
| OOS/IS ratio | 1.2 | **16.64** | extreme overfit signal |

## Why it failed

**Two non-negotiable floor violations:**

1. **IS Sharpe < 1.0 floor.** IS Sharpe of +0.127 is barely above noise.
   The 14-day labeling produces labels that depend on 42 future candles;
   the added noise from 2x lookahead overwhelms the signal at training
   time.

2. **OOS trades/month < 10/month floor.** 29 trades over 13 months
   = 2.2/month. Well below the skill's 10/month minimum. A Sharpe
   computed on 29 trades has low statistical reliability regardless
   of its magnitude.

3. **OOS/IS Sharpe ratio = 16.6.** The skill's overfitting gate is 0.5
   (IS/OOS). Inverse means OOS ÷ IS = 16.6 which is 33x above the
   healthy range. This is the signature of OOS luck, not generalization.

## Why the EDA was misleading

The EDA observed that *past* timeout trades (under 7d rule) had WR 78%.
Changing the label window doesn't just extend existing trades — it
changes which trades the MODEL OPENS. With 14d labels, training labels
span more volatile futures, the optimizer picks different predictions,
and the whole trade set shifts.

The post-hoc intuition "more time → more TP hits" ignores that the
model is now optimizing for a different labeling regime. What looked
like a near-guaranteed improvement became a regression.

## Lesson

**Labeling is part of the system, not a knob on top of it.** Changing
`label_timeout_minutes` changes:
- The distribution of labels (more +1/-1, fewer neutrals with same threshold)
- The CV gap size (42 candles instead of 21)
- Which bars are trainable (bars within 14 days of window end are
  unlabeled)
- Feature-label correlations at training time

Any single change cascades through the whole walk-forward pipeline.
Safer iteration approach: **do EDA on candidate configurations FIRST**
(label distribution statistics, training-sample counts, IS CV Sharpe
estimates) before committing to a full 5-seed backtest.

## Decision

NO-MERGE. DOT's 7-day timeout is not the constraint we thought. Any
future labeling changes need pre-test filters.

## Exploration/Exploitation Tracker

Window (182-192): [X, E, X, X, X, X, X, E, E, E, **E**] → **5E/6X**.
Balancing toward 50/50.

## Next Iteration Ideas

- **Iter 193**: Compact this session and commit to just **maintaining
  v0.186** until a clear new direction emerges. The rate of failed
  exploration iterations (189, 190, 191, 192) suggests the v0.186
  baseline is near a local optimum across many dimensions.
- **Iter 194**: Alternative feature generation — AFML Ch. 5 fractional
  differentiation. Compute frac-diff close/volume at `d=0.4, 0.6`
  on BTC (the most-liquid symbol). Displacement-based, so no
  samples/feature degradation.
- **Iter 195**: Run the seed-robustness sweep of v0.186 (deferred from
  iter 186). Needed before live deployment. 3-way sweep of ensemble
  seeds — measures the Sharpe confidence interval.
