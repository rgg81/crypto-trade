# Volume-participation breadth-thrust baseline

This candidate asks whether direction becomes more persistent when unusual trading participation is not isolated to one contract. For each eligible symbol, complete 8-hour bars are aggregated into complete UTC days. Daily quote volume is compared with a 28-day median shifted by one day, so the current observation never enters its own baseline.

The 12-day thrust is the quote-volume-excess-weighted sign of daily returns. Price magnitude does not determine the thrust. A symbol is directional only when that thrust agrees with the sign of its 28-day price change. The candidate trades only when at least half of the analyzed universe has at least two unusual-participation days, then holds up to the three strongest confirmed symbols on each side in a dollar-balanced book.

Rebalancing occurs at 00:00 UTC on ISO-even Mondays. At every other boundary the strategy returns `None`. All bar rows are explicitly filtered to require `open_time + 8h <= decision_time`, rankings use symbol as a deterministic tie-break, and the seed is intentionally unused because the rule contains no random choice.

The main falsifier is a failure to retain cost-resistant performance across development folds. The mechanism is also falsified if removing the broad cross-sectional participation gate does not materially weaken the evidence, because then breadth is not doing the economic work claimed by the hypothesis.
