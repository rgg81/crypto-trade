# Team07 provenance

This family was developed independently in the Team07 V2 namespace from the tournament charter,
methodology, public templates, neutral strategy/risk interfaces, and frozen Amendment 0006
pure-crypto authority. No V1 strategy/result, other V2 team, private-qualifier record, final-OOS
data, leaderboard, organizer journal/state, or Amendment 0005 diagnostic was inspected.

The economic starting point is the generic market-microstructure idea that price discovery occurs
first in more liquid instruments and propagates to related instruments with heterogeneous delay.
Team07's implementation is original for this tournament: a dynamic liquidity leader basket,
contemporaneous-beta residualization, nonnegative lag-response estimate, residual overshoot term,
funding crowding conditioner, cross-sectional two-sided ranks, and bounded directional side tilt.

Authorship state as delivered:

- families.jsonl and experiments.jsonl remain organizer-owned empty ledgers;
- no registration, evaluator, lifecycle, test, Python, or git command was run by the clean-room
  authoring agent;
- no performance number, qualification claim, or schema-validation claim is made;
- zero hashes and the epoch timestamp in registration templates are explicit sentinels and must be
  materialized from frozen bytes immediately before organizer registration;
- strategy.py contains no network, subprocess, filesystem read/write, fitted historical constant,
  timestamp-target table, or evaluator-state dependency.

Amendment 0006 remains the exact pure-crypto universe authority. Its entrypoint is now
superseded-unchanged by the reviewed Amendment 0005 superset. All future Team07 commands must use
`scripts/top40_v2_tournament_score_diagnostics_v5.py` (SHA-256
`0dc9228f3b9c6fe41b2655055f766fc92f323a289a050e6bdf4e48a30b0105f4`), bound by A5
integration-freeze commit `d2b95f610722aab65b4e67466b34efeaa3554101` and SHA-256
`b3b2b96245a479ccfff95b5cd5b5cd0aef3b2d0aac0fc9faf5367d3e6772958c`. Any result produced
through a historical or draft entrypoint is outside this package's authority.
