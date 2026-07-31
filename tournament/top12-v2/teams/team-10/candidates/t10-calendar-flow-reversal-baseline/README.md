# Team 10 calendar-flow reversal baseline

This baseline tests whether recurring UTC month changes temporarily concentrate one-sided trading. It measures each eligible contract's price displacement over nine completed 8-hour bars and the concurrent taker-buy imbalance surprise relative to the preceding 81 completed bars. A contract is eligible for the signal only when both standardized measures are material and point in the same direction.

During the 24 hours before through 48 hours after a month change, the strategy fades up to three strongest confirmed dislocations on each side: negative price-and-flow pressure is bought and positive pressure is sold. It requires at least two names on both sides, holds a dollar-neutral 0.80-gross book, and otherwise requests flat targets. Calendar windows are derived from the current UTC month; there are no literal date anchors or timestamp-to-position tables.

Turnover is structurally limited by the short recurring monthly window, equal rather than continuously strength-proportional weights, and the organizer-enforced 0.20 one-way turnover cap. Volatility scaling targets 15% annualized risk, with drawdown brakes at 10% and 15%.

The economic claim is causal: temporary calendar-driven inventory pressure should mean-revert after aggressive flow confirms crowding. It is falsified if the preregistered reversal does not beat its exact sign inversion directionally or if its gross edge is not positive after prescribed costs across development folds.
