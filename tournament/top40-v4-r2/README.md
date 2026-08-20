# Top-40 V4-R2

This directory is the public authority for a fresh 15-lane tournament. Teams choose their own
mechanisms inside deny-by-default clean rooms. Six or fewer robust IS nominees enter a single
sealed historical championship ending after the final July 2026 bar.

The charter is [`../../TOURNAMENT-CHARTER-TOP40-V4-R2.md`](../../TOURNAMENT-CHARTER-TOP40-V4-R2.md).
Numerical policy is [`config.toml`](config.toml), clean-room semantics are
[`CLEANROOM-POLICY.md`](CLEANROOM-POLICY.md), and the operating sequence is
[`TEAM-PLAYBOOK.md`](TEAM-PLAYBOOK.md). The complete neutral candidate interface is
[`STRATEGY-API.md`](STRATEGY-API.md).

## Lifecycle

```text
15 independent clean rooms
  -> up to 12 preregistered IS trials per lane
  -> one eligible nominee or evidence-backed retirement per lane
  -> exact robust rank; at most 6 finalists
  -> identities + reporting ensemble frozen
  -> one serial, silent historical observation per finalist
  -> one atomic cohort release
  -> September 2026 live-forward paper observation
```

## Organizer commands

```bash
uv run python scripts/top40_v4_r2_tournament.py audit-isolation
uv run python scripts/top40_v4_r2_tournament.py validate --pre-activation
uv run python scripts/top40_v4_r2_tournament.py activate
uv run python scripts/top40_v4_r2_tournament.py status
```

Activation additionally requires a frozen snapshot whose exclusive hard end is 2026-08-01. It
fails closed if the bound data manifest ends before that boundary.
Activation performs the expensive full raw-source replay once. Each later result command repeats
the bound pure-crypto classification audit and canonical-file hashes before and after execution,
without re-reading tens of thousands of immutable source archives.

This worktree is the third clean restart after private predecessor incidents. No predecessor is
continued: no candidate, feedback, result, source archive, research receipt, or decision is reused,
and all 15 lanes begin at trial zero. The exact score-blind incident facts and predecessor hashes
are frozen in `FRESH-RESTART-AUTHORITY.json`; teams cannot read that organizer authority or any
predecessor artifact. Activation independently proves the physical restart is an exact seed-only
genesis, repeats that proof across its test run, and binds the resulting chained surface digest
into the activation freeze before any team can launch. Team-model commands additionally use an
organizer-private, skill-empty, per-team Codex runtime; the exact model, prompt, argv, sanitized
environment, and runtime identities are bound into every launch and candidate receipt.

The isolated rebuild authority is `SNAPSHOT-BUILD.toml`; it publishes to `snapshot-v2` and an
edition-local manifest, leaving every existing snapshot unchanged.

```bash
uv run python scripts/top40_tournament.py build-snapshot \
  --config tournament/top40-v4-r2/SNAPSHOT-BUILD.toml
```

```bash
uv run python scripts/top40_v4_r2_team_broker.py probe team-01
uv run python scripts/top40_v4_r2_team_broker.py run-team team-01
uv run python scripts/top40_v4_r2_tournament.py close-is
uv run python scripts/top40_v4_r2_tournament.py historical-release
```

The broker runs one short-lived offline model session at a time and evaluates only after that
process exits. One blocking process-wide lease makes `run-all` and individual broker commands
strictly serial; they never overlap teams. The state machine resumes completed phases and skips
terminal teams after a process or host restart. No team command reads the holdout. Heavy result
commands serialize under one kernel lock. During the historical phase, `status` reveals only the
frozen finalist count and a constant sealed state.
