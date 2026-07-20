# Team 06 controls-off ablation

This mandatory control ablation estimates each eligible coin's beta to the contemporaneous median-crypto
return using completed bars only. Downside semivariance, residual volatility and maximum residual
drawdown are combined into a transparent low-risk score. The cross-sectional score is then
orthogonalized to the same causal beta estimate so a low-risk rank cannot silently become a market
direction trade.

The strategy code, 126-bar formation window, weekly cadence, 25% tails, factor weights and requested
gross exposure are behaviorally identical to the parent. The adjacent policy disables every
optional organizer control: volatility targeting, drawdown brakes, position and time stops, and the
turnover throttle. Hard strategy and protocol limits remain in force. This is an ablation, not a
nomination candidate.

The portfolio owns the broad lowest-risk sleeve and shorts the broad highest-risk sleeve with equal
gross. It requests no rebalance away from the weekly boundary. Minimum history, liquidity, breadth,
symbol weight, gross and net checks fail closed.

The candidate uses no market-capitalization proxy, external data, future membership, regime label,
or date-specific rule. Targets execute through the organizer at the next executable open.

The family is falsified if the short sleeve is not profitable, beta orthogonalization removes the
edge, doubled costs consume the spread, or one component or one small group of coins carries the
result.
