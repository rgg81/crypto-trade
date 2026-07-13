# Top-40 tournament Phase-0 policy

This file is part of the common playing-field freeze. `TOURNAMENT-CHARTER-TOP40.md` and
`config.toml` remain authoritative if prose here conflicts with a machine-readable value.

## Fixed research budget

Each team may evaluate at most 120 materially distinct configurations, consume at most 12 CPU
hours and 18 wall-clock hours, and deliberately inspect the public OOS period at most three times.
Every material configuration and public-OOS access must be appended to the team's trial ledger
before results are read. Each candidate uses a `registered` event followed by a `result` event as
defined in `templates/experiment-event.schema.json`; registrations are never rewritten. The
research deadline is 2026-07-16 18:00 UTC.

An OOS-requesting registration is necessary but not sufficient for access. The only full-period
research path is `run-team TEAM_ID --candidate-id ID`; before loading the evaluator it atomically
reserves that still-pending candidate in organizer-owned `run_state.json` and
`organizer_research_journal.jsonl`. The journal begins with a canonical genesis anchored by the
Phase-0 common commit and `run_state.json`; reservation/result records form a canonical SHA-256
hash chain. Reservations bind exact registration/ledger bytes, the complete team-tree fingerprint,
Git identity, seed, evaluator, config, and data hashes. Each candidate is single-use. The organizer
automatically measures and records compute, status, metrics, and output hashes after the attempt.
Completed, failed, and interrupted reservations all count toward the maximum of three.

Result accounting uses the organizer journal as a write-ahead log: a result record contains the
exact canonical team-result bytes and their SHA-256 before the same bytes are appended to
`experiments.jsonl`, and `run_state.json` is projected last. If the process stops in any of those
windows, run `recover-research-accounting`. Recovery accepts only the journal tail extending the
state's exact anchored prefix, never rewrites either append-only stream, and rejects a different
ledger prefix, result, or tail. If recovery leaves a reservation open because evaluation never
produced a result, the organizer must run `close-interrupted-run TEAM_ID CANDIDATE_ID`; this records
one failed, non-replayable view and conservatively charges elapsed wall time since reservation.

Commit candidate code and its pending registration before `run-team`. After every run, commit the
strict append of the organizer journal, `run_state.json`, affected `experiments.jsonl`, and run
outputs before the next reservation. Freeze rejects dirty accounting, a journal/ledger rewrite or
truncation anywhere in Git history, or a mismatch with the organizer records.

The canonical strategy seed is `20260713`. Trial-search randomness uses the deterministic namespace
`20260713NN`, where `NN` is the two-digit team number. Teams must persist any additional derived
seeds and may not retry a seed merely because its result is poor.

## Data access and statistical interpretation

The two-year interval from 2024-07-01 through 2026-06-30 is a visible public OOS benchmark, not a
secret statistical holdout. Teams may use their limited, logged views for model selection. The
leaderboard must label it `public_oos`; claims of untouched performance begin only with forward
paper observations after the winning artifact is frozen. Market data from 2026-07-01 through that
freeze is quarantined: it may not be used in tournament scoring and may not be backfilled as
prospective evidence.

All market inputs come from the frozen Binance public USD-M snapshot named by
`tournament/top40/data_manifest.json`. Teams have read-only access. They may derive past-only
features but may not replace, repair, extend, or selectively omit common observations.

`build-snapshot`, `verify-snapshot`, and `freeze-phase0` perform the expensive raw-archive and
source-provenance verification. After the Phase-0 record has been uniquely first-added as the
exact child of the clean common commit, each research/canonical run may reuse that audit only if
the live manifest, snapshot builder, evaluator, config, dependency lock, methodology, organizer,
and run-state bindings still match the frozen Git and SHA-256 records. Every run still validates
the canonical manifest schema, hashes every manifest-listed canonical file before loading it,
validates the loaded data bounds, and rehashes every listed file after team execution. With no
Phase-0 record the runner invokes the full source verifier; a present but dirty, rewritten, or
mismatched Phase-0 record fails closed.

## Isolation

Teams receive only their identifier, common hashes, this policy, generic agent methodology, and
the common snapshot. They may not read historical portfolio strategies, reports, experiment
diaries, another team's namespace, or another team's results. The orchestrator logs mechanism
fingerprints before experiments solely to detect collisions without revealing either proposal.

## Freeze and rerun

One champion per team is frozen before any canonical cohort score is calculated. Formatting and
path-only repairs must occur before rebuilding the source manifest, repeating the affected review,
and freezing; no team-file mutation is allowed afterward. The orchestrator reruns every champion
in a clean process through the same evaluator and the independent 2x-cost evaluation.

Before QE review, `build-team-source-manifest` records every allowed non-self team text file and its
Git blob/hash. The complete regular UTF-8 text tree is freeze-bound and fingerprinted; opaque
prefit state and timestamp→target lookup artifacts are forbidden. The canonical worker stages only
Python plus the fixed small strategy-config names. It runs only under the implemented fail-closed
Linux namespace/Landlock/seccomp controls with a minimal environment, resource limits, and
900-second CPU and whole-run wall caps.

Phase 0 is a single-shot branch-local operation. The CLI, configuration, evaluator, methodology,
dependency lock, data manifest, snapshot builder, and common BTC artifacts are Git- and SHA-pinned.
The freeze record itself is committed in a later derived record commit, avoiding self-reference.
QR/QE review commits and evidence hashes are reverified at champion freeze. The source manifest is
required QE evidence. Commit each `freeze-team` state mutation before the next freeze. All ten
champion SHAs must be recorded before any canonical rerun, and every `finalize-team` executes two
independent byte-identical reruns. The tenth finalization creates the objective lock; commit it and
the tenth outputs/state in its unique first-add commit.

The Critic lock commit must be the objective record's direct child. Independent organizer
confirmations—not Critic allegations alone—select which cited integrity codes become DQs, and the
confirmation lock commit must directly follow the Critic lock. Performance never supplies a DQ
code. Only after confirmation may the user ballot be created and locked in the next direct-child
commit. Final scoring accepts only the canonical locked cohort and unchanged lock chain. Commit
the final leaderboard before freezing the winner; the winner record and paper-frozen state share
one unique first-add commit whose sole parent is that final-selection commit.
