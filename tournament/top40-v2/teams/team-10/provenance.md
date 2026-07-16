# Team 10 provenance

Status: **prospective, unregistered, no result-bearing artifacts**

## Clean-room inputs used to author this draft

- Top-40 V2 public README, methodology, team playbook, frozen config, and public schemas;
- the neutral `DecisionContext`/`TargetStrategy` interface and strategy-neutral evaluator contract;
- active Amendment 0006 public authority, freeze, and integration freeze; and
- Team 10's own bootstrap, base risk-policy scaffold, and empty organizer ledgers.

No other team's namespace, V1 team artifact, report, private qualifier artifact, final-OOS artifact,
leaderboard, ballot, evaluator output, or performance result was inspected. No snapshot data was
opened. No evaluation, registration, lifecycle mutation, or performance-directed search occurred
while preparing this package.

## Availability and implementation lineage

`strategy.py` uses only `decision_time`, `eligible_symbols`, and the past-closed `open_time` and
`close` columns in `DecisionContext.bars`. It does not use funding or auxiliary datasets. The
canonical worker supplies these histories causally and Amendment 0006 certifies the upstream
eligible universe as native crypto only.

All model choices are explicit in `frozen_config.json`; there are no serialized fitted coefficients,
hidden state, external files, network calls, subprocesses, credentials, or writable outputs. The
strategy is deterministic for every valid seed. Exact source/config/risk/source-bundle hashes are
intentionally left as zero-hash sentinels only in clearly named templates until organizer review and
preregistration replace them.

## Holds

Before any measurement, an organizer must perform the static review, bind the complete executable
source set, replace every template sentinel, register the family, and register the exact trial through
the active A5 superset entrypoint, which preserves the A6 pure-crypto preflight. Before any
qualification claim, the six chronological fold artifacts,
stitched returns, and all neighbor returns must be centrally produced and hash bound. The private
ticket remains one-shot and final OOS remains sealed.
