# Team 06 downside-risk neighborhood: 126 bars, every fourteen days, 25% tails

This preregistered cadence point estimates each eligible coin's beta to the contemporaneous median-crypto
return using completed bars only. Downside semivariance, residual volatility and maximum residual
drawdown are combined into a transparent low-risk score. The cross-sectional score is then
orthogonalized to the same causal beta estimate so a low-risk rank cannot silently become a market
direction trade.

Relative to the parent, it refreshes every fourteen calendar days rather than weekly. The schedule
is anchored to 1970-01-05, a deterministic Monday epoch boundary, and contains no sample-specific
date rule. The 126-bar history, 25% tails, factor weights, gross exposure and organizer-applied risk
controls remain unchanged.

The portfolio owns the broad lowest-risk sleeve and shorts the broad highest-risk sleeve with equal
gross. It requests no rebalance away from the fourteen-day boundary. Minimum history, liquidity, breadth,
symbol weight, gross and net checks fail closed.

The candidate uses no market-capitalization proxy, external data, future membership, regime label,
or date-specific rule. Targets execute through the organizer at the next executable open.

The family is falsified if the short sleeve is not profitable, beta orthogonalization removes the
edge, doubled costs consume the spread, or one component or one small group of coins carries the
result.
