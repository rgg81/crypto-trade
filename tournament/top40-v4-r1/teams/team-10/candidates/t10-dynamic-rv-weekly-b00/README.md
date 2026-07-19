# Team 10 dynamic relative-value baseline

This candidate rebuilds a deterministic nearest-neighbor pair graph once each week from completed
returns. Each possible trade then needs a bounded rolling hedge ratio, a positive finite convergence
half-life, repeated residual zero crossings, and a robust current dislocation. Pair legs preserve
their fitted hedge ratio and are normalized before portfolio aggregation.

The book is deliberately small: 0.30 maximum gross, 0.025 per symbol, a weekly decision schedule,
and no trade unless both long and short roles are populated. Candidate-local controls cap turnover,
scale volatility, stop adverse legs, time out stale convergence positions, and brake drawdowns.
Incomplete or structurally weak histories produce a flat request.

This is a preregistered baseline, not a performance claim. Formation length, entry threshold, and
minimum pair correlation define its local research neighborhood.
