# Top-12 V1

Top-12 V1 is a new twelve-team, strategy-blind successor to the Top-40 tournament machinery. It
preserves the anti-cheat controls while replacing the universe with a causal weekly Top 12 ranked
over six complete months.

The authoritative prose contract is
[`../../TOURNAMENT-CHARTER-TOP12-V1.md`](../../TOURNAMENT-CHARTER-TOP12-V1.md). Numerical policy is
in [`config.toml`](config.toml). Team-facing isolation rules are in
[`TEAM-ISOLATION.md`](TEAM-ISOLATION.md), the neutral implementation contract in
[`TEAM-API.md`](TEAM-API.md), and research workflow in [`TEAM-PLAYBOOK.md`](TEAM-PLAYBOOK.md).

## Lifecycle

```text
12 blind IS labs -> one eligible nominee/team -> robust IS rank -> top five
       -> freeze identities + ensemble -> one serial historical-OOS computation
       -> one atomic simultaneous release -> 365-day live-forward paper test
```

## Windows

| Stage | Dates | Feedback |
|---|---|---|
| IS research | 2020-08-03 to 2024-06-30 | complete causal artifacts |
| Historical OOS | 2024-07-01 to 2026-06-30 | one simultaneous final release |
| Live forward | from 2026-08-03 | no changes for at least 365 days |

The historical-OOS label is candidate-relative. The organizer already knows this era and may know
unrelated strategies; teams do not. It cannot be presented as a globally pristine deployment test.

## Universe

At each Monday 00:00 UTC boundary:

1. use only completed days strictly before the boundary;
2. require exactly 180 complete daily observations;
3. compute each eligible native-crypto contract's median daily quote volume;
4. rank descending with a symbol tie-break; and
5. trade the first twelve until the next weekly boundary.

The full ranking and pure-crypto classification are independently reproduced at activation and
before/after every result-bearing command.

## Non-negotiable rules

- Teams may not inspect prior strategies or another current team.
- Pure native crypto only; ambiguous classifications fail closed.
- At most twelve accepted trials per team; accepted failures count.
- At least eight trials and a complete research certificate precede nomination.
- Every IS floor is conjunctive; only the top five eligible nominees advance.
- Historical-OOS code and weights are frozen, archive-backed, and observed once.
- There is no forced winner, post-OOS repair, replacement, or backfill.
- Heavy result commands are serialized under an organizer lock.

## Organizer commands

All commands run from the repository root. Activation is one-time and must occur only after all
twelve baseline bundles, focused tests, hashes, and the blindness audit are final.

```bash
uv run python scripts/top12_v1_tournament.py validate --pre-activation
uv run python scripts/top12_v1_tournament.py activate
uv run python scripts/top12_v1_tournament.py status
```

An IS trial is accepted before the runner opens market data:

```bash
uv run python scripts/top12_v1_tournament.py is-run team-01 \
  tournament/top12-v1/teams/team-01/candidates/<candidate-id>/strategy.py \
  --purpose "preregistered baseline"
```

After at least eight accepted trials, a team nominates one eligible candidate or retires:

```bash
uv run python scripts/top12_v1_tournament.py nominate team-01 candidate-id \
  tournament/top12-v1/certificates/team-01/candidate-id.json
uv run python scripts/top12_v1_tournament.py retire team-01 --reason "mechanism falsified"
```

Only after all twelve lanes have a terminal IS disposition may the organizer close IS and perform
the atomic historical release:

```bash
uv run python scripts/top12_v1_tournament.py close-is
uv run python scripts/top12_v1_tournament.py historical-release
```
