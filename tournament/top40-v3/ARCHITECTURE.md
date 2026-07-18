# Top40-v3 architecture decision

## Decision

Top40-v3 is a new tournament generation on branch `quant-portfolio-blind-top40-v3`. Top40-v2
remains terminal at commit `608f3842`; V3 never rewrites its state, locks, journals, amendments,
team ledgers, strategies, or reports.

V3 reuses the expensive strategy-neutral foundation by importing frozen implementations and
binding their hashes at Phase 0:

- target generation and canonical base/doubled-cost evaluation from `engine_v2.py`;
- strategy and decision contracts from `protocol.py`;
- risk execution from `risk_policy.py`;
- metric construction from `metrics_v3.py`;
- append-only train accounting from the fresh `journal_v3.py` authority;
- the shared immutable manifest and `data/top40/snapshot-v1` bytes; and
- the exact fail-closed native-crypto audit in `pure_crypto_universe_v6.py`.

V3 owns fresh layout, contract, runner, worker, lab, qualification, evidence, final, and CLI
boundaries. A V3 command may write only under `tournament/top40-v3/` and
`reports-top40-v3/`. Private and final-OOS trees are organizer-only. Team workers can see their
own executable tree and past-truncated market context, never another team, a private artifact,
or a future bar.

## Research lifecycle

Each team develops a complete trading system in a logged training lab. A material change to
features, horizons, parameters, portfolio construction, or risk controls creates a new immutable
lab record with source, configuration, risk-policy, artifact, resource, and result hashes.
Team candidate lanes are therefore excluded from the global infrastructure Phase-0 hash. The
organizer hashes the exact selected candidate tree, adjacent config and risk policy before each
accepted request, checks them again after execution, and journals both identity and outcome before
disclosure. This preserves unlimited logged IS iteration without weakening infrastructure drift
checks.

Before request acceptance, the organizer also creates or reuses a canonical content-addressed
archive below `reports-top40-v3/source-archives/sha256/`. It contains every UTF-8 source, config,
document, and test byte in the fingerprinted candidate boundary. A top-level team candidate owns
only direct regular files beside `teams/team-NN/strategy.py`; nested incumbent or challenger
entrypoints own their recursive candidate directory. The archive path and archive SHA-256 are
journal fields in addition to `source_bundle_sha256`. The runner replays the same boundary while
staging and may execute the live tree only when its complete staged manifest exactly equals the
verified archive manifest. This makes the archived bytes sufficient to recover the precise source
input for an accepted run even after the development lane changes.

Each team receives at most three sealed validation probes in the opening round. The runner maps
the validation stage internally; callers cannot pass arbitrary dates. A probe is bound to exact
candidate bytes and counts toward selection multiplicity. It returns the frozen validation
metrics and the candidate's public qualification gaps.

A submission lock requires matching positive training and validation checkpoints, positive
doubled-cost Sharpe in both, and a complete core-eligible development assessment. The first lock
freezes the team's executable and disables further labs. Each team has one formal nominee.

If fewer than three teams produce a core-eligible nominee, the organizer opens the predeclared
comeback round. Unqualified teams receive two additional logged validation probes and may develop
one replacement mechanism. The quality floors do not change.

## Qualification lifecycle

Public core eligibility is absolute. Core-eligible nominees are ordered by the compensatory
robustness score, and at most four advance to the one-shot private qualifier. Diagnostics such as
individual role signs, fold signs, IC, parameter neighborhoods, trial-adjusted confidence, and
PnL concentration remain published evidence; none is a standalone veto, ranking input, or
tie-breaker.

Private qualification is a generalization and safety check: integrity must remain intact, net and
doubled-cost Sharpe and annualized return must be positive, and drawdown must not exceed 35%.
There is no private per-regime veto. Survivors are frozen before the single final-OOS reveal.

## Data-change rule

The current V3 season uses only fields already present in the frozen snapshot. Premium-index
convergence is a reserve research track because premium-index history is not part of those bytes.
Adding it, or adding later contracts, requires a new manifest and a reviewed V3 pure-crypto audit;
no team may fetch or join external data inside a tournament run.
