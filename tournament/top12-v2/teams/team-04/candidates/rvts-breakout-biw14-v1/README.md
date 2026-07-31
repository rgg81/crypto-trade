# rvts-breakout-biw14-v1

This baseline tests whether a directional price breakout becomes more durable when the short end
of realized volatility enters a new high-volatility regime relative to the longer state. The
economic intuition is that a breakout accompanied by newly concentrated price discovery should
carry more information than the same channel crossing during an unchanged volatility regime.

At every scheduled decision, each eligible contract uses only 8h bars completed by that boundary.
The volatility curve is the ratio of 7-day to 42-day root-mean-square log returns. A contract
qualifies only when that ratio is at least 1.15 and is at least 1.08 times its value seven days
earlier. The rule then searches the latest seven days for the most recent closing-price break of
the preceding 14-day Donchian channel. Price must remain on the corresponding side of the recent
channel median. Signal strength combines normalized breakout distance with curve excess.

The strategy rebalances at 00:00 UTC on Mondays in even-numbered ISO weeks. It ranks long and short qualifiers,
matches the number selected on each side, and holds at most three per side at an unlevered weight
of 0.15 per name. It stays flat unless both sides are present. This creates zero requested net
exposure, at most 0.90 gross exposure, and deliberately moderate turnover. The risk policy adds a
15% volatility target, two drawdown brakes, and a 0.20 one-way turnover limit. Central evaluation
continues to own fills, funding, costs, membership exits, and all policy enforcement.

The implementation is deterministic, ignores the seed, does not retain state, and returns `None`
between scheduled boundaries. Missing or inadequate observations cannot produce a signal.

The thesis is falsified if the baseline does not retain edge under higher costs and across folds
and regimes, if its exact sign inversion is not materially worse, or if a control that removes the
volatility-curve transition performs similarly. Weak long/short breadth, unstable neighboring
horizons, or concentration-driven results also reject the mechanism.
