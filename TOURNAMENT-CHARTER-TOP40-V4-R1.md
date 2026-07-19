# Top-40 V4-R1 tournament charter

Status: pre-activation authority

Tournament: `quant-portfolio-blind-top40-v4-r1`

## 1. Objective

Top-40 V4-R1 is a two-round, twelve-team, pure-crypto model-building tournament. Round 1 is a
transparent in-sample research league. Only the strongest robust IS finalists advance. Round 2 is
a single frozen historical championship over 2024-07-01 through 2026-06-30. The exact strategies,
risk policies, dependencies, data authority, evaluator and ensemble weights are frozen before any
Round-2 observation.

V4-R1 does not rewrite any earlier result. The aborted first V4 activation and all V1–V3
namespaces remain immutable evidence. V4-R1 starts with a new activation and empty journal and
inherits no performance observation from that infrastructure-only failure.

## 2. Evidence labels

| Layer | Interval, UTC | Permitted use |
|---|---|---|
| IS research | `[2020-02-03, 2024-07-01)` | full causal artifacts and feedback |
| Historical OOS championship | `[2024-07-01, 2026-07-01)` | one atomic retrospective release |
| Live forward | from `2026-08-01` | genuine unseen paper observation |

The historical championship is OOS with respect to a newly frozen candidate that never accessed
those rows. It is not globally pristine: the period and some prior-strategy outcomes are already
known to the organizer. It determines the V4 tournament winner but cannot, by itself, authorize
capital. Only the later live-forward record is a genuine deployment test.

## 3. Universe and execution

Only point-in-time members of the frozen, weekly reconstituted Top-40 Binance USD-M native-crypto
universe may be traded. Stablecoins, fiat proxies, leveraged tokens, tokenized or direct TradFi,
equities, funds, metals, commodities, indexes and FX are ineligible even if a perpetual contract
exists. Unknown classifications fail closed.

All features are causal at the decision boundary. Orders execute at the next executable open.
Funding is charged on carried positions before rebalance. The frozen base cost is 5 bps taker fee
plus 2.5 bps slippage per side. Every IS result is independently evaluated at 1x, 2x and 3x costs.
Gross, net, symbol and participation caps are organizer-owned and identical across teams.

## 4. Twelve independent lanes

Each team owns one economic mechanism. Shared causal transforms and risk controls do not create a
collision; copying another team's alpha does. A team may make one documented mechanism pivot only
after its original thesis is falsified across the mandatory research matrix.

1. Slow per-coin time-series momentum.
2. Fast breakout and time-series momentum.
3. Volume-confirmed time-series momentum.
4. Market-residual cross-sectional momentum.
5. Short-horizon liquidity-shock reversal.
6. Downside-risk and low-volatility selection.
7. Funding carry with crowding-crash protection.
8. Funding crowding and mean reversion.
9. Taker-flow and price-volume pressure.
10. Dynamic cointegration and relative-value convergence.
11. UTC and weekday seasonality.
12. A simple preregistered regime ensemble of causal base signals.

## 5. Round-1 research discipline

Every material trial is accepted into an append-only, hash-chained journal before market data are
opened. Acceptance consumes the trial even if execution fails, crashes or is abandoned. A team may
consume at most twelve trials. Candidate IDs, parents, hypotheses, falsifiers, material parameters,
source archives, risk policies and research tags are immutable.

A team may nominate only after at least eight accepted trials and a completed research certificate
covering:

- a transparent baseline and exact sign inversion;
- at least three formation horizons and two rebalance/holding horizons;
- controls-off, individual-control and combined-control ablations;
- long, short and chop role checks;
- at least five preregistered points in the finalist's local parameter neighborhood; and
- every success, failure, pivot and abandoned attempt.

A negative candidate is evidence, not a submission. The organizer sends RED and AMBER teams back
with a concrete diagnosis while trials remain. No team may nominate merely because its time or
compute budget is exhausted.

## 6. IS qualification

The five fixed chronological folds are 2020 (from February 3), 2021, 2022, 2023 and 2024H1. A
nominee must pass every conjunctive floor frozen in `tournament/top40-v4-r1/config.toml`, including:

- full-period Sharpe, return, drawdown and 2x/3x cost resilience;
- positive-quarter and chronological-fold breadth;
- turnover, gross-edge-density and cost-share limits;
- bull, bear, chop and stress behavior;
- positive long and short gross contribution;
- preregistered local-neighborhood stability; and
- trial-adjusted block-bootstrap confidence.

Aggregate performance cannot compensate for a failed hard floor. Selection uses exact unrounded
values. Among eligible nominees, ranking prefers worst-fold 2x-cost Sharpe, median-fold 2x-cost
Sharpe, trial-adjusted confidence, gross edge per turnover, lower turnover, then team ID. At most
five advance; if fewer than five qualify, only the actual qualifiers advance. Floors are never
lowered and no empty slot is backfilled after historical-OOS access.

## 7. Freeze and ensemble

Each team may nominate one exact archive-backed identity. After nomination there is no repair,
withdrawal, substitution or next-ranked replacement. The organizer closes IS at one journal head
and atomically freezes the complete ranked population and advancing identities before Round 2.

An additional reporting portfolio is frozen at the same boundary. It allocates by capped inverse
IS volatility across the advancing finalists. Full-precision weights, cap algorithm, constituents,
missing-result behavior and daily sleeve-return aggregation are fixed before Round 2. If too few
finalists exist to invest 100% without breaking the cap, the remainder starts in cash. A failed
constituent's weight also remains cash and is never redistributed. The ensemble is reported beside
the individual competition and does not displace an individual winner.

## 8. Historical-OOS championship

Every selected identity receives exactly one observation. All finalist acceptances are durable
before any sealed-data access. A separate journaled start marker distinguishes an accepted but
unstarted finalist from one whose observation may have begun. Failure or interruption after that
marker is a DNF and consumes the observation; there is no retry, repair, replacement or backfill.
Runs are serial, but no team-specific result, progress, error, timing or completion order is
disclosed until every selected observation is terminal.

An individual is winner-eligible only when its base- and 2x-cost returns are positive, 2x-cost
Sharpe is positive, drawdown is at most 30%, and at least four of eight quarters are positive. The
official winner is the eligible candidate with highest 2x-cost Sharpe, then higher annualized base
return, lower drawdown, higher gross edge per turnover, lower turnover and team ID. If nobody is
eligible, V4 has no winner.

All individual packets, the ensemble packet and the manifest are built and hash-verified privately.
One release authorization binds the complete bundle before an atomic public rename. There is no
partial publication.

## 9. Live-forward disposition

Historical winner status never implies funding. The exact winner and frozen ensemble may enter a
minimum 365-day paper observation beginning no earlier than 2026-08-01. No parameter, universe,
signal, risk or execution change is permitted during that declared observation. Any changed model
starts a new research lineage and receives no inherited evidence.

## 10. Authority and amendments

The machine-readable config controls numerical policy. This charter controls meaning. Activation
must fail on disagreement. Before the first result, an activation record hash-binds this charter,
config, implementation, dependency lock, source-archive contract, data authority, pure-crypto
audit and focused tests. Later changes require a prospective, append-only amendment made before
the affected data are accessed. Historical evidence is never rewritten.
