# Top-40 V4

Top-40 V4 is the twelve-team successor to V3. It keeps V3 immutable and reuses only audited,
generation-neutral execution components through a new V4 authority and write namespace.

The authoritative prose contract is
[`../../TOURNAMENT-CHARTER-TOP40-V4.md`](../../TOURNAMENT-CHARTER-TOP40-V4.md). Numerical policy is
in [`config.toml`](config.toml). Team mechanisms are defined in [`TEAM-MANDATES.md`](TEAM-MANDATES.md)
and the operating workflow in [`TEAM-PLAYBOOK.md`](TEAM-PLAYBOOK.md).

## Lifecycle

```text
12 structured IS labs -> one eligible nominee/team -> robust IS rank -> top five
       -> freeze identities + ensemble -> one serial historical-OOS computation
       -> one atomic simultaneous release -> 365-day live-forward paper test
```

## Windows

| Stage | Dates | Feedback |
|---|---|---|
| IS research | 2020-02-03 to 2024-06-30 | complete causal artifacts |
| Historical OOS | 2024-07-01 to 2026-06-30 | one simultaneous final release |
| Live forward | from 2026-08-01 | no changes for at least 365 days |

The historical-OOS label is candidate-relative. This period is already known to the organizer and
cannot be presented as a globally pristine deployment test.

## Non-negotiable rules

- Pure native crypto only; stablecoins and every direct or tokenized TradFi exposure are excluded.
- At most twelve accepted trials per team; accepted failures still count.
- A research certificate and at least eight accepted trials are required before nomination.
- Every IS floor is conjunctive. Only the top five eligible nominees advance.
- Historical-OOS code and weights are frozen, archive-backed and observed once.
- There is no forced winner and no post-OOS repair.
- Heavy result commands are serialized under an organizer lock.

## Organizer commands

All commands run from the repository root. Activation is one-time; it runs the focused V4 tests,
hashes the infrastructure and pure-crypto authority, and pre-creates the durable journal.

```bash
uv run python scripts/top40_v4_tournament.py validate --pre-activation
uv run python scripts/top40_v4_tournament.py activate
uv run python scripts/top40_v4_tournament.py status
```

An IS trial is accepted before the runner opens market data. Its entrypoint must be the exact
`strategy.py` in one nested candidate directory.

```bash
uv run python scripts/top40_v4_tournament.py is-run team-01 \
  tournament/top40-v4/teams/team-01/candidates/t01-slow-tsm-baseline-v1/strategy.py \
  --purpose "transparent slow-trend baseline"
```

After at least eight accepted trials, a team either nominates one eligible candidate with a
journal-backed certificate or retires. Certificate files live under
`tournament/top40-v4/certificates/<team-id>/`; each required evidence cell lists the accepted
request-record hashes whose preregistered tags satisfy that cell.

```bash
uv run python scripts/top40_v4_tournament.py nominate team-01 candidate-id \
  tournament/top40-v4/certificates/team-01/candidate-id.json
uv run python scripts/top40_v4_tournament.py retire team-01 --reason "mechanism falsified"
```

Only after all twelve lanes have a terminal IS disposition may the organizer freeze the top-five
eligible bracket. The second command first journals every finalist acceptance without reading the
sealed snapshot, then journals one start marker and consumes each observation serially. It makes
one simultaneous public release.

```bash
uv run python scripts/top40_v4_tournament.py close-is
uv run python scripts/top40_v4_tournament.py historical-release
```
