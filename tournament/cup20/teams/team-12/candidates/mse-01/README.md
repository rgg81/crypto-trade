# team-12 / mse-01

Nominee: the four-sleeve preregistered ensemble.

All four sleeves (CARRY, TREND, LOWRISK, FLOW) active, combined by the preregistered
inverse-volatility rule. This is the candidate the lane is about.

## Sleeves

| Sleeve | Causal base | Construction |
|---|---|---|
| CARRY | the perpetual funding mechanism moves cash from the crowded side to the uncrowded side | cross-sectional rank of trailing mean funding rate, sign flipped |
| TREND | information diffuses slowly across a fragmented 24/7 retail base, and leverage makes the diffusion reflexive | per-coin time-series momentum, volatility-scaled, three horizons; net exposure free |
| LOWRISK | leverage-constrained and lottery-seeking participants overpay for the wild names | cross-sectional rank of trailing drawdown depth, sign flipped |
| FLOW | aggressive, price-insensitive demand leaves a persistent footprint in the buy/sell split of traded volume | cross-sectional rank of trailing taker-buy share |

## The preregistered combination rule

At every decision boundary each sleeve emits a unit-gross weight vector. Sleeve k contributes that
vector times 1/sigma_k(t), where sigma_k(t) is the sample standard deviation (ddof=1) of sleeve k's
own past-only proxy return series over the most recent RISK_PARITY_BARS observations attributed to
boundaries strictly before t. The proxy return attributed to boundary g is the sleeve's own
unit-gross vector formed at boundary g-1 applied to the close-to-close simple return of the bar that
closed at g; no costs, no funding, no leverage. Before RISK_PARITY_BARS observations exist, or if
sigma_k(t) is not finite and strictly positive, the multiplier is 1. The book is the plain sum of the
scaled sleeve vectors, returned unnormalised. No other sleeve-level multiplier, tilt, cap, floor,
sign flip, correlation term or performance-conditioned term is applied anywhere.

Naive inverse volatility rather than a full equal-risk-contribution solve, deliberately: the
correlation matrix is the channel through which a combination would learn from the answer.

## Risk policy

Flat. Nothing declared, nothing enabled; `volatility_target.enabled` is `false`
(charter amendment A3). Scale belongs to the organiser's common risk unit; shape belongs to
the signal.
