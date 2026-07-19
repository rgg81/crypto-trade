# Top-40 V4 robustness policy

Robustness is qualification evidence, not decorative diagnostics.

## Chronological breadth

The organizer computes five fixed nonoverlapping folds. At least four must have positive base and
2x-cost cumulative return. Ranking begins with the exact worst and median fold 2x-cost Sharpe.

## Trial adjustment

Daily returns use a 2,000-sample circular block bootstrap with fixed 10-day blocks. If `B` is
the fraction of bootstrap arithmetic means above zero and `T` is the team's complete accepted-trial
count at nomination, trial-adjusted confidence is `max(0, min(1, 1 - T*(1-B)))`. It must be at
least 0.90. The unadjusted probability and trial count are always disclosed.

## Neighborhood stability

The finalist belongs to a neighborhood declared before its first point is evaluated. At least five
distinct successful coordinate vectors must vary every declared neighborhood coordinate both upward
and downward around the finalist. Every coordinate must map to an identically named numeric material
parameter. At least 70% must have positive annualized return and 2x-cost Sharpe; median 2x-cost Sharpe
must be at least 0.50.

## Cost and turnover

Base annualized one-way turnover may not exceed 20 times equity. Gross arithmetic edge must be at
least 50 basis points per unit of one-way turnover. Base fees and slippage may consume at most 25%
of positive gross PnL. Independently rerun 2x Sharpe must be at least 0.75 and 3x Sharpe positive.

## Role and regime breadth

Long and short gross PnL must each be positive over IS. Full-portfolio Sharpe must be positive in
bull, bear and chop. Stress Sharpe must be at least -0.50. A flat sleeve is acceptable only when the
candidate does not claim that role; a nominated combined strategy must satisfy all declared roles.

## Return concentration

The five largest absolute daily returns may contribute no more than 35% of total absolute daily
return. No chronological fold may contribute more than 60% of total positive arithmetic PnL. These
checks use every scheduled day, including flat days.
