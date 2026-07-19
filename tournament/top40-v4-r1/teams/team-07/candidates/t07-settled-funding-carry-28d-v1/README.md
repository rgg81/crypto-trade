# Team 07 settled-funding carry baseline

This candidate estimates each eligible contract's daily funding rate from already settled events.
It infers event cadence from past timestamps, checks event coverage and staleness, and combines robust
short and long funding windows. The long sleeve owns the lowest-rate names and the short sleeve owns
the highest-rate names. The complete proposed book must have strictly positive expected carry.

Completed market-residual returns do not choose the carry sign. They apply a bounded continuous
discount when a long is falling or a short is rising. This is a crash-protection ablation target,
not a categorical market router. Funding rates are capped before robust estimation, and no basis or
spot series is synthesized.

Daily cohorts are held in a three-vintage book, keeping exposure across settlement events while
reducing rank-replacement turnover. A day without a new valid cohort adds no sleeve but allows live
vintages to age normally. The book is broad, low gross and fail-closed on an exposure-limit failure.

The mechanism is falsified if price losses consume carry, the continuous protection adds no value,
funding cadence sensitivity dominates, or stressed execution costs make the complete book
nonpositive.
