# team-02 — channel-position-breakout

**Objective.** Trade departures from an established price range.

## Thesis

A range that has held for months accumulates resting orders and stop clusters on both sides. Price leaving it forces those stops and attracts momentum flow, so the exit tends to run rather than snap back. Position within the trailing range is a continuous, low-turnover way to express this: it says how close a name is to breaking out, not merely whether it has.

## Directions worth testing

- Prefer a continuous position-in-range measure to a binary breakout flag; the binary version trades every time price touches the edge.
- Consider whether a breakout against the longer trend deserves the same size as one with it.
- Range compression before the break is a candidate precondition worth testing.

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
