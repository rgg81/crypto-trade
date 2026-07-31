# Team 08 baseline: correlation-network centrality rotation

This candidate estimates two deterministic correlation graphs from adjacent halves of an
84-day window of completed 8-hour returns. An edge exists when pairwise correlation is at least
0.55, and its weight is the correlation in excess of that threshold. Network connectivity is the
equal-weighted average of edge density and the largest-component share.

When connectivity falls materially, the candidate treats the market as fragmenting and holds the
five most central coins long against the five most peripheral coins short. When connectivity rises
materially, it treats the graph as reconnecting and reverses those sides. Weighted degree in the
current graph defines centrality; symbol order breaks all ties. An immaterial topology change
produces a flat book.

The strategy evaluates only at Monday 00:00 UTC, uses only bars complete by that boundary, and
requests at most 0.08 absolute weight per symbol. With twelve eligible symbols its target gross is
0.80 and target net is zero.

The mechanism is falsified if the topology-conditioned rotation adds no value over a
marginal-volatility comparator, if centrality ranks are unstable at nearby formation windows or
edge thresholds, or if either the central or peripheral role fails across the required market-role
checks.
