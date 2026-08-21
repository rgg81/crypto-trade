# CUP-50 v2 — Generalization-First Binance Top-50 Tournament, Edition II

## Purpose and scope

CUP-50 v2 looks for one thing: a book that survives bull, bear and chop. Not the highest return, not
the best single window — the mechanism whose worst market state is still worth holding. The winner
earns a six-month forward paper record, and only that record could later justify capital.

This is a new namespace. Earlier tournaments' candidate sources, parameters, rankings, results and
performance-derived conclusions are inadmissible. Neutral infrastructure and checksum-verified raw
Binance archive bytes may be reused, and are.

Every one of the twelve lanes is observed on the sealed window. A missing, leaking, non-causal,
mutated or crashed entry is a permanent DNF with score zero and is never replaced.

## What CUP-50 v2 changes, and why

Each rule below exists because of something that happened, not because it sounded prudent.

**A research phase.** CUP-50's field was twelve unchanged organizer seeds: twelve of one hundred
forty-four trials were used and no team iterated, so its leaderboard measured the regime luck of
naive starting points. Teams here get an unlimited, journaled research evaluator and twelve charged
trials, and must spend at least three before nominating.

**An ex-ante risk unit.** CUP-50 sized each book by the realised volatility of its own past returns,
which describes a position the strategy no longer holds. Its winner sat flat half of every window
and then concentrated, and ran at 23% annualised against a 10% target. The scalar now prices the
book about to be held, from the covariance of the names in it.

**A regime term.** Half-year folds mix market states, so a lane can be carried through a fold by the
kind of month it likes. Months are labelled from an equal-weight index of that week's members, and
the score prices the weakest regime directly.

**Cost weights that discriminate.** At half the weight on 3x cost, the in-sample window selected for
never trading: no CUP-50 lane was profitable at 3x, eight of twelve in-sample scores fell below
0.05, and the window could not tell lanes apart.

**Participation.** A cell that never deploys scores zero. CUP-50 paid a permanently flat path 4.74
against 0.008 for trading badly, and two lanes collected it with a lookback long enough to
disqualify every symbol.

**A qualification bar fixed in advance.** CUP-50 promised no cut, ranked all twelve on the sealed
window, then applied a top-three in-sample stage retrospectively. The winner changed, nine lanes
were reclassified after their evidence was read, and the incident record concedes the correction
cannot recreate the blindness it spent.

## Universe and data

At every Monday 00:00 UTC, the first 50 eligible Binance USD-M, USDT-quoted and USDT-margined
perpetuals by the median of the prior 180 complete UTC days of USDT quote volume. The boundary day is
excluded, a complete day holds exactly the canonical 00/08/16 UTC bars, ties break lexicographically,
and there is no hysteresis. Native-crypto classification is applied before ranking and fails closed:
stablecoins, leveraged tokens, metals, commodities, TradFi, equities, funds, indexes, FX and unknowns
are excluded. Archived bars, not current onboard dates, establish listing and relisting episodes.

Selection never consults future-week bars, marks or funding, and a selected name is never
substituted. Where checksum-verified lower-interval archives prove a selected contract stopped
trading, it stays in its weekly roster but becomes causally non-executable from that boundary; a
position held into it is force-settled at the preceding verified transaction close with ordinary
costs and no participation cap. Execution coverage continues past a roster exit for as long as a
participation-limited position may still be carried.

The replay runs continuously from **2021-03-15**. The research window is
`[2021-03-15, 2024-02-01)`; the sealed window is `[2024-02-01, 2026-08-01)`. IS and sealed snapshots
are physically separate, checksum-bound, and censor every sealed-only symbol, roster, label and
metadata fact from the team-visible side.

## Interface and execution

`DecisionContextV2` exposes bars from the trailing 365 complete days with close times strictly before
the decision, funding from the same window settled strictly before it, causal auxiliary data, and the
current eligible symbols. It exposes no transaction opens, execution marks, fills, costs, positions,
equity or PnL. A strategy is built by `build_strategy()` and returns signed target weights, `{}` to
flatten, or `None` to hold.

Targets decided at `t` fill at the transaction open at `t`. Funding belongs to `(t, t+8h]`. Fee is
5 bps and slippage 2.5 bps per side, run independently at 1x, 2x and 3x. Gross and absolute net are
capped at 1.0, per symbol at 0.20, and participation at 0.001 of the bar's quote volume. Market drift
or a partial fill can leave a carried book temporarily above a cap when the participation ceiling
prevents immediate deleveraging; the evaluator applies all remaining capacity toward the capped book
at every boundary, and this organizer-owned shortfall is not a candidate failure.

The common risk unit targets 10% annualised volatility, computed ex ante from an exponentially
weighted covariance of the intended book over bars that closed before the decision, and clamped to
[0.10, 3.00]. **Team volatility targeting is forbidden.** Teams own a book's shape; the organizer
owns its size. Note that the caps beat the unit in one direction only: a book calm enough to want
more than its ceiling is held at the ceiling.

## Research field

Twelve independent lanes: multi-horizon trend; channel-position breakout; residual cross-sectional
momentum; regime-allocated ensemble; funding carry with a crowding guard; defensive quality,
beta-neutral; taker-flow pressure; volume-shock event reversal; cluster-relative reversal;
attention flow; a walk-forward learned model; and breadth market-state timing.

Each lane receives a written mandate and an organizer seed — the lane's idea in the least clever form
that could work. A seed is a floor, not a claim: each team's first charged trial is its unmodified
seed, and the leaderboard publishes the distance between that trial and the nomination.

## Research process

Research evaluations are unlimited and every one is journaled; the count is disclosed with the
result. They run on the team-visible snapshot, where execution is approximated at the last visible
close, and they can never be nominated.

Charged trials are capped at **12** and at least **3** must be spent before nominating. The first
must be the unmodified seed. Preregistered ablations and mechanism falsifiers are uncharged, because
charging for honest self-examination is how a prior edition made its certificate unaffordable.

Every trial binds source, parameters, risk policy, seed, and the data, config and scorer digests.
A nomination binds the source bundle and the generated numeric neighbourhood before any sealed result
exists. Neighbourhood cardinalities and transforms are implemented exclusively in
`crypto_trade.cup50v2.neighbourhood`: one dimension is probed three steps out, more are probed two
steps out on every axis, and at most five may be declared.

A candidate must also declare its risk policy explicitly. Every control is either described or
recorded as "none, deliberately". A default is not a declaration.

## Falsification and integrity

At nomination the organizer runs, at no charge to the team: exact sign inversion (a book whose
opposite scores as well is an artifact, and is disqualified); future corruption at key-derived cut
points, requiring every earlier decision to be byte-identical (failure is terminal); two independent
clean runs, required to agree exactly; and a run-length-preserving spell shuffle, disclosed rather
than gated.

Team workspaces live outside the repository and are scanned before evaluation: no prior-edition
namespace, no organizer-only surface, no cached frame, no date literal after the in-sample end.
Separately, each team agent's session transcript is audited for reads it was not entitled to make.
Any finding is confirmed independently by the organizer before it disqualifies anyone, and no
performance code exists among the integrity codes — performance is never an integrity failure, and
integrity is never repaired by a score.

## Frozen score

The sealed folds are Feb–Aug 2024, Aug 2024–Feb 2025, Feb–Aug 2025, Aug 2025–Feb 2026 and
Feb–Aug 2026. For each point, window and cost, on daily-compounded net returns:

```
g = 365/n Σ log(1+r_net)      D = max drawdown      v = annualised gross volatility
a = active-day fraction       u = min(1, v/.10, a/.50)      h = top-five gross-day share
x = g − .50 D − .10 (1−u) − .05 max(0, (h−.25)/.75)
q = 50 (1 + tanh(x/.10)), and q = 0 when a < .05
C = .45 q₁ + .35 q₂ + .20 q₃
```

`G` weights fold scores sorted ascending by (.40, .25, .20, .10, .05). `R` weights the three regime
scores sorted ascending by (.50, .30, .20); a regime with fewer than 60 days in the window is dropped
and the weights renormalise. `A` is `C` over the whole window. Then

```
P = .60 G + .25 R + .15 A
S = .50 median(P) + .25 P_low + .25 P_centre,   P_low = sorted position ceil(K/4)
```

The research window is scored by the same machinery over six in-sample folds weighted
(.35, .25, .15, .12, .08, .05). Failed candidate cells score zero; organizer failures pause.

Entries rank: eligible, then observed-ineligible, then DNF; within a tier by higher S, P_low, minimum
point, centre, centre worst-fold 3x, then lower centre 3x drawdown, lower turnover, bundle SHA-256,
team id. Score fields use decimal round-half-even at 1e-6.

## Qualification and the winner

Every nominated lane is observed. A lane is **eligible** to win when its nomination's in-sample S is
at least **35** and every in-sample regime cost score of its centre is at least **15**.

Both numbers were calibrated against the measured seed field before any sealed data was opened, and
both sit inside an observed gap in that distribution rather than being chosen for roundness. The
twelve naive seeds score S from 3.0 to 47.6, with a gap between 30.1 and 40.1; their worst-regime
scores run from 0.0 to 24.3, with a gap between 11.6 and 24.3. Exactly one seed clears both today —
the regime-allocated ensemble, the lane deliberately built to be all-weather — so a nomination must
be at least as regime-robust as a balanced naive construction, and every team has twelve charged
trials to get there. This is a bar,
not a rank: in-sample position carries almost no information about sealed position — CUP-50's sealed
winner ranked ninth of twelve in sample, and CUP-20's in-sample leader lost money out of sample — but
a lane that showed no in-sample edge at all should not win on one sealed draw. Requiring the bar in
every regime is what stops a book carried by a single market state from qualifying on its average.

The winner is the highest sealed S among eligible lanes. Ineligible lanes are scored and published in
full, labelled as such. **No eligible lane means no winner**, and no desk opens.

## Custody, observation and amendment

Activation binds the charter, config, transitive evaluator path, CLI, dependency lock, pure-crypto
audit, data manifests, scorer, test transcript, a clean commit, and a content-addressed sandbox
image. Its preflight requires the twelve-seed readiness field, a clean-room workspace scan, a
sandbox isolation probe, determinism across worker counts and hash seeds, the full test suite and
the linter. The forward desk's parity smoke is a precondition of launching a desk, not of running
the field: the desk is downstream of the release and is not bound by this record, so requiring it
here would force the desk to be built before any research happened, for no gain in integrity. Acquisition, sealed data, private artifacts, caches and reports are quarantined before
research begins. Readiness requires all twelve seeds to complete a full in-sample replay at three
cost levels: CUP-50's readiness strategy was flat, exercised no carried position, roster exit or
participation limit, and three organizer defects survived into a live field.

All twelve dispositions, their qualification verdicts and the observation order freeze before sealed
restoration. The order is derived from the field-signing key, not the team numbering. A durable batch
marker precedes the first sealed read; every point has durable start and terminal records; an
interrupted candidate point is a terminal zero and cannot be retried. No score or progress is
released during observation. Evidence is staged privately, integrity-reviewed, bundle-hashed, and the
leaderboard is published atomically.

**No scoring, qualification or execution rule changes after the first sealed read.** A material
defect found later voids the edition; it is never corrected retrospectively. A defect found before
the first sealed read is fixed by a journaled amendment that re-runs every affected trial at no
charge to the team.

## Forward paper stage

Four desks launch on the first canonical 8-hour boundary strictly after release, after exact
non-terminal state reconstruction: the winner, the two next-ranked eligible lanes, and a
preregistered equal-risk ensemble of the three. Running one desk would leave the edition's outcome
resting on a ranking whose own noise floor it cannot see.

Desks use public data only, weekly dynamic Top-50 membership, append-only cache generations, parity
checks against the tournament's own evaluator, a watchdog, a healthcheck and a digest. Any strategy
change starts a new lineage.

After at least **183 official days**, capital goes to the desk with the highest official-phase 1x cell
score among those with an official drawdown at or below 20% and a score of at least 50, ties broken by
lower drawdown. If none qualifies, no capital is deployed and the edition closes without a
deployment. The tournament result never authorises capital; only the forward record can.

## Disclosed limitations

1. **The sealed window is organizer-contaminated.** The organizer has seen CUP-50's lane-level
   results on `[2024-02-01, 2026-08-01)`, and the window has been revealed in six prior editions.
   The seeds are mechanism templates written from lane theses rather than from any prior result, but
   the contamination cannot be undone by care. The forward desks are the only uncontaminated test.
2. **Agent hindsight cannot be fully policed.** A language model knows what happened in these
   markets. Date-literal scanning, preregistration, neighbourhood robustness, regime stratification
   and the forward record all reduce the exposure; none eliminates it.
3. **Two and a half years cannot finely rank survivors.** The standard error on a Sharpe estimate
   over this window is roughly ±0.7. The tournament can identify survivors; it cannot separate three
   of them. That is why four desks run forward, not one.
4. **Research evaluations approximate execution** at the last visible close. Charged trials on the
   organizer's snapshot are authoritative, and the two differ by the open-to-close gap.
5. **Organizer-side blindness during scoring remains detection, not prevention.** The transcript
   audit and the quarantine receipt record what was read; neither is an operating-system control.
6. **A calm book cannot reach the volatility target**, because the caps bind before the risk unit
   does, and a concentrated book is capped harder than a diversified one. Drawdowns across lanes are
   comparable in kind, not in scale.
