# team-05 — funding-carry-crowding-guarded

**Objective.** Receive the funding paid by crowded leverage, without standing in front of a cascade.

## Thesis

Perpetual funding is the price leveraged traders pay to hold a position, and the side paying it is the crowded one. Receiving that flow is a real premium, but it is regime-coupled rather than all-weather: the same crowding that pays well marks the positioning that liquidates violently, and the carry earned over months can be lost in days. Six prior investigations in this repository have confirmed the coupling; the lane's job is to find whether a guard changes it.

## Directions worth testing

- Extreme funding is a different state from high funding; treat the tail as a signal to stand aside, not to size up.
- The funding leg and the price leg of the trade can be separated in analysis, and should be.
- Funding term structure — how the rate is changing — may carry more than its level.

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
