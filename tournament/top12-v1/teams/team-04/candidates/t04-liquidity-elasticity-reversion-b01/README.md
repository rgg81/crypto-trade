# Team 04 baseline: liquidity-impact elasticity reversion

## Thesis

A directional move is more likely to be temporarily dislocated when its size is unusually large
relative to the liquidity capacity that accompanied it. The baseline measures the completed
21-day log return and divides it by the square root of quote-volume capacity relative to the
symbol's trailing capacity anchor. This is a signed impact-elasticity estimate, not a rank on raw
volume.

The elasticity is robustly standardized against the symbol's own prior observations, then
standardized again across the eligible universe at the decision boundary. The two standardized
views receive equal weight, and the final score takes the opposite sign to express reversion.

Only rows satisfying `open_time + 8h <= decision_time` are used. The strategy can submit targets
at most once per 24 hours. It requests a matched-dollar long/short book with a 0.39 budget per
side and a 0.079 per-symbol cap, so gross exposure is at most 0.78 and net exposure is zero up to
floating-point precision.

## Falsifier

Reject the hypothesis if replacing the capacity-adjusted elasticity with the same completed
return normalization is not materially worse, or if apparent edge is concentrated in crash
observations rather than recurring across ordinary regimes. Failure to produce positive gross
contribution on both long and short roles also falsifies this baseline as a balanced
cross-sectional mechanism.

## Declared baseline

- Formation: 63 completed 8-hour bars (21 days).
- Own-history normalization: 270 prior 8-hour observations, with at least 90 valid elasticity
  observations.
- Capacity anchor: trailing quote-volume median shifted one bar, requiring at least 126 bars.
- Rebalance interval: no less than 24 hours.
- Controls: organizer risk controls disabled for this transparent baseline.
