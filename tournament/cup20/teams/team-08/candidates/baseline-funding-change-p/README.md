# baseline-funding-change

The transparent baseline for team 08's lane, and the book the exact sign inversion is run
against. It is a reference point, not a contender.

**Signal.** For each eligible coin, the most recent funding rate minus the mean of the
`REGIME_WINDOW = 20` funding rates before it. Positive means funding has risen against the
coin's own recent regime.

**Book.** Sort the eligible cross-section on that difference; long the lowest third,
short the highest third, equal weight, dollar neutral. Rebalance every
`REBALANCE_BARS = 3` boundaries (one calendar day); hold quantities in between.

**What is deliberately absent.** No normalisation by the coin's own funding scale, no
control for the funding *level*, no dispersion gate, no concentration, no holding-period
logic. Every one of those is a later, separately journaled step, so that each can be
attributed.

**Causality.** The strategy applies its own `funding_time < decision_time` cut rather than
relying on the context to have applied one, and never reads a bar.

**Risk policy.** Nothing declared. `volatility_target.enabled` is `false` (charter A3).
