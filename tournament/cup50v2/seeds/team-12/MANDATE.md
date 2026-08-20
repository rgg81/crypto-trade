# team-12 — breadth-market-state-timing

**Objective.** Time aggregate exposure from the breadth of the cross-section.

## Thesis

Breadth turns before price: the number of names participating in an advance thins out well before the index rolls over, and broadens before it recovers, because the marginal name is more sensitive to flow than the aggregate. This is the only lane whose output is primarily a net directional exposure rather than a cross-sectional book, so it is also the lane most exposed to being wrong about direction.

## Directions worth testing

- Combine several breadth measures; any single one is noisy.
- A dead zone around neutral keeps the book from trading its own noise.
- Divergence between breadth and price is the classic signal and is worth testing explicitly.

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
