# Team 11 baseline: sign-entropy transition predictability

## Thesis

Completed 8h return signs alternate between locally ordered and high-entropy
sequences. A change in conditional sign entropy can alter which direction is
likely after the current two-sign state. The candidate estimates that
state-specific next-sign expectation and removes the expectation of a matched
recent cumulative-direction and volatility state. It therefore trades the
incremental information in the entropy transition, rather than raw momentum.

The estimator uses the last 180 completed 8h returns. For every historical
observation it computes 18-sign first-order conditional entropy, its six-bar
change, a fixed three-way entropy-transition bucket, and the last two signs.
Laplace-smoothed next-sign means are compared with a direction/volatility
control mean. The residual is shrunk by state sample size and scaled by the
current entropy-transition magnitude and conditional predictability.

At 00:00 UTC only, the strategy ranks positive and negative residual scores. It
holds at most five longs and five shorts, paired in equal count and weighted at
8% per symbol. Thus requested gross exposure is at most 80%, net exposure is
zero, and each symbol is capped at 8%.

## Falsifier

Falsify the thesis if, across the mandatory formation and rebalance matrix and
the long, short, and chop role checks, the entropy-transition residual fails to
improve direction, return, or gross edge after accounting for the matched
recent-direction and volatility control, or if any apparent improvement is
unstable under sign inversion and the preregistered local neighborhood.
