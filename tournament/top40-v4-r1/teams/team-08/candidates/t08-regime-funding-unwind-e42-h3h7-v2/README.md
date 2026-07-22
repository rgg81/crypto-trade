# Team 08 regime-conditioned funding unwind

The baseline traded only in 2024 because it required four price/flow-confirmed funding extremes on both sides at the same decision. This mechanism pivot keeps settled funding crowding and next-open mean reversion, but removes that forced-symmetry bottleneck.

Every UTC day, the strategy standardizes each coin's latest settled funding rate against 42 earlier events. Outside a causal 60-day BTC chop state, funding deviations of at least 0.5 robust z are eligible only after the three most recent completed bars move in the predicted unwind direction; those cohorts persist for three days. In chop, where the confirmed sleeve was weak, only unconditioned 1.25-z extremes are used and averaged over seven days. Long and short sleeves qualify independently, with 11% gross reserved for each side.

Strict pre-2024-07-01 diagnostics including funding transfers and base transaction costs produced positive raw Sharpe in bull, bear, and chop and 14 positive quarters out of 18. No historical-OOS rows were opened.
