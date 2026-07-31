# Residual consensus baseline V1

This baseline asks whether asset-specific trends survive removal of a lagged crypto-market
component. At each Monday 00:00 UTC boundary it uses only 8h bars that have completed by the
decision time. It forms an equal-weight return for the available Top-12 cross-section, lags that
market return by one bar, and estimates each asset's 168-day beta to the lagged component. The
asset residual deliberately retains its intercept so that persistent asset-specific drift is not
erased.

Residual trend is measured over 28, 84, and 168 days. A name qualifies only when every horizon has
the same sign and clears a small standardized-trend floor. Ranking strength is the median absolute
horizon t-statistic multiplied by a bounded quality term based on how linearly cumulative residual
returns evolve through time. The portfolio holds the strongest two or three positive-consensus
names against the strongest two or three negative-consensus names, equal-weighted within each side,
with 0.80 total requested gross and zero requested net exposure.

Weekly gating, equal weighting, a 20% one-way turnover control, and volatility/drawdown scaling are
intended to keep turnover and concentration moderate. Missing breadth, insufficient history, or
fewer than two qualifying names on either side produces a flat request; non-rebalance boundaries
preserve existing quantities subject to organizer controls.

The economic thesis is falsified if exact sign inversion is competitive, if removing the consensus
or path-quality requirements does not weaken results, if one formation horizon or one regime
dominates, or if base and stressed costs consume the gross edge. Breadth across folds, quarters,
long and short books, and the protected local neighborhood should matter more than a single peak.
