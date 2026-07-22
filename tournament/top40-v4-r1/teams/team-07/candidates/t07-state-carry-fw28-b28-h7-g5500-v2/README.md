# Team 07 market-state funding carry repair

The baseline decomposition showed that high-rate shorts collected funding but lost much more to
continued price appreciation. Its original adverse-price multiplier was normalized back to the
same sleeve gross, so it changed names without reducing risk. This candidate leaves that discount
unnormalized: rising shorts and falling longs now consume less capital rather than donating their
weight to another adverse name.

A completed 28-day BTC return assigns 72/28 long/short budgets in directional states and equal
budgets in chop. Every cohort must still have strictly positive expected settled-funding carry, so
the market state cannot turn Team 07 into an unrestricted directional model. Net exposure is
bounded before a target is emitted.

Daily funding ranks are averaged across seven causal cohorts. Missing cohorts age naturally, and
symbols leaving the point-in-time eligible universe are permanently pruned from live vintages.
This is intended to reduce rank-replacement churn while retaining exposure across funding events.

The trial is falsified if the short role remains negative, bear/chop breadth fails, turnover remains
above the gate, or the higher gross simply scales the baseline drawdown without improving edge.
