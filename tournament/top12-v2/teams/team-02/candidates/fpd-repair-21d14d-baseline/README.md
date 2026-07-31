# FPD repair 21d/14d baseline

This baseline tests `funding-price-dislocation-repair`. At each Monday 00:00 UTC boundary, it
measures the log displacement between the latest complete 8h close and the close at least 21 days
earlier. Funding pressure is the mean of settlements in the trailing 14 days, strictly before the
decision boundary.

A symbol is eligible for a repair position only when funding and price displacement have opposite
signs. Small price moves and weak funding pressure are ignored. The signal fades the price move:
negative displacement with positive funding is a long repair, while positive displacement with
negative funding is a short repair. Hyperbolic-tangent transforms bound both feature contributions.
Funding-price agreement is a veto and never creates a position.

The book takes the three strongest eligible names on each side, requires at least two per side,
equal-weights each side to 50% gross, and otherwise goes flat. Symbol ordering resolves ties. The
weekly schedule, breadth requirement, 20% one-way turnover limit, 18% volatility target, and
drawdown brakes are intended to keep turnover and concentration moderate. Missing or insufficient
causal inputs result in no signal; supplied inputs are never mutated.

The thesis is falsified if disagreement-conditioned repair is not positive after base costs, is
materially one-sided between long and short states, or does not improve on the preregistered
agreement-state veto control across development folds.
