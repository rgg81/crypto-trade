# team-09 — cluster-relative-reversal

**Objective.** Fade short-term dislocation relative to a name's own peer group.

## Thesis

One-week reversal is strong in altcoins, but a large part of any name's weekly move is its sector and the market. Fading the raw move is therefore mostly fading the market, which is a different and worse trade. Measuring dislocation relative to a cluster of correlated peers isolates the part that is idiosyncratic, and that is the part that reverts.

## Directions worth testing

- Clusters must be re-derived periodically from returns, and the clustering itself must be deterministic given the seed.
- Reversal is stronger when cross-sectional dispersion is high; conditioning on it is a legitimate direction.
- Volume confirmation separates a laggard from a name being repriced.

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
