# SVPP persistent-pressure baseline

This baseline tests whether sustained signed aggressor pressure predicts continuation. For each
completed eight-hour bar it computes taker-sell volume as paired total volume minus taker-buy
volume, then measures pressure as `(taker_buy - taker_sell) / total`. Base-volume pairs are
preferred, with a same-unit quote-volume pair allowed only when the base pair is absent. A symbol
is skipped when no explicit taker-buy/total pair exists; price-sign volume and volume-surprise
proxies are never substituted.

The causal feature uses up to 30 completed days. Its primary persistence view is the median of
three consecutive seven-day block means; a 12-bar-half-life exponentially weighted mean must have
the same sign. The score is 60% block persistence and 40% exponential persistence. At each fixed
96-hour rebalance bucket, the portfolio equally weights up to three contracts above +2% pressure
and up to three below -2%, assigning 0.50 gross to each side. If either side is absent, it requests
a flat book. Timestamp filtering explicitly excludes any bar that has not completed by the
decision boundary, and symbol ordering supplies deterministic tie-breaks.

Turnover resistance comes from the 96-hour cadence, equal side weights, a 20% organizer-enforced
one-way turnover limit, and no same-boundary re-entry. The risk policy also applies a 15% annual
volatility target and drawdown brakes. Stops are disabled so the baseline tests the assigned
economic feature without path-dependent exit alpha.

The hypothesis is falsified if exact sign inversion is not materially worse, pressure-tail returns
do not order monotonically, or apparent edge fails the fixed cost, turnover, fold, breadth, and
local-stability gates. The bundle is preregistered as a `baseline`; it has no neighborhood ID.
