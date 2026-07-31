# Team 10 baseline: causal contract-age cohorts

This candidate tests whether the behavior of a perpetual contract changes systematically as it
seasons after acquiring its first 180 complete days of history. At the first Monday decision of
each UTC week, it infers each currently eligible contract's age from that contract's earliest
completed past 8-hour bar. It longs up to four of the oldest contracts and shorts the same number
of the youngest contracts at 8% per symbol.

The ranking is exclusively by causal contract age. Price returns, volume, trade count, funding,
liquidity, and future contract survival do not enter the signal. Equal cohort sizes keep target
net exposure at zero; gross exposure is at most 64%.

The economic hypothesis is that recently eligible contracts retain more speculative attention and
less settled ownership than well-seasoned contracts, producing an overvaluation premium that
decays with contract age. The intended payoff is therefore long established listing vintages and
short newly seasoned listing vintages.

Falsify the candidate if the old-minus-young cohort spread is not repeatable across independent
listing vintages and chronological folds, or if either side's gross contribution is persistently
non-positive. Bull, bear, and chop role checks should also reject a result explained by one market
regime or one listing cohort.
