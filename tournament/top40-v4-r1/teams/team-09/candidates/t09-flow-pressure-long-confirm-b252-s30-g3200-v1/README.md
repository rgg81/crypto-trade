# Team 09 long-confirmed flow pressure: 252/30/3200

This preregistered high-extreme neighborhood candidate forms a weekly market-neutral spread from completed eight-hour bars. It combines
cross-sectionally residualized taker-buy imbalance, residual price pressure, and quote-volume plus
trade-count activity normalized against each coin's own history. Price/flow disagreement is treated
as exhaustion and dampens conviction rather than reversing the economic hypothesis. Relative to
the parent, an unconfirmed positive score is scaled to 10% while an unconfirmed negative score
retains the parent's 35% scale. This directly targets the losing long sleeve observed in the weak
folds without changing the short-pressure rule.

The portfolio selects balanced long and short sleeves, retains names inside a wider rank buffer,
and targets 0.32 gross. It uses 252 completed bars for normalization and a 30-bar pressure window.
Candidate-local controls add volatility scaling, position cooldowns,
drawdown brakes, and a one-way turnover cap. Missing, incomplete, or insufficient histories request
a flat book. The implementation is deterministic and uses only rows completed by the decision.

This is a preregistered high-extreme point and makes no performance claim. Its nearby research
coordinates are the long history, short pressure window, and gross budget recorded in
`candidate.json`.
