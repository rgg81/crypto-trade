# Top-40 Crypto Futures Research Tournament

This charter creates ten independent teams. Each team has one Quantitative Researcher (QR) and
one Quantitative Engineer (QE), invents one fresh strategy, and submits one frozen champion to a
common Binance USDⓈ-M perpetual-futures evaluator. The tournament inherits research discipline,
role separation, reproducibility, leakage tests, realistic costs, and constructive review from
the repository's agent methodology. It inherits **no historical signal, strategy family, result,
parameter, or portfolio construction**.

## 1. Objective

Find the strongest generalizing long/short crypto portfolio over the point-in-time Binance top 40:

- high net risk-adjusted performance in both development and the two-year public evaluation;
- useful long and short sleeves across bull, bear, chop, and stress markets;
- explicit funding, fee, slippage, turnover, fillability, and delisting accounting;
- reproducible behavior that can proceed to a post-freeze forward paper stage.

The tournament always names the highest-scoring valid submission. “Best in this tournament” and
“ready for capital” are separate conclusions.

## 2. Strategic clean room

Competitors must not inspect or copy the old portfolio research artifacts. During competition,
the following are out of bounds: `briefs-portfolio-*`, `diary-portfolio-*`, historical
`analysis/portfolio/iter_*`, `ORCHESTRATOR_BRIEF*`, `TOURNAMENT-CHARTER-MN4.md`, old tournament
reports, and `src/crypto_trade/portfolio/strategy.py`. The last file imports historical strategy
code and is not neutral infrastructure.

Competitors may read this charter, `tournament/top40/config.toml`, their dedicated Top-40 agent
definition, generic statistical methodology references, official Binance documentation, and the
new `src/crypto_trade/tournament/` evaluator. The organizer has distilled all three local quant
skill files into `tournament/top40/METHODOLOGY-DISTILLATION.md`: their feature, regime, and
walk-forward controls are mandatory, while their illustrative indicators, strategy mappings, and
trade examples are explicitly excluded. No seeded idea menu exists. Teams cannot read one
another's namespaces before freeze.

Each QR must sign a provenance statement: the mechanism was independently proposed for this
tournament and was not selected from a prior branch result.

## 3. Time windows and honest terminology

- **In-sample:** `[2020-02-03, 2024-07-01)` UTC. February 3 is the earliest Monday for which
  official Binance monthly USD-M archives provide the required 30 complete prior trading days;
  the point-in-time universe contains fewer than 40 contracts while the venue is young.
- **Public OOS:** `[2024-07-01, 2026-07-01)` UTC, exactly two years.
- **Quarantined gap:** `[2026-07-01, winner-freeze-next-8h-boundary)` UTC; never backfilled as
  untouched evidence.
- **Forward paper:** begins at the first 8h boundary after the winner freezes and accumulates only
  prospectively from that point.

Teams may inspect and iterate on the public OOS, as requested. Therefore it is not statistically
sealed and must never be presented as untouched proof. Every material public-OOS evaluation goes
into `experiments.jsonl`; the submitted `trial_count` includes abandoned and offline candidates.
Nested walk-forward/CPCV within IS supplies internal validation. The forward-paper period is the
first genuinely untouched temporal evidence.

The team ledger is append-only. A candidate must have a `registered` event before execution and a
later `result` event; both follow `tournament/top40/templates/experiment-event.schema.json`.
Registration declares whether a public-OOS view is requested. In parallel, the organizer owns
`tournament/top40/organizer_research_journal.jsonl`: `init-teams` creates its canonical genesis,
the Phase-0 common commit and `run_state.json` anchor that genesis, and every later reservation and
result extends a SHA-256 hash chain. The finalizer verifies both ledgers, their strict append-only
Git histories, event ordering, compute totals, deadline, trial count, and the public-OOS budget.

Full evaluator access to public OOS is possible only through `run-team TEAM_ID --candidate-id ID`.
The organizer write-ahead reserves the pending, OOS-requesting registration in the hash-chain
journal and then projects it into `run_state.json` before execution. The reservation binds the exact registration bytes,
complete team-tree fingerprint, ledger bytes, Git/team-tree identity, seed, evaluator, config, and
data manifest. After the attempt, the organizer measures CPU/wall time and automatically appends
canonical status, metrics, artifact hashes, and the exact canonical team-result bytes to the
organizer journal before appending those bytes to the team ledger and projecting `run_state.json`.
Thus the journal is a write-ahead authority, while the ledger and state are recoverable
projections. After a process interruption, run `recover-research-accounting`; it accepts only a
valid journal extension of the state anchor, rejects divergent ledger bytes, and appends only the
exact result bytes already hash-bound in that extension. A recovered reservation whose evaluator
did not finish must be explicitly consumed with `close-interrupted-run TEAM_ID CANDIDATE_ID`; its
failed result charges wall time from reservation through closure and cannot be replayed or freed.
Only one reservation per team may remain open. Failures consume a view, a candidate cannot be
replayed, and the fourth reservation is rejected. Before each later run—and always before
freeze—the changed journal, `run_state.json`, team ledger, and run outputs are committed as an
append-only extension.

## 4. Common Binance data contract

Signals, labels, universe selection, and execution use only public Binance data plus deterministic
calendar fields. Freeze one checksummed snapshot for every team. Prefer the official
[Binance public archives](https://github.com/binance/binance-public-data); record archive URL,
checksum, download time, and parser version. Snapshot current
[`exchangeInfo`](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data#exchange-information)
for contract identity and filters, while disclosing that Binance does not publish a complete
point-in-time history of old filter values.

Permitted data include transaction klines, mark/index/premium klines, funding-rate history, and
other public Binance series with adequate official historical coverage. A series whose public API
retains only recent history cannot be backfilled by another venue or vendor. Transaction prices
model fills; mark prices model funding and risk. Candle data cannot justify free maker fills,
queue priority, or exact liquidation claims.

When an executable-member funding month is absent from the checksummed monthly archive catalog,
the builder may query only that UTC month from Binance's official USD-M
`/fapi/v1/fundingRate` endpoint. It always refetches and freezes every deterministic response page
with exact parameters, retrieval time, canonical bytes, and a local SHA-256. Binance supplies no
upstream checksum sidecar for these REST responses and may revise API history; this limitation is
published separately from the archive inputs, which continue to require official SHA-256
sidecars. Missing or inconsistent REST coverage fails the whole snapshot.

When a checksummed monthly `markPriceKlines` archive omits an exact required hour, the builder next
probes Binance's deterministic daily `markPriceKlines` object for that UTC date and accepts it only
with its official SHA-256 sidecar. Only if the daily checksum object is absent or that valid daily
ZIP lacks the hour does it request the single exact hour from Binance's official USD-M
`/fapi/v1/markPriceKlines`; that response is always refetched, retained canonically, and bound to
the gapped monthly archive. Offline verification reparses every retained monthly and daily ZIP and
partitions each required hour into exactly one monthly, daily, or REST source. It never
interpolates or substitutes transaction price. Mark REST responses share the
no-upstream-checksum/revision limitation above.

Transaction bars before a symbol's first Top-40 admission remain visible as past-only research
history but are non-executable, so the builder neither requires nor invents a risk mark for them.
Funding intervals are derived from the complete adjacent-event history before pre-admission
cashflows are removed. From first admission onward every transaction boundary remains mark-required,
including after a later weekly removal while participation-limited liquidation can continue.

Actual funding rows drive cashflows; never assume an eight-hour schedule. At a funding timestamp:

`funding_pnl = -signed_position_notional * funding_rate`

Positive funding is paid by longs and received by shorts. Funding itself is not doubled in the
2×-cost stress; fees and slippage are. When funding and a rebalance share a timestamp, funding is
charged to the position carried into that timestamp, then the next-open rebalance executes.

## 5. Point-in-time Top-40 universe

Use Binance USDⓈ-M linear USDT perpetual crypto contracts only. Exclude stablecoin bases, leveraged
tokens, delivery contracts, and non-crypto underlyings.

Reconstitute Monday at 00:00 UTC. For each eligible contract, sum quote volume by completed UTC
date, take the median over the prior 30 complete days, and rank descending. Require 30 observed
prior dates and an observation on the immediately preceding date. Select at most 40, resolving
ties by symbol. Never start from today's survivors. Historical delisted names remain eligible
before their last executable data. Their last-bar close exit obeys the same remaining participation
capacity as every other execution. If a disappearing contract still has residual quantity after
that capped exit, the evaluator records an explicit adverse full-notional settlement loss rather
than inventing unlimited close liquidity. Positions still open only because the tournament horizon
ends are marked and reported as unresolved, not given that delisting haircut.

A strategy may hold fewer than 40 names but may not hold an ineligible name. Membership changes
are ordinary trades and incur turnover, fee, and slippage.

## 6. Common execution and risk contract

The base data cadence is 8h; teams may emit slower targets. The central evaluator, never team code,
does the following:

1. Give the strategy only candles closed by decision time and funding rows published earlier.
2. Accept signed target weights only through `TargetStrategy.target_weights`. Returning a mapping
   is an explicit rebalance (`{}` means flat); returning `None` holds current quantities until the
   next instruction. Holds never bypass membership exits, delisting exits, participation limits,
   or central exposure reductions.
3. Fill at the next bar open, using transaction-price data.
4. Cap fills at 0.10% of prior 24h quote volume; carry any unfilled target gap as unfilled.
5. Charge VIP-0 taker fee 5 bps plus 2.5 bps conservative slippage per executed side.
6. Apply exact historical funding events to the position held at each timestamp.
7. Attempt a participation-capped exit at a disappearing contract's last executable bar with
   normal costs, then conservatively settle any unfilled delisting residual as described above.
8. Re-run from scratch at 2× fee and slippage.

If marked holdings drift beyond a common exposure cap between slower strategy decisions, the
evaluator requests an immediate scale-down, records a `risk_reduction` market event, and charges
ordinary fee and slippage. It shares the same remaining participation budget as strategy orders;
any unfilled reduction and continuing cap breach are recorded rather than granted fictitious
liquidity. Risk reduction is never a free implicit rebalance.

Common capital is 100,000 USDT. Gross exposure is capped at 1.0× equity, absolute net exposure at
0.25×, and a symbol at 0.10×. The unlevered gross cap intentionally avoids pretending that public
bar data contains complete historical margin-tier and liquidation mechanics. The instruments are
real futures, and both long and short targets are required, but no submission receives points for
synthetic leverage.

The two-sided requirement is measured on realized positions, not a token target. In each of IS and
public OOS, each sleeve must have at least 1% gross exposure on 5% of 8h bars, at least 0.5% mean
gross exposure, and the execution ledger must contain at least 1,000 USDT of both buy and sell
notional. Side price/funding PnL and exposure are published and reconciled. This is a design-contract
check, not a performance threshold: neither sleeve has to be profitable to remain valid.

The four mutually exclusive regime labels are fixed from one-day-lagged BTC daily data: `stress`
when trailing 30-day annualized volatility exceeds 80%; otherwise `bull` when trailing 60-day BTC
return exceeds +10%, `bear` when it is below −10%, and `chop` otherwise. No strategy input defines
its own scoring regimes.

Binance does not publish point-in-time historical quantity steps and minimum-notional filters.
The backtest therefore uses continuous quantities and retains current `exchangeInfo` only as
disclosed metadata; applying today's filters retroactively would create a different historical
bias. Small simulated orders must be visible in the trade ledger and treated as a limitation by
the Critic. The forward-paper stage applies the then-current quantity step, minimum quantity,
minimum notional, price tick, and order-rounding rules before any order is considered executable.

## 7. Team lifecycle

### Phase 0 — Common infrastructure freeze

The orchestrator freezes config, evaluator SHA, data manifest, regime labels, metric definitions,
compute budget, and the tournament CLI itself. Freeze is single-shot on branch
`quant-portfolio-blind-top40`. The generated `phase0_freeze.json` is committed in a later record
commit; its last-modifying commit and exact bytes are derived rather than self-referenced. Every
team freeze must descend from that record. Any pre-dispatch correction requires a new tournament
rather than silently rewriting this playing field.

### Phase 1 — Independent research

The QR writes `research_brief.md` before material experiments: mechanism, data lineage, expected
regime behavior, falsifier, model/validation plan, tuning budget, cost/funding thesis, and risk
failure modes. The QE implements the strategy adapter and tests. Teams may iterate on IS and public
OOS, logging every candidate and result.

No team may modify the evaluator, scorer, shared config, data snapshot, or another namespace.

### Phase 2 — Freeze one champion

The pair freezes exactly one Git SHA, parameters, seeds, dependency lock, data SHA, strategy SHA,
trial ledger, target-generation entrypoint, and submission manifest. Before the source manifest and
final reviews, a technical validation window may fix formatting only; it cannot change strategy
logic or parameters. No team file changes after the reviewed champion freeze.

The organizer binds QR and QE handoffs to their current Git commit and SHA-256 hashes of required
evidence. The source manifest is built and committed before the QE review. `freeze-team` rechecks
those hashes, the ledger/compliance evidence, the journal's Git history, and the team Git tree,
then records the strategy name/SHA without executing a canonical run. Its `run_state.json` change
is committed before the next team freezes. Only the tenth champion advances `research` to
`cohort_frozen`.

Before QE review, `build-team-source-manifest` inventories every non-self source/evidence file in
the complete team Git tree. Freeze permits only regular, non-executable UTF-8 text files with the
allowlisted source/config/document suffixes, at most 2 MiB per file and 10 MiB in aggregate; the
manifest records each path, Git blob OID, size, and SHA-256. The freeze commit and canonical runner
bind and fingerprint that whole allowed tree, so a helper cannot affect execution merely by being
omitted from the shorter named-artifact list.

The worker does not receive that entire evidence tree. It stages only Python source plus the
narrow fixed strategy config names (`frozen_config.json` and `strategy_config` in JSON/TOML/YAML),
with staged config capped at 64 KiB. Opaque pre-fitted model blobs and timestamp→target lookup
tables are prohibited even when Git-frozen: they can encode information from later decisions that
runtime context truncation cannot detect. Learned state must be created or refit inside the
chronological worker from the history available at that decision. This restriction applies to the
scored historical rerun, not to a model trained after winner freeze solely for prospective paper
use.

Canonical strategy execution fails closed unless the host supplies the implemented Linux
sandbox: user/mount/network/PID namespaces, a masked repository, read-only staged source/runtime,
Landlock ABI 6+ restrictions, the x86-64 seccomp policy, cleared capabilities, `no_new_privs`,
resource limits, and Python audit guards. The environment is built from a minimal allowlist rather
than inherited organizer variables. Each worker has a 1,800-second whole-run wall deadline and
900 CPU-second limit, plus bounded address space, files, descriptors, and processes/threads. These are
defense-in-depth controls around the trusted parent evaluator, not a separate physical host.

Every team entrypoint exposes `build_strategy()` and returns one fresh object implementing
`TargetStrategy.target_weights(context, seed=...)`. The canonical runner imports only that factory;
teams cannot submit fills, costs, PnL, or scores.

### Phase 3 — Canonical rerun

The orchestrator reruns every frozen champion from a clean process on the common snapshot. Team
metrics are advisory only; evaluator outputs are canonical. It produces base and 2×-cost results,
long/short attribution, calendar and regime breakdowns, trial-adjustment evidence, and integrity
tests.

`finalize-team` reads the recorded champion; it accepts no caller-supplied strategy name or SHA and
is unavailable until all ten champions are frozen. Each invocation performs two independent clean
canonical runs and requires identical scalar fields, artifact entries, and bytes. The first nine
tracked submissions/artifact manifests and `run_state.json` changes are committed before the next
finalization; reproducible report files remain local and are SHA-bound rather than added to Git.
The tenth completed finalization also creates `objective_lock.json`, binding all ten submissions,
artifact/canonical-output hashes, objective scores/ranks, cohort hash, and Phase-0 hashes, and
advances `cohort_frozen` to `objective_locked`. That record, the tenth tracked manifests, and
updated state are committed together as a unique first-add commit whose sole parent is the
pre-lock HEAD.

### Phase 4 — Critic and user ballots

The Critic reviews all ten together after the objective record is committed. Team identity stays
blinded until the Critic ballot is final. `lock-critic` seals the complete Critic score and
adjudication files; those files, their lock, and updated state are first-added together in a commit
whose sole parent is the objective-lock record commit. Objective scores and ranks were computed
before any Critic finding, so a Critic DQ never changes another team's objective result.

Critic findings are allegations until independently confirmed. On the Critic-lock commit, the
organizer records exact confirmed codes for every team and runs `lock-critic-confirmations`; only
confirmed, already-cited findings become scoring DQs, while every unconfirmed finding remains
review commentary. The confirmations, their lock, and state are committed together as the direct
child of the Critic-lock commit. Only then may the user ballot be requested or created.
`lock-user-ballot` binds that later ballot in another direct-child first-add commit. Final scoring
loads only the ten canonical locked submission paths, verifies the whole unchanged chain, and
publishes objective rank, Critic score, user score, total rank, and paper eligibility. If confirmed
findings would eliminate every mechanically valid team,
the confirmation or scoring step stops for manual integrity review rather than approving an empty
field.

### Phase 5 — Forward paper

The winner and any paper-eligible runner-up may enter the frozen forward-paper stage. Tournament
scores never change retroactively. The prospective clock begins at the first 8h boundary after
the winner-freeze timestamp. Data from 2026-07-01 through that boundary is quarantined and may not
be backfilled as untouched evidence. `freeze-winner` recomputes the committed final leaderboard,
selects its unique rank-one team, binds the complete winning Git tree and canonical artifact set,
and initializes a paper-only hash-chain genesis. The winner record and paper-frozen state must be
committed together in the record's unique first-add commit, whose sole parent is the committed
selection record; `verify-winner-freeze` is required afterward. Live orders are explicitly
disabled. The record defines, but does not itself
implement, the later public-Binance observation ingester. Its timestamp trusts the organizer host's
UTC clock: Git/SHA history makes mutation evident inside this repository but is not an external
timestamping or notarization service. Forward evidence changes only deployability status.

## 8. Scoring and critic authority

The final score is **70 objective + 15 Critic + 15 user**. Objective scoring uses average cohort
percentile ranks with deterministic tie handling:

- 28: public-OOS net Sharpe, Sortino, Calmar, annualized return, and drawdown;
- 8: IS net Sharpe and Calmar;
- 12: IS/OOS coherence and the weaker window's positive-quarter fraction;
- 12: worst regime Sharpe and fraction of positive regimes;
- 10: actual 2×-cost Sharpe and Sharpe retention.

The score rewards strong IS and OOS together; an OOS-only inversion does not dominate a coherent
generalizer. Trial count and the candidate-return ledger inform the Critic's bounded selection-bias
score. The leaderboard must also publish raw metrics and confidence intervals so rank aggregation
never hides economic magnitude. Sharpe intervals use a deterministic 2,000-sample circular block
bootstrap with 10-day blocks and seed 20260713.

The Critic awards 0–15 using five equally weighted categories: timestamp/leakage integrity,
execution/funding realism, deterministic reproducibility, honest multiple-testing ledger, and risk
disclosure/ablations. It must cite evidence and score every valid team.

The Critic may allege disqualification only for demonstrated integrity/executability failures:
future data, future
membership, non-Binance market input, same-bar leakage, evaluator tampering, omitted or wrong-sign
funding, omitted costs, post-freeze mutation, false provenance, or failed deterministic rerun. It
may **not** disqualify or veto for low Sharpe, high drawdown, a weak regime, complexity, subjective
doubt, or failure to cross DSR/PBO/PSR thresholds. Those affect scores and confidence. At least one
valid team is the tournament winner even when no team is paper-eligible.

Every Critic integrity finding must use a machine-enforced charter code, cite a specific artifact
and its SHA-256, and bind to both the team's freeze SHA and canonical artifact-manifest SHA. The
adjudication also binds the complete ten-team cohort hash. The accepted codes are:
`critic_future_data`, `critic_future_membership`, `critic_non_binance_input`,
`critic_same_bar_leakage`, `critic_evaluator_tampering`, `critic_omitted_funding`,
`critic_wrong_funding_sign`, `critic_missing_costs`, `critic_post_freeze_mutation`,
`critic_false_provenance`, and `critic_failed_deterministic_rerun`. Performance findings have no
disqualification code. A cited finding affects validity only if the later independent confirmation
record includes its exact code; unconfirmed findings never disqualify. Final scoring requires the
locked objective record, complete Critic ballot and adjudications, complete confirmation record,
and the later locked user ballot.

## 9. Paper eligibility (separate, mechanical)

A valid team is automatically nominated for paper trading when it has IS net Sharpe ≥0.75, public
OOS net Sharpe ≥1.0, 2×-cost OOS Sharpe ≥0.5, OOS drawdown ≤30%, at least 62.5% positive OOS
quarters, at least three positive regimes, and worst-regime Sharpe ≥−0.25. The Critic cannot erase
this label; only a confirmed, allowlisted integrity failure can make the team invalid.

## 10. Required artifacts and namespace

Each team writes only `tournament/top40/teams/team-NN/` and `reports-top40/team-NN/`:

- `research_brief.md`, `provenance.md`, `feature_lineage.json`;
- `experiments.jsonl` with every attempted candidate and public-OOS access;
- strategy source, frozen config, seeds, dependency lock, and reproduce command;
- complete `team_source_manifest.json` for the allowed frozen text tree;
- tests for truncation invariance, future corruption, append invariance, funding sign/timestamp,
  membership, next-open execution, long/short signs, costs, and deterministic rerun;
- evaluator-produced targets, fills, positions, funding, daily returns, regime metrics, and audit;
- deterministic 95% Sharpe intervals for IS, public OOS, and 2×-cost public OOS;
- `submission.json` conforming to `tournament/top40/templates/submission.json`.

The orchestrator alone writes shared config, evaluator, scoring code, and final leaderboard.
