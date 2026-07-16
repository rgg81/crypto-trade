# Team 04 UTC reference 001: family decision

Date: 2026-07-16  
Candidate: `team-04-utc-reference-001`  
Family: `team-04-uncrowded-trend-carry-v1`

## Decision

**STOP the UTC family. Do not continue with UTC parameters, neighbors, ablations, or risk
controls.**

This is a family stop, not a claim that the whole team must end research. If Team 04 continues,
the permitted next action is a separately documented mechanism pivot with a new family and a new
preregistration. It is not a within-family rescue.

## Binding reason

The preregistered core requires pooled next-three-day composite-score IC above zero and positive
score IC in at least four of six folds. Both values are unavailable: the runner does not report
them and the frozen target artifact persists weights rather than the composite score. Team 04's
rule for this review treats unavailable score IC as failure. The global stop expressly forbids
later parameter, neighbor, or risk observations after a score-IC failure.

Exact score-IC decision values:

- pooled score IC: `unavailable` -> **FAIL**;
- positive-IC folds: `unavailable/6` -> **FAIL** against `>=4/6`.

## Independent qualification failure

The candidate also fails the visible positive-quarter gate:

- observed: `0.5 = 7/14`;
- required: `>= 0.55`;
- result: **FAIL**.

Thus the reference cannot qualify even if score diagnostics were later backfilled favorably.
Additional currently missing qualification fields include trial-adjusted probability, exact
regime net returns, long-bull and short-bear attribution, combined-chop return, official PnL
concentration, and neighborhood stability.

## Evidence that does not override the stop

The reference is economically interesting but non-compensatory gates control:

- annualized return `0.22961686194837383`;
- net Sharpe `1.5251401450635822`;
- doubled-cost Sharpe `1.326264500422908`;
- Calmar `1.4397252448816922`;
- maximum drawdown `0.15948658451650777`;
- four profitable folds out of six;
- four positive regime Sharpes, worst `0.7867376412555669`;
- both sleeves active on `0.680064308681672` of bars at the `0.01` threshold.

These passes cannot compensate for a causal score falsifier or the failed quarter gate. The result
is also concentrated in fold 2, and whole-window pre-cost attribution is long
`0.89658250963319441` versus short `-0.068230777377904922`; this further argues against spending
the remaining budget on local UTC tuning.

## Authorized next state

- UTC family: stopped as falsified negative research.
- Candidate: not qualified; no private-qualifier ticket.
- UTC diagnostics, coarse cells, schedule/portfolio cells, neighbors, and risk factorial: do not
  run.
- Team 04: may either record DNF or use a separately documented mechanism pivot under the common
  cumulative budget and public maximum of two pivots. A pivot must not reuse UTC parameter tuning
  as a purported new mechanism.

This document is a Team 04 local review decision only; it does not change organizer-owned state or
append-only ledgers.
