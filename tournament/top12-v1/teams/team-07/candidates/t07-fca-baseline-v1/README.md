# Team 07 funding-curve-acceleration baseline

Candidate: `t07-fca-baseline-v1`

## Thesis

Changes in perpetual-futures funding encode changes in leveraged positioning demand. A funding
curve whose slope is rising and whose first difference is itself accelerating should identify
contracts where that demand is still being repriced. The baseline therefore buys the strongest
positive derivative signals and shorts the strongest negative derivative signals for the next
daily holding interval.

This is not a passive funding-carry strategy. The latest funding level is never added to the
alpha. Instead, the combined slope/acceleration score is cross-sectionally residualized against
the latest settled funding level before contracts are ranked.

## Construction

- Make decisions only at 00:00 UTC, so target changes occur at most once per day.
- For every eligible symbol, use the most recent 21 funding settlements strictly before the
  decision boundary.
- Estimate funding slope as the least-squares trend in funding rates and acceleration as the
  least-squares trend in their first differences.
- Robustly standardize slope and acceleration across the current eligible universe, combine them
  equally, and remove the combined score's linear exposure to current funding level.
- Hold up to five highest residual scores long and five lowest residual scores short. Allocate
  equal gross capital to both sides, with no symbol above 8%.
- Request no more than 80% gross exposure and zero intended net exposure. If fewer than ten
  symbols have adequate history, reduce gross exposure rather than breach the symbol cap.

All settlement timestamps are checked in the strategy. Rows at or after the decision boundary are
excluded, even if supplied by the runner.

## Falsifier

Falsify the hypothesis if slope/acceleration does not add stable predictive value across the
mandatory chronological folds, long/short role checks, formation/rebalance grid, and cost
multiples; if a funding-level-only or sign-inverted control explains the result; or if next-open
execution and turnover costs consume the effect.
