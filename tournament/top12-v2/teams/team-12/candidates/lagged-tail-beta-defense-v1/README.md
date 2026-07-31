# lagged-tail-beta-defense-v1

Baseline candidate for `tail-concentration-defensive-rotation`.

## Economic mechanism

Crypto selloffs do not always distribute losses evenly. When losses become concentrated in a
small part of the cross-section, the affected contracts can reveal fragile exposure to the next
downside episode. This candidate measures the Herfindahl concentration of cross-sectional losses,
lags and smooths that state, and uses it to weight two defensive characteristics: relative
downside beta to the cross-sectional market return and the frequency with which a contract falls
into the cross-sectional lower tail.

At the weekly boundary, the strategy ranks contracts by the resulting fragility score. It holds a
broad, dollar-neutral long sleeve of the most resilient contracts and a short sleeve of the most
fragile contracts. Gross exposure rises modestly when the lagged concentration state is high
relative to its recent history. Robust cross-sectional clipping, capped observation weights,
broad sleeves, and a small rank tilt keep isolated extreme returns and idiosyncratic-volatility
lottery exposure from dominating the portfolio.

## Causality and turnover

Only 8-hour bars complete by the decision boundary are converted to UTC daily closes. The
concentration state is lagged by one daily observation before it can weight a return. Targets are
computed only at Monday 00:00 UTC and execute centrally at the next executable open. Weekly
rotation, an 84-day formation window, a 21-day state smoother, diversified sleeves, and the
organizer-enforced one-way turnover limit make the design moderately low turnover.

Missing or insufficient history produces a flat target at a scheduled rebalance. Outside the
scheduled boundary the strategy returns `None`, preserving current quantities subject to central
exits and risk reductions. Funding, fills, costs, eligibility, participation, and all risk-policy
actions remain owned by the organizer.

## Preregistered falsifier

The thesis is rejected if the resilient-minus-fragile spread does not retain a consistent sign
across development folds, if doubled costs consume its gross edge, or if exact sign inversion is
not materially worse. A result driven by one tail event, one contract, or unstable sleeve churn
also falsifies the intended mechanism rather than motivating an ex-post reinterpretation.
