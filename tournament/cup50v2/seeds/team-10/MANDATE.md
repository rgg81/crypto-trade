# team-10 — attention-flow

**Objective.** Trade the migration of retail attention between coins.

## Thesis

Crypto retail attention is a scarce resource that rotates: a name's share of total volume rises as it becomes the story, and the rotation is slow enough to trade. Rising share tends to precede continuation over weeks and exhaustion over months, so the sign of the trade depends on the horizon over which attention is measured.

## Directions worth testing

- Share of cross-sectional volume is the measure, not raw volume, which is dominated by market conditions.
- Trade count share and volume share disagree in an informative way.
- Attention that arrives without price confirmation is a different state from attention that follows price.

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
