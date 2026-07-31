# Top-12 V1 tournament charter

Status: pre-activation authority

Tournament: `quant-portfolio-blind-top12-v1`

## 1. Objective

Top-12 V1 is a two-round, twelve-team, pure-crypto model-building tournament. Round 1 is a
transparent in-sample research league. Only robust IS finalists advance. Round 2 is a single
frozen historical championship over 2024-07-01 through 2026-06-30. Exact strategies, risk
policies, dependencies, data authority, evaluator, membership rule, and ensemble weights are
frozen before any Round-2 observation.

This tournament has a new authority, journal, report namespace, candidate population, and weekly
Top-12 membership. It inherits no candidate, score, selection, or performance result from an
earlier tournament.

## 2. Evidence labels

| Layer | Interval, UTC | Permitted use |
|---|---|---|
| IS research | `[2020-08-03, 2024-07-01)` | full causal artifacts and feedback |
| Historical OOS championship | `[2024-07-01, 2026-07-01)` | one atomic retrospective release |
| Live forward | from `2026-08-03` | genuine unseen paper observation |

The historical championship is OOS with respect to a newly frozen candidate that never accessed
those rows. It is not globally pristine: the period and some unrelated prior-tournament outcomes
are already known to the organizer. It determines the Top-12 tournament winner but cannot, by
itself, authorize capital. Only the live-forward record is a genuine deployment test.

## 3. Universe and execution

The universe is recomputed at 00:00 UTC every Monday. At each boundary, eligible contracts require
180 complete UTC days of history immediately before the boundary. Eligible contracts are ranked
by the median of their 180 completed daily Binance USD-M quote-volume totals. The twelve largest
become tradable until the next boundary; ties use lexicographically smaller symbols. No current or
future volume enters a historical rank.

Only native-crypto, linear USDT perpetuals are eligible. Stablecoins, fiat proxies, leveraged
tokens, tokenized or direct TradFi, equities, funds, metals, commodities, indexes, and FX are
ineligible. Unknown or ambiguous classifications fail closed. The first valid twelve-member
boundary is 2020-08-03; earlier dates are warm-up only.

All features are causal at the decision boundary. Orders execute at the next executable open.
Funding is charged on carried positions before rebalance. The frozen base cost is 5 bps taker fee
plus 2.5 bps slippage per side. Every IS result is independently evaluated at 1x, 2x, and 3x
costs. Gross, net, symbol, and participation caps are organizer-owned and identical across teams.

## 4. Twelve independent and blind lanes

Each team owns one economic mechanism. Shared causal transforms and organizer-owned risk controls
do not create a collision; substantially equivalent alpha hypotheses, signal constructions, or
economic payoffs do. The organizer assigns and privately records disjoint mechanism fingerprints,
reviews every baseline and pivot for collision, and refuses a colliding candidate before it can
consume market-data feedback.

Teams are prior-strategy blind and cross-team blind. A team may read only the public tournament
contract, the neutral strategy API, its own lane brief and files, and organizer-returned
standardized evidence. It may not inspect any prior-tournament strategy, candidate, diary, brief,
report, result, deployment artifact, or any other Top-12 team lane. The organizer must not reveal
prior mechanism names or outcomes while coaching. Rediscovery is allowed: a genuinely independent
team is not disqualified merely because the organizer later recognizes a mechanism from an older
tournament.

A team may make one documented mechanism pivot only after its original thesis is falsified across
the mandatory research matrix. The organizer must register a collision-free pivot before its
first run. Strategy blindness is an experimental control, not a claim that independently invented
ideas can never resemble earlier work.

## 5. Round-1 research discipline

Every material trial is accepted into an append-only, hash-chained journal before market data are
opened. Acceptance consumes the trial even if execution fails, crashes, or is abandoned. A team
may consume at most twelve trials. Candidate IDs, parents, hypotheses, falsifiers, material
parameters, source archives, risk policies, mechanism fingerprints, and research tags are
immutable.

A team may nominate only after at least eight accepted trials and a completed research certificate
covering:

- a transparent baseline and exact sign inversion;
- at least three formation horizons and two rebalance or holding horizons;
- controls-off, individual-control, and combined-control ablations;
- long, short, and chop role checks;
- at least five preregistered points in the finalist's local parameter neighborhood; and
- every success, failure, pivot, and abandoned attempt.

A negative candidate is evidence, not a submission. The organizer sends RED and AMBER teams back
with a concrete diagnosis while trials remain. No team may nominate merely because its time or
compute budget is exhausted.

## 6. IS qualification

The five fixed chronological folds are 2020H2 (from August 3), 2021, 2022, 2023, and 2024H1. A
nominee must pass every conjunctive floor frozen in `tournament/top12-v1/config.toml`, including:

- full-period Sharpe, return, drawdown, and 2x/3x cost resilience;
- positive-quarter and chronological-fold breadth;
- turnover, gross-edge-density, and cost-share limits;
- bull, bear, chop, and stress behavior;
- positive long and short gross contribution;
- preregistered local-neighborhood stability; and
- trial-adjusted block-bootstrap confidence.

Aggregate performance cannot compensate for a failed hard floor. Selection uses exact unrounded
values. Among eligible nominees, ranking prefers worst-fold 2x-cost Sharpe, median-fold 2x-cost
Sharpe, trial-adjusted confidence, gross edge per turnover, lower turnover, then team ID. At most
five advance; if fewer than five qualify, only actual qualifiers advance. Floors are never lowered
and no empty slot is backfilled after historical-OOS access.

## 7. Freeze and ensemble

Each team may nominate one exact archive-backed identity. After nomination there is no repair,
withdrawal, substitution, or next-ranked replacement. The organizer closes IS at one journal head
and atomically freezes the complete ranked population and advancing identities before Round 2.

An additional reporting portfolio is frozen at the same boundary. It allocates by capped inverse
IS volatility across advancing finalists. Full-precision weights, cap algorithm, constituents,
missing-result behavior, and daily sleeve-return aggregation are fixed before Round 2. If too few
finalists exist to invest 100% without breaking the cap, the remainder starts in cash. A failed
constituent's weight remains cash and is never redistributed. The ensemble is reported beside the
individual competition and does not displace an individual winner.

## 8. Historical-OOS championship

Every selected identity receives exactly one observation. All finalist acceptances are durable
before any sealed-data access. A separate journaled start marker distinguishes an accepted but
unstarted finalist from one whose observation may have begun. Failure or interruption after that
marker is a DNF and consumes the observation; there is no retry, repair, replacement, or backfill.
Runs are serial, but no team-specific result, progress, error, timing, or completion order is
disclosed until every selected observation is terminal.

An individual is winner-eligible only when its base- and 2x-cost returns are positive, 2x-cost
Sharpe is positive, drawdown is at most 30%, and at least four of eight quarters are positive. The
official winner is the eligible candidate with highest 2x-cost Sharpe, then higher annualized base
return, lower drawdown, higher gross edge per turnover, lower turnover, and team ID. If nobody is
eligible, Top-12 V1 has no winner.

All individual packets, the ensemble packet, and the manifest are built and hash-verified
privately. One release authorization binds the complete bundle before an atomic public rename.
There is no partial publication.

## 9. Live-forward disposition

Historical winner status never implies funding. The exact winner and frozen ensemble may enter a
minimum 365-day paper observation beginning no earlier than the Monday boundary at
2026-08-03T00:00:00Z. The same causal 180-complete-day rule refreshes membership each Monday using
only data known at that boundary. This scheduled universe refresh is part of the frozen strategy,
not a model change.

No parameter, signal, risk, execution, classification, or universe-ranking change is permitted
during that declared observation. Any changed model or policy starts a new research lineage and
receives no inherited evidence.

## 10. Authority and amendments

The machine-readable config controls numerical policy. This charter controls meaning. Activation
must fail on disagreement. Before the first result, an activation record hash-binds this charter,
config, implementation, dependency lock, source-archive contract, data manifest, Top-12 ranking
reproduction, pure-crypto audit, blind-lane registry, and focused tests.

Later changes require a prospective, append-only amendment made before the affected data are
accessed. Historical evidence is never rewritten. Any strategy-blindness breach is a reportable
incident: the exposed team is quarantined, receives no further data, and may restart only under a
new identity and untouched lane if no sealed OOS data were exposed.
