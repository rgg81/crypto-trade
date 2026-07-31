# Top-12 V1 robustness policy

Robustness is qualification evidence, not a decorative diagnostic.

## Chronological breadth

The organizer computes five fixed, nonoverlapping folds. At least four must have positive base and
2x-cost cumulative return. Ranking begins with exact worst and median fold 2x-cost Sharpe.

## Trial adjustment

Daily returns use a 2,000-sample circular block bootstrap with fixed 10-day blocks. If `B` is the
fraction of bootstrap arithmetic means above zero and `T` is the complete accepted-trial count,
trial-adjusted confidence is `max(0, min(1, 1 - T*(1-B)))`. It must be at least 0.90.

## Neighborhood stability

The finalist belongs to a neighborhood declared before its first point is evaluated. At least five
distinct successful coordinate vectors vary every declared coordinate both upward and downward.
At least 70% must have positive annualized return and 2x-cost Sharpe; median 2x-cost Sharpe must be
at least 0.50.

## Cost and turnover

Base annualized one-way turnover may not exceed 20 times equity. Gross arithmetic edge must be at
least 50 basis points per unit of one-way turnover. Base costs may consume at most 25% of positive
gross PnL. Independently rerun 2x Sharpe must be at least 0.75 and 3x Sharpe positive.

## Role and regime breadth

Long and short gross PnL must each be positive over IS. Full-portfolio Sharpe must be positive in
bull, bear, and chop. Stress Sharpe must be at least -0.50.

## Return concentration

The five largest absolute daily returns may contribute no more than 35% of total absolute daily
return. No fold may contribute more than 60% of total positive arithmetic PnL. Checks include flat
scheduled days.
