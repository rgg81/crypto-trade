# team-06 — defensive-quality-neutral

**Objective.** Own resilience and fund it by shorting fragility, with the market factor removed.

## Thesis

In crypto the low-volatility anomaly runs backwards during euphoria: the most fragile, least liquid, most retail-fragmented names outperform violently in a mania and give it all back afterwards. A quality book that is long resilience and short fragility should therefore earn in bear and chop and lose in a melt-up, which is exactly a regime exposure the score will price. Neutralising the market factor is what separates this from a short-beta bet.

## Directions worth testing

- Define quality from more than volatility: liquidity depth, flow fragmentation, and stability of activity are all candidates.
- Beta-neutralise explicitly, or the lane becomes a market-direction bet wearing a factor name.
- Consider whether the short leg should be conditional on the market state.

## What the organizer owns

- fills at the transaction open, fees, slippage, funding and delisting settlement
- weekly Top-50 membership and eligibility
- the common risk unit that sizes every book to a common volatility target
- gross, net, per-symbol and participation caps

## Forbidden

- reading any earlier tournament's directory, results, parameters or conclusions
- any date literal after the in-sample end
- team-level volatility targeting; the organizer owns book size
- pre-fitted objects, cached data, or any state not reconstructed from the streamed context
- reading another team's workspace, the sealed data, or any organizer-private surface

## Deliverable

one frozen candidate: strategy.py exposing build_strategy(), parameters.json declaring a centre and at most five tunable dimensions, risk-declaration.json, and RESEARCH-CERTIFICATE.md

## Scored on

worst fold, worst regime and the whole path, at 1x/2x/3x cost, across the declared neighbourhood rather than the nominated point alone
