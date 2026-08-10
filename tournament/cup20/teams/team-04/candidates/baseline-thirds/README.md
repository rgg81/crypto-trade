# baseline-thirds

The transparent baseline for team 04's lane, and the reference every later variant is measured
against.

Rank the eligible cross-section by **market-residual momentum**: the trailing 63-bar (21-day) sum
of log returns with an estimated market component removed, where the market factor is the
equal-weight mean log return of the symbols the organiser named eligible at that decision, and the
loading on it is a causal OLS slope fitted with an intercept on the trailing 270 bars (90 days)
ending at the decision. The most recent bar is skipped. Long the top third, short the bottom
third, equal weight inside each sleeve, dollar neutral at unit gross, rebalanced every 21 bars
(7 days) and holding quantities in between.

Nothing is fitted outside the decision's own context: the strategy holds no state between calls,
so every weight it emits is a pure function of rows at or before that decision.

Risk policy: flat. Nothing declared, nothing engaged -- the charter's common risk unit sets the
book's scale and this candidate makes no claim on it.
