# Team 12 tail-contagion baseline

Candidate: `t12-tail-contagion-baseline-v1`

This baseline tests whether cross-sectional winners and losers differ when the
crypto market enters a downside tail-contagion state. It uses 252 completed
8-hour return bars (84 days) and defines market-tail observations as the worst
15% of contemporaneous cross-sectional median returns.

For each eligible contract, the signal combines two explicitly tail-conditional
quantities:

1. excess co-crash frequency: the probability that the contract is in its own
   downside tail when the market proxy is in its downside tail, less the
   contract's unconditional downside-tail frequency; and
2. tail-loss amplification: the contract's mean downside loss during market-tail
   observations divided by its unconditional mean downside loss.

The two quantities are ranked across the current universe. Contracts with the
lowest composite fragility are relative-resilience longs; contracts with the
highest composite fragility are relative-fragility shorts. Up to five contracts
are selected on each side at 8% absolute weight, so requested gross exposure is
at most 80%, requested net exposure is zero, and no symbol exceeds 8%. The
strategy emits a target no more than once every seven days. It does not use
ordinary linear correlation or rank contracts by standalone volatility.

The hypothesis is that, conditional on a market downside tail, relatively
fragile contracts continue to underperform relatively resilient contracts over
the next weekly holding interval because contagion exposes asymmetric balance
sheet, liquidity, and positioning weakness.

Falsify the thesis if tail conditioning adds no value over the mandatory
formation and rebalance matrix, if sign inversion is not materially worse, if
the effect lacks chronological and regime breadth, or if short-sleeve returns
are explained primarily by generic market beta rather than relative tail
fragility.
