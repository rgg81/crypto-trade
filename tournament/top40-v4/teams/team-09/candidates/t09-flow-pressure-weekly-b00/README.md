# Team 09 flow-pressure baseline

This candidate forms a weekly market-neutral spread from completed eight-hour bars. It combines
cross-sectionally residualized taker-buy imbalance, residual price pressure, and quote-volume plus
trade-count activity normalized against each coin's own history. Price/flow disagreement is treated
as exhaustion and dampens conviction rather than reversing the economic hypothesis.

The portfolio selects balanced long and short sleeves, retains names inside a wider rank buffer,
and targets only 0.28 gross. Candidate-local controls add volatility scaling, position cooldowns,
drawdown brakes, and a one-way turnover cap. Missing, incomplete, or insufficient histories request
a flat book. The implementation is deterministic and uses only rows completed by the decision.

This is a preregistered baseline and makes no performance claim. Its nearby research coordinates
are the long history, short pressure window, and gross budget recorded in `candidate.json`.
