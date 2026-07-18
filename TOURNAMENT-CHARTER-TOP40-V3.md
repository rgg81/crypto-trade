# Top-40 V3 Tournament Charter

Status: **v3 policy and training infrastructure active; Phase-0 freeze required before any lab result**

This charter defines a new ten-team tournament. It is intentionally stricter about research
quality than Top-40 V2: teams may iterate freely on visible training data, but they may not lock
a nominee that is already losing on either training or sealed validation data.

## 1. Independent season and immutable history

Top-40 V2 is terminal and immutable. V3 MUST NOT amend, reopen, relabel, overwrite, or append to
any V2 charter, amendment, registry, audit log, submission, or result. V3 has its own namespace,
registries, journals, reports, locks, and result authorities under `tournament/top40-v3` and
`reports-top40-v3`.

V3 may read the frozen Top-40 snapshot and the approved Amendment 0006 (A6) pure-crypto audit as
immutable authorities. Reuse does not transfer V2 lifecycle state or authorize writes to V2.

## 2. Teams, objective, and eligible instruments

The field contains exactly `team-01` through `team-10`. Each team develops a complete,
deterministic long/short crypto portfolio system, including any signals, sizing, brakes, stop
losses, exposure controls, liquidity controls, and state transitions it needs to survive bull,
bear, chop, and stress conditions.

The instrument universe is the exact weekly Top-40 membership already frozen in
`data/top40/snapshot-v1/membership.parquet`; its ranks MUST NOT be rebuilt or reinterpreted. Every
candidate and every weekly member MUST pass the exact A6 native-crypto policy before and after
every result-bearing command:

- data manifest SHA-256:
  `077eb036d262befec80f7013084fe6906859f7c3bbe2f8c193c9d9ec68e367c3`;
- membership SHA-256:
  `f51c9eb207c1da51cc4b9ff6045bb5e914828015b5c9c214f0e2673cd868eb14`;
- contract-metadata SHA-256:
  `0995d50011e73de880358b994031fdf8bb58e75ab8901de2c5601e7abed05243`;
- exchange-info SHA-256:
  `aab4219452e61cfa5e135518ed182c98fd7e527d13bc240e891bb6b550deeb64`;
- A6 policy SHA-256:
  `2c7fb0ff593d06c323517e60df4b28ab9387a2df580b83f82f65ef71c91fc350`;
- A6 audit-module SHA-256:
  `fc93c0f26dcbf6304abe028736693ab2bee7430a56c14a8547defff472008192`.
- A6 integrity-dependency SHA-256:
  `e3a4f60aa955ebcf461026527da5b6b28b87e9e7ec057dd2e10a1e884612a8ab`;
- deterministic A6 audit-report SHA-256:
  `b9c55b40fef331861af068272159f45860870182a58c93652eff2a819b3d5d1b`.

Eligibility is fail-closed. A listing on Binance USD-M is not sufficient. Only native crypto
coins or tokens in exact `PERPETUAL`, `COIN`, USDT-quoted and USDT-margined contracts are allowed.
Stablecoins, leveraged tokens, tokenized metals or commodities, direct metals or commodities,
equities, ETFs, indexes, foreign exchange, premarket instruments, and every other direct TradFi
exposure are excluded. Unknown or ambiguous classifications are excluded pending a separately
reviewed future snapshot. Crypto protocol tokens in Binance's `RWA` sector are not direct TradFi
exposures merely because of that sector label; A6's exact asset-level and contract-level checks
remain authoritative.

## 3. Frozen evaluation windows

All boundaries are UTC and MUST be enforced from exact frozen timestamps:

| Window | Inclusive dates | Team access | Purpose |
| --- | --- | --- | --- |
| Warm-up | 2020-01-01 to 2020-02-02 | historical context only | indicator initialization; never scored |
| Training | 2020-02-03 to 2022-06-30 | rows and full metrics visible | research laboratory |
| Sealed validation | 2022-07-01 to 2023-06-30 | no rows, returns, targets, or positions; fixed metric packet only | limited model selection |
| Private qualifier | 2023-07-01 to 2024-06-30 | no information before the one private decision | finalist gate |
| Final OOS | 2024-07-01 to 2026-06-30 | no information before simultaneous reveal | final test |

A strategy may use earlier observations as causal warm-up at a later window boundary, but scored
PnL starts exactly at that window's first executable boundary. No later-window value, timestamp
availability fact, target, statistic, cached state, or indirect proxy may enter an earlier run.

## 4. Research laboratory and multiplicity ledger

Training iteration is not numerically capped. It is instead fully accountable: every
organizer-recognized train run, including failures, aborted runs, baselines, ablations, risk-only
changes, seed changes, and parameter sweeps, MUST receive a monotonic per-team sequence number and
be appended to an organizer-owned, append-only journal before its metrics are released. Entries
MUST NOT be deleted, renumbered, replaced, squashed, or reset during a comeback round.

The V3-specific journal schema binds the season. Across its hash-chained request and terminal
records, each trial MUST bind: team, run and candidate IDs; accepted and completed timestamps;
parent candidate; purpose; source-bundle, strategy, dependency-lock, tournament-configuration,
risk-policy, data-authority, evaluator, metric-packet, and artifact hashes; seed and all material
parameters; train window and cost model; unique output path; CPU/wall resource use; terminal event,
failure reason and gate vector; and the cumulative material-trial count. A change
to code, configuration, feature set, seed, fit window, portfolio construction, execution
assumption, or risk control creates a new material trial. The active training laboratory has no
special replay mode: every invocation, including identical bytes, is another logged material
trial. A future organizer replay authority may be introduced only prospectively; it may never
erase, reduce, or relabel the historical trial count.

A successful training run returns the full frozen coaching packet: annualized return, net Sharpe,
Sortino, Calmar, maximum drawdown, positive-quarter fraction, doubled-cost Sharpe, executed-trade
count, bull/bear/chop/stress Sharpes, bootstrap confidence intervals, exact core-floor gaps,
RED/AMBER/GREEN action codes, candidate/evaluator/data hashes, and immutable artifact hashes. The
transparent training artifacts include bar and daily returns at base and doubled costs, targets,
positions, trades, and events; teams may compute richer attribution, turnover, fee, slippage,
funding, exposure, concentration, fold, IC, and neighborhood diagnostics from those visible IS
artifacts. Those research diagnostics are coaching evidence, not undisclosed performance gates.

## 5. Sealed validation probes

Each team has at most **three** sealed-validation probes in the opening round. The counter is
organizer-owned, append-only, consumed when a valid request is accepted, and is not restored by a
crash, failure, withdrawal, replay, candidate rename, or team restart. If and only if the
predeclared comeback round triggers, an unqualified team receives two additional probes, for a
maximum of five. An exact organizer-caused replay may verify reproducibility, but MUST NOT
disclose a second observation.

Before a probe, the team MUST freeze the candidate's exact source, dependencies, configuration,
risk controls, parameters, seed, and train-run parent by cryptographic hash. The organizer runs
that frozen candidate without revealing validation rows, per-period returns, positions, trades,
targets, or regime timestamps. The team receives one fixed summary packet: gate status; gross and
net aggregate metrics; base- and doubled-cost metrics; drawdown; trade count; quarterly and fixed
regime aggregates; the public-core pass/fail vector; and hashes. The packet format is identical
for every team and cannot be queried interactively.

Any post-probe change to a frozen byte or material setting creates a new candidate and requires a
new probe before that candidate can be nominated. Probe results may never be transferred between
non-identical candidates.

## 6. Development, readiness, and formal nomination

Teams are expected to develop the full trading system before lock. Stop losses, volatility
brakes, trend or chop filters, drawdown responses, time exits, exposure caps, deleveraging,
liquidity controls, and other causal risk controls are legitimate research components. They are
not post-result repairs and become immutable parts of the candidate they accompany.

A candidate is *readiness-eligible* only if:

1. it has completed, hash-bound training and sealed-validation records;
2. all hard gates in section 7 pass in both records;
3. training `net_sharpe > 0`, `annualized_return > 0`, and `double_cost_sharpe > 0`; and
4. validation `net_sharpe > 0`, `annualized_return > 0`, and `double_cost_sharpe > 0`.

Zero is not positive. A team MUST NOT formally nominate a candidate with a negative or zero value
in any of those six train/validation values. `DNF`, a missing metric, a nonfinite metric, an
incomplete run, or a gate failure is not a submission.

After the ordinary lab phase and any triggered comeback round, each team may lock **one and only
one** formal nominee. The nominee MUST be readiness-eligible, satisfy every public-core floor in
section 8 on the deterministic train-plus-validation record, and be byte-for-byte and
configuration-for-configuration identical to that probed candidate. A positive but below-core
candidate remains lab evidence and is not a formal tournament submission. Nomination consumes
the team's only formal slot; withdrawal does not create another. No signal, parameter, risk
control, dependency, seed, or configuration may change after lock.

## 7. Non-negotiable hard gates

Hard gates are evaluated before performance. Failure of any one is terminal for that run and
cannot be offset by score:

- **integrity and reproducibility:** all authorities and artifacts are present, hash-bound,
  deterministic under exact replay, and journaled before disclosure;
- **data and universe:** only the frozen snapshot, exact point-in-time membership, and A6-passing
  native-crypto contracts are used; no stablecoin, TradFi, metal, commodity, or index exposure;
- **causality:** every feature, fit, state transition, membership decision, price, and risk action
  uses only information available at the decision boundary; future-data corruption tests pass;
- **execution contract:** next-open fills, point-in-time fillability, fees, slippage, funding,
  participation, delists, and exposure controls are applied by the frozen evaluator;
- **solvency and completeness:** equity remains finite and strictly positive, required marks and
  positions reconcile, no bankruptcy/liquidation is hidden, and the full scored window completes.

## 8. Public performance core

For a formal nominee, the public qualification record is the deterministic concatenation of its
training and sealed-validation scored return streams, while the two windows remain separately
reported and must satisfy section 6. All metrics below are net of fees, slippage, and funding.
Maximum drawdown is a nonnegative magnitude. A trade is one nonzero executed symbol/boundary fill
after evaluator netting; funding alone is not a trade, and order fragmentation cannot inflate the
count. A regime is positive only when its Sharpe is strictly greater than zero.

A nominee is a public-core passer only if every floor holds:

| Metric | Hard floor |
| --- | ---: |
| Net Sharpe | `>= 0.75` |
| Annualized return | `> 0` |
| Maximum drawdown | `<= 0.30` |
| Doubled-cost Sharpe | `>= 0.35` |
| Positive-quarter fraction | `>= 0.50` |
| Executed trades | `>= 1000` |
| Positive bull/bear/chop/stress regime Sharpes | `>= 2 of 4` |
| Worst bull/bear/chop/stress regime Sharpe | `>= -0.75` |

A missing or nonfinite core value fails the core. The floors are fixed and may not be waived,
averaged away, rounded into compliance, or lowered because too few teams pass.

## 9. Robustness ranking and advancement

Only public-core passers are ranked. Let `C(x) = min(1, max(0, x))`. For the public qualification
record, compute:

```text
R = 25*C((net_sharpe - 0.75) / 0.75)
  + 15*C(annualized_return / 0.30)
  + 15*C((0.30 - max_drawdown) / 0.20)
  + 15*C((double_cost_sharpe - 0.35) / 0.65)
  + 15*C((positive_quarter_fraction - 0.50) / 0.25)
  + 10*(positive_regime_count / 4)
  +  5*C((worst_regime_sharpe + 0.75) / 1.50)
```

`R` ranges from 0 to 100 and is a ranking score, not an additional veto. Rank eligible nominees
by descending unrounded `R`. Ties break by lower maximum drawdown, then higher doubled-cost
Sharpe, then higher worst-regime Sharpe, then lexicographically smaller team ID. The top four
advance to the private qualifier; if fewer than four pass the core, every core passer advances.

## 10. Diagnostics are evidence, not hidden vetoes

The organizer MUST compute, score, and disclose: expected role/sign agreement; fold and
walk-forward consistency; information-coefficient level, sign, and decay; trial-adjusted
confidence using the complete multiplicity journal; local parameter-neighborhood stability; and
position, sleeve, sector, and return concentration. The season implementation MUST freeze and
hash the normalization rubric before the first lab result. The disclosed diagnostic score is
0–100 with component weights of 15, 20, 15, 20, 15, and 15 points in the order listed above.

Diagnostics may expose fragility and inform human interpretation, but they MUST NOT disqualify a
hard-gate-compliant nominee, change a core floor, enter `R`, change the top-four order, or become
an undeclared private or final veto.

## 11. Predeclared comeback lab round

After ordinary probes close but before formal nomination lock, the organizer counts teams that
have at least one readiness-eligible candidate satisfying every public-core floor. If that count
is below three, one—and only one—comeback lab round opens for teams without such a candidate.
Formal nomination lock is delayed until that round ends.

The comeback round permits more fully logged training work and grants each eligible team exactly
two additional validation probes. It grants no trial reset, no second formal nominee, no access
to private or final data, and no change to any gate, metric, cost, window, floor, ranking formula,
or tie-break. Every additional probe remains hash-bound and counts in the multiplicity record.
The round ends on the precommitted schedule even if fewer than three teams qualify.

## 12. Private qualifier

Each advancing nominee is evaluated once on the private qualifier with its formal hashes intact.
It advances to the final OOS reveal only if all of the following hold:

- integrity, data/universe, causality, execution, solvency, and completeness gates pass;
- net Sharpe is strictly positive;
- annualized return is strictly positive;
- doubled-cost Sharpe is strictly positive; and
- maximum drawdown is `<= 0.35`.

There is no private trade-count floor, positive-quarter floor, or per-regime veto. Private regime
metrics are reported diagnostically only. Failure is final; there is no repair, replacement,
second run, or fall-through promotion.

## 13. Final OOS and terminal publication

Every private passer receives exactly one final-OOS observation. The organizer may perform an
exact, nondisclosing deterministic replay solely to verify infrastructure, but all finalists'
complete final packets are released simultaneously as one reveal; no interim metric, direction,
rank, error detail, or partial result may reach a team. No candidate may be repaired or replaced
after any final computation begins.

The final leaderboard reports the full metric packet and orders hard-gate-compliant finalists by
the same unrounded robustness formula `R`, now computed only on final-OOS metrics, with the same
tie-breaks. Final core floors are disclosed as reference flags, not retroactive OOS vetoes. If no
candidate reaches the final, the season records **no qualified finalist** rather than fabricating
a submission or lowering a standard.

Every stage transition, counter, hash, gate vector, score, advancement decision, and publication
MUST be append-only, reproducible from frozen authorities, and attributable to an organizer
event. Silence, missing output, and `DNF` never count as a valid submission.
