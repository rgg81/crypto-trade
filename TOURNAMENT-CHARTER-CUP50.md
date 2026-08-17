# CUP-50 — Generalization-First Binance Futures Tournament

## Immutable scope

CUP-50 is a new namespace. Earlier tournament strategies, fitted artifacts, parameters, rankings,
results, and performance-derived conclusions are inadmissible. Neutral infrastructure and
checksum-verified raw Binance archive bytes may be reused. All twelve lanes are scored; there is no
performance qualification or finalist cut. A missing, leaking, noncausal, mutated, or
candidate-crashed entry is a permanent DNF with score zero and is not replaced.

Historical OOS is exactly `[2024-02-01T00:00:00Z, 2026-08-01T00:00:00Z)`. The replay begins at the
re-derived first full Top-50 boundary, frozen as `2021-03-15T00:00:00Z`, and carries membership,
strategy state, positions, common-risk calibration, and policy state continuously. Only intervals
whose left boundary is in OOS are scored.

## Universe and data

At every Monday 00:00 UTC, select exactly the first 50 eligible Binance USD-M, USDT-quoted and
USDT-margined perpetuals by the median of the prior 180 complete UTC days of USDT quote volume.
The boundary day is excluded, a complete day contains exactly the canonical 00/08/16 UTC 8-hour
bars, volume ties break lexicographically, and there is no hysteresis. Native-crypto classification
is applied before ranking; stablecoins, leveraged tokens, metals, commodities, TradFi, equities,
funds, indexes, FX, and unknowns fail closed. Archived bars, not current onboard dates, establish
historical listing and relisting episodes.

Selection never consults future-week bars, marks, or funding, and a selected name is never
substituted. If checksum-verified lower-interval transaction archives prove that a selected
contract ceased trading before a later canonical boundary, it remains in the weekly roster but is
causally non-executable from that boundary. A position held into the boundary is force-settled at
the preceding verified transaction-bar close with the ordinary per-side cost multiplier and no
participation cap, and cannot reopen while unavailable. Every such interval is frozen in the
pre-activation organizer audit; all other missing execution coverage fails readiness. Bars are
bounded by open time and are strictly before the endpoint. Terminal marks and funding through
2026-08-01 00:00 UTC are required. For every historical member, execution coverage continues from
its first membership through every later positive-activity transaction interval, even after a
roster exit, because participation-limited positions may remain carried. Checksum-bound hourly
marks value variable-frequency funding at each actual settlement; multiple settlements inside one
8-hour holding interval are summed, while a verified monthly event ledger with no row proves zero
funding for that interval. IS and sealed snapshots are physically separate,
checksum-bound, and censor every sealed-only symbol, roster, summary, cache, and metadata fact
from the team-visible side.

## Interface and execution

`DecisionContextV2` exposes only current-eligible-symbol bars from the trailing 180 complete UTC
days with actual close time strictly before the decision, funding from the same trailing window
strictly before the decision, causal auxiliary data, and current eligible symbols. It exposes no
transaction opens, execution marks, fills, costs, positions, equity, or PnL. A strategy is built by
`build_strategy()` and returns signed target weights, `{}` to flatten, or `None` to hold.

Targets decided at `t` fill at the transaction open at `t`. Funding belongs to `(t, t+8h]`, so a
settlement at OOS start is IS and the settlement at 2026-08-01 00:00 UTC is in the last July
interval. Fee is 5 bps and slippage 2.5 bps per side, independently at 1x/2x/3x cost. Gross and
absolute net targets are capped at 1.0, symbols at 0.20, and participation is capped at 0.001.
Market drift or a partial fill can leave the carried book temporarily above a target cap when the
participation ceiling prevents immediate deleveraging. The evaluator applies all remaining bar
capacity toward the capped book at every boundary; this organizer-owned execution shortfall is not
a candidate failure. The common risk unit targets 10% annual volatility causally from 90 trailing
days. Team volatility targeting is forbidden. Organizer-owned unavailability settlement is
applied identically to every lane and cost run and cannot be influenced by a strategy.

## Research field

The independent lanes are slow trend; breakout trend; volume-confirmed trend; residual
cross-sectional momentum; liquidity-shock reversal; defensive/low-risk selection; funding carry;
funding-crowding reversal; taker-flow pressure; relative-value convergence; calendar/settlement
seasonality; and a preregistered simple regime ensemble.

Each team has at most 12 promoteable IS-feedback trials and no minimum. Every trial pre-binds
source, parameters, risk policy, seed, data/config/scorer hashes, and purpose. Preregistered
ablations and mechanism falsifiers are uncharged only when permanently non-promoteable. Nomination
binds the source bundle and generated numeric neighbourhood before any official neighbourhood
result is visible. Neighbourhood cardinalities and transforms are implemented exclusively in
`crypto_trade.cup50.neighbourhood`.

## Frozen score

The five folds are Feb–Aug 2024, Aug 2024–Feb 2025, Feb–Aug 2025, Aug 2025–Feb 2026, and Feb–Aug
2026. For each point/window/cost, compute

`g = 365/n Σlog(1+r_net)`, drawdown `D`, annual gross volatility `v`, active-day fraction `a`,
`u=min(1,v/.10,a/.50)`, and top-five absolute gross-day share `h` (one for a flat path). Then

`x = g - .50D - .10(1-u) - .05 max(0,(h-.25)/.75)` and
`q = 50(1+tanh(x/.10))` in `[0,100]`.

Cost score is `.20q1 + .30q2 + .50q3`. Sort fold scores ascending and compute
`G=.40C1+.25C2+.20C3+.10C4+.05C5`. Compute the cost score `A` on the whole OOS path and
`P=.85G+.15A`. For K neighbourhood points, `Plow` is sorted position `ceil(K/4)` (one-indexed) and
`S=.50 median(P)+.25 Plow+.25 Pcentre`. Failed candidate cells are zero; organizer failures pause.
There are no return, Sharpe, drawdown, activity, turnover, or trade gates.

Valid entries rank before DNF, then by higher S, Plow, minimum point, centre, centre worst-fold 3x,
lower centre 3x drawdown, lower turnover, bundle SHA-256, and team ID. Score fields use decimal
round-half-even at 1e-6.

## Custody, observation, and paper

Activation binds the charter/config, transitive evaluator path, CLI, dependency lock, pure-crypto
audit, data manifests, scorer, test transcript, clean commit, and content-addressed sandbox image.
Acquisition, sealed data, private universe artifacts, caches, and reports are quarantined before
research. A material policy defect normally requires a new tournament version. The initial CUP-50
release was invalidated before any sealed candidate read after an organizer-owned
participation/exposure feasibility defect disqualified every IS trial. At the owner's direction,
that failed release remains preserved as evidence and CUP-50 is remediated in place without
changing any candidate source, parameters, seed, or nomination.
The first remediation activation was likewise preserved before any sealed read when a full IS
candidate exposed that execution coverage had incorrectly stopped at roster exit. Its partial IS
trial evidence is non-scoring; remediation remains in the same owner-directed CUP-50 lineage.

All twelve dispositions and the observation order freeze before sealed restoration. A durable
batch marker precedes the first sealed read and every point has durable start/terminal records. An
interrupted candidate point is terminal zero and cannot be retried. No team score or progress is
released during observation. Complete point evidence is staged privately, integrity-reviewed,
bundle-hashed, and the leaderboard is published atomically.

The winning centre launches on the first canonical 8-hour boundary strictly after release, after
exact non-terminal state reconstruction. It uses public data for at least 365 days, weekly dynamic
Top-50 membership, append-only cache generations, parity checks, watchdog, healthcheck, and digest.
Any strategy change starts a new lineage.
