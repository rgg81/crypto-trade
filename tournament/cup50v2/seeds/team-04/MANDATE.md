# team-04 — regime-allocated-ensemble

**Objective.** Allocate across simple sleeves according to a causal read of the market state.

## Thesis

No single mechanism is all-weather: trend earns in directional markets and bleeds in chop, carry earns while positioning is calm and gives it all back in a cascade, defensive books lag in euphoria. If the market state can be identified from information available before the decision, the allocation across sleeves is itself the strategy. The lane's hazard is that a regime map fitted to a sample is a lookahead in disguise.

## Directions worth testing

- Keep each sleeve simple enough that its behaviour is attributable; this lane is about the allocation, not about a better trend signal.
- The regime read must use only closed bars, and its own parameters count as declared dimensions.
- An allocation that adapts online to sleeve performance is a legitimate direction, and a harder one to keep causal.

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
