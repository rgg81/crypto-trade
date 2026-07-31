# Close-location persistence baseline 01

This baseline asks whether repeated closes near one side of each completed 8-hour high-low range
represent persistent directional auction pressure. For each eligible contract it maps close
location to `[-1, 1]` over 126 completed bars, applies a 42-bar exponential half-life, and
multiplies the decayed mean location by the absolute decayed balance of location signs. A large
positive or negative value therefore requires both directional location and repeated agreement.

To distinguish the mechanism from ordinary momentum, the strategy removes the cross-sectional
linear component explained by the average rank of same-window log close return. It ranks the
residual pressure and allocates 0.5 gross to each side, with weights proportional to distance from
the cross-sectional median. It rebalances only at the Monday 00:00 UTC weekly universe boundary;
the declarative policy caps one-way turnover at 0.20 and scales risk to 18% annualized volatility.

All bar filtering is causal: a bar is usable only when its `open_time + 8 hours` is no later than
the decision boundary. The strategy is state-free, seed-independent, deterministic under symbol
sorting, and returns flat targets if fewer than six contracts have a complete formation window.

The mechanism is falsified if development evidence does not show stable positive net edge across
folds and higher-cost evaluations, or if exact sign inversion is comparably strong or stronger.
