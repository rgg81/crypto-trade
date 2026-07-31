# T06 broad shock retention baseline

This baseline tests whether price impact survives a broad liquidity shock instead of quickly
reverting. For each symbol, it compares a two-bar event with the preceding 42 completed 8h bars.
A qualifying event requires quote volume and trade count to jump together, average quote volume
per trade to remain bounded, and both quote volume and trade count to remain elevated during the
next three completed bars. This treats trade-count expansion and a bounded average ticket as a
causal proxy for broad participation rather than a small number of oversized transactions.

The signed signal follows event impact only when at least 35% of that impact remains after the
three-bar confirmation window. Recent qualifying events receive more weight, and the aggregate is
normalized by trailing per-bar price volatility for cross-symbol ranking. Every 72 hours the book
holds up to three strongest positive and three strongest negative signals, matched by count at
15% per symbol. It goes flat when fewer than two names qualify on either side. All observations
are completed before the decision boundary; the next executable open is never inspected.

The primary falsifier is failure of the persistence condition to add value over a preregistered
shock-only ablation. The mechanism is also rejected if exact sign inversion is not worse, or if
net performance is not stable across the fixed folds, stated cost multiples, and the later
protected local horizon neighborhood.

Risk is organizer-enforced with a 15% annualized volatility target, drawdown brakes, and a 20%
maximum one-way turnover per decision. The strategy itself requests at most 90% gross exposure,
is matched long/short, and uses no position or time stop.
