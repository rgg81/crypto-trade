# Team 08 funding-crowding reversal baseline

This candidate treats the latest already settled funding observation as a crowding event. Each rate
is robustly standardized against that contract's prior settled events. Positive extremes imply a
potential crowded-long unwind and negative extremes imply a potential crowded-short unwind.

Funding extremity alone cannot trade. The latest completed market-residual price move and normalized
taker pressure must already align with the proposed unwind. Their fixed continuous combination sizes
the score; it never changes the funding-implied sign. The portfolio has no expected-carry constraint
and may pay funding, which keeps this mechanism distinct from Team 07.

Broad long and short event sleeves enter through three overlapping daily cohorts. A day without a
new confirmed cohort adds no sleeve while live vintages age normally; an exposure-limit breach
requests a flat book. The strategy uses no current settlement, future bar, external series,
synthetic basis, regime label, or date-specific rule.

The mechanism is falsified if crowded extremes continue, next-open execution misses the unwind,
one funding direction dominates, or the signal is nonpositive after doubled and tripled costs.
