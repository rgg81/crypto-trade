# Team 09 repaired flow-pressure exact sign inversion

This mandatory diagnostic forms the repaired weekly market-neutral spread from completed eight-hour bars. It combines
cross-sectionally residualized taker-buy imbalance, residual price pressure, and quote-volume plus
trade-count activity normalized against each coin's own history. Price/flow disagreement is treated
as exhaustion and dampens conviction rather than reversing the economic hypothesis. Relative to
the parent, an unconfirmed positive score is scaled to 10% while an unconfirmed negative score
retains the parent's 35% scale. This directly targets the losing long sleeve observed in the weak
folds without changing the short-pressure rule.

The portfolio selects balanced long and short sleeves, retains names inside a wider rank buffer,
and targets 0.26 gross. It uses 168 completed bars for normalization and an 18-bar pressure window.
Candidate-local controls add volatility scaling, position cooldowns,
drawdown brakes, and a one-way turnover cap. Missing, incomplete, or insufficient histories request
a flat book. The implementation is deterministic and uses only rows completed by the decision.

After the complete parent target is formed, every weight is multiplied by exactly negative one.
Former longs become equal-sized shorts and former shorts become equal-sized longs. Formation,
retention state, scheduling, gross budget and risk controls are unchanged. This is a direction
diagnostic and is not a nomination candidate.
