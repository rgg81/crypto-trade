# CUP-50 v2

An immutable tournament namespace. It imports no earlier candidate source, parameter, ranking,
result or conclusion; only neutral protocol code and checksum-verified raw Binance archive bytes are
reused.

The human policy is [`TOURNAMENT-CHARTER-CUP50-V2.md`](../../TOURNAMENT-CHARTER-CUP50-V2.md); the
machine policy is [`config.toml`](config.toml), and it is the *only* place a tunable lives — the
scorer, the evaluator, the risk unit, the neighbourhood geometry and the trial budget all read from
it, so a number cannot be changed in one place and disagreed with in another.

```text
cup50v2 acquire-reuse | build | readiness | export-protocol | export-evaluator | activate |
        quarantine | research-eval | trial | evaluate | nominate | critic-pack | field-close |
        observe | integrity-review | leaderboard | release | paper
```

## What is here

| Path | What it is |
|---|---|
| `config.toml` | every tunable, hash-bound by the activation record |
| `TEAM-MANDATES.json` | the twelve lanes: objective, thesis, guidance, and what is forbidden |
| `seeds/team-NN/` | the organizer's starting point for a lane, plus its mandate and templates |
| `historical-unavailability.json` | every verified contract cessation, organizer side |
| `is-unavailability.json` | the in-sample restriction of the same audit, team-visible |
| `risk-policy.json` | the common risk unit, and the requirement that teams declare their own |
| `sandbox/` | the evaluation image: no network, read-only root, non-root user |

## The shape of a run

Team research roots are generated outside this repository and are accepted only after the clean-room
scanner proves they contain no Git metadata, prior tournament, private artifact, sealed data, cached
frame or post-cutoff date literal. Evaluation runs in network-disabled, read-only containers with
only the protocol bundle and the sanitized team-visible snapshot mounted. That export carries no
transaction-open column, no execution marks and no funding mark prices; organizer execution uses a
separately hashed snapshot that is never mounted into a team workspace.

No lane qualifies out of observation and none is replaced. At field close each lane is either a
source- and neighbourhood-bound nomination — carrying its qualification verdict, decided from
in-sample evidence while the sealed window is still shut — or a DNF. Observation is one-shot and
silent until the complete leaderboard passes integrity review and is published atomically.
