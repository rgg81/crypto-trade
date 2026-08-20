# team-07 — taker-flow-pressure

**Objective.** Follow sustained aggression in the order flow, and fade it when price stops responding.

## Thesis

Taker buy volume is the part of the tape that crossed the spread to get filled: it is either informed or reflexive, and both continue for days. The refinement that matters is absorption — when persistent buying meets a price that will not rise, the flow is being absorbed by a larger seller and the imbalance is a signal to fade rather than follow.

## Directions worth testing

- Combine a fast and a slow flow window; they answer different questions.
- Flow relative to price response is more informative than flow alone.
- Trade size, inferable from volume and trade count, distinguishes retail churn from size.

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
