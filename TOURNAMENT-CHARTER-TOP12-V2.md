# Top-12 V2 tournament charter

Status: pre-activation authority

Tournament: `quant-portfolio-blind-top12-v2`

## Objective and evidence boundaries

Twelve strategy-blind teams research distinct native-crypto mechanisms. Generalization, not the
largest backtest, is the objective. The evidence is divided before activation:

| Layer | Interval, UTC | Use and disclosure |
|---|---|---|
| Development IS | `[2020-08-03, 2023-07-01)` | causal artifacts and standardized feedback |
| Sealed IS confirmation | `[2023-07-01, 2024-07-01)` | one observation per qualified nominee; atomic release only after finalist freeze |
| Historical OOS | `[2024-07-01, 2026-07-01)` | one observation per finalist; one atomic final release |
| Live forward | from `2026-08-03` | unchanged paper model for at least 365 days |

Historical OOS is candidate-relative, not globally pristine: the organizer knows unrelated prior
results from this era. A mechanism previously observed on this exact OOS is therefore ineligible,
even if a blind team independently rediscovers it. The organizer enforces that rule without
revealing any prior strategy or result. Historical success never authorizes capital.

## Universe and execution

At 00:00 UTC each Monday, eligible contracts require 180 complete preceding UTC days. Native-
crypto Binance USD-M linear USDT perpetuals are ranked by median daily quote volume over those
days; the first twelve trade until the next boundary, with symbol as deterministic tie-break.
Stablecoins, fiat proxies, leveraged tokens, tokenized or direct TradFi, equities, funds, metals,
commodities, indexes, FX, and ambiguous classifications are ineligible.

Features are causal at the decision boundary. Orders fill at the next executable open. Funding is
charged on carried positions before rebalance. Base costs are 5 bps taker fee plus 2.5 bps
slippage per side. The organizer independently evaluates 1x, 2x, and 3x costs under identical
gross, net, symbol, and participation caps.

## Blind and collision-free lanes

Each team may read only this charter, the neutral API, the isolation contract, its private brief
and lane, and its own standardized IS evidence. Prior strategies, results, reports, git history,
other team lanes, the organizer registry, sealed windows, and private lifecycle state are
forbidden. The organizer assigns twelve disjoint economic mechanisms and rejects collisions or
known OOS-tested families without identifying the conflicting strategy. One prospective pivot is
allowed only after the original thesis is falsified and the organizer registers a collision-free
replacement before market access.

## Development discipline

Every trial is preregistered and hash-journaled before data access. A failure, crash, or abandoned
accepted run consumes one of sixteen trials. Trials 1-8 must complete baseline, exact sign
inversion, formation and rebalance grids, control ablations, and role checks. Trials 9-13 are a
protected, preregistered five-point local neighborhood (center and axial perturbations). Trials
14-16 are optional narrow repairs and must be labeled prospectively. Nomination or retirement
requires at least thirteen accepted trials and a certificate covering every accepted attempt.

## Development qualification

Six fixed nonoverlapping folds are 2020H2 (from August 3), 2021H1, 2021H2, 2022H1, 2022H2, and
2023H1. Every numerical floor in `tournament/top12-v2/config.toml` is conjunctive. These include
return, Sharpe, drawdown, 2x/3x costs, positive quarters and folds, worst and median fold Sharpe,
turnover, gross edge density, cost share, regime and long/short breadth, concentration,
trial-adjusted confidence, and local-neighborhood stability. Floors are never lowered and empty
slots are never backfilled.

## Sealed confirmation and finalist freeze

After all lanes nominate or retire, all qualified identities are frozen and batch-accepted before
the confirmation snapshot opens. Runs are serial. A start marker consumes the sole observation;
interruption after it is a DNF. There is no feedback, retry, repair, withdrawal, substitution, or
replacement. Only candidates passing all confirmation gates are rankable. Ranking maximizes the
weaker of confirmation 2x Sharpe and development median-fold 2x Sharpe, then confirmation 2x
Sharpe, development worst-fold 2x Sharpe, confirmation return, and team ID. At most four advance.
If nobody passes, there are no finalists. The complete confirmation bundle is published atomically
only after the finalist identities and development-only ensemble weights are frozen.

## Historical OOS championship

Every finalist identity is archive-backed and batch-accepted before OOS access. Runs are serial,
with one start and one terminal event; a started failure is a DNF and cannot be retried. No
candidate-specific progress or result is disclosed until all observations are terminal. Winner
eligibility requires base annualized return above 3%, 2x return above 1.5%, 2x Sharpe above 0.50,
drawdown at most 25%, and at least five positive quarters. Ranking then follows frozen exact-value
rules. If nobody passes, there is no winner.

The reporting ensemble uses capped inverse development-IS volatility. Missing sleeves remain cash;
weights are never redistributed and the ensemble cannot win. Individual packets, ensemble, and
manifest are privately hash-verified before one journal authorization and atomic public rename.

## Compute, activation, and amendments

Result commands are serialized and refuse to run with affinity wider than two CPUs. Activation
hash-binds this charter, config, implementation, dependencies, data and universe authorities,
private mechanism registry, team briefs, and focused tests. Later changes require a prospective
append-only amendment before affected data access. Evidence is never rewritten. A blindness breach
quarantines the exposed lane; exposure to sealed data permanently ends that lineage.
