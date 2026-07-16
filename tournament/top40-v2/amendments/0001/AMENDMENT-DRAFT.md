# Top-40 V2 Amendment 0001 — reviewed score diagnostics

Status: **IMPLEMENTED — HOLD NOTICE AND ORGANIZER REVIEW STILL REQUIRED**

This additive amendment preserves the original Phase-0 record and every byte it froze. It adds a
global administrative hold, two required organizer-private score-IC backfills, an exact deadline
toll, and an amendment-aware adapter that resumes the ordinary byte-frozen V2 orchestrator without
weakening schema or journal authority.

No production hold notice, review decision, integration freeze, activation state, or resume event is
part of this implementation commit. Those are separately authored lifecycle records.

## Authority and chronology

1. The organizer authors canonical `HOLD-NOTICE.json`. It binds the Phase-0 freeze, the exact legacy
   activation-state bytes, and the exact baseline research-journal head/count/latest timestamp.
2. `draft-amendment` verifies the notice's unique first-add commit and direct-parent chronology,
   migrates schema 2 to schema 3 atomically, and freezes the legacy projection while the hold is
   active.
3. The draft is committed exactly once as the notice commit's direct child.
4. `integration-review-material` derives the stable integration manifest SHA-256, exact reviewed
   file hashes, and the nonempty required-backfill list.
5. The organizer authors canonical `REVIEW.json` at the fixed path and commits it exactly once as
   the draft commit's direct child. `authorized_by` is descriptive provenance; it is not a claim of
   cryptographic authentication. The explicit decision fields are the review authority.
6. `freeze-amendment` reads that exact committed review, reconstructs and validates the integration
   manifest, and atomically binds the manifest, review, freeze, chain, and run state.
7. The organizer commits the generated integration manifest, freeze, chain, and state together as
   the review commit's direct child. Reservations remain fail-closed until that unique first-add
   freeze record commit exists.

All lifecycle event times except the immutable notice/review decision records come from the trusted
UTC clock. Publication uses the recoverable Git-path transaction intent.

## Required diagnostics

The integration freeze binds these exact completed candidates and their authoritative registration,
trial-result, source, risk, config, seed, runner-record, and archived target hashes:

- `team-01/rdf-core-h21-k3-g10`
- `team-01/rdf-ref-001`

The archived canonical replay authority is each candidate's `targets.parquet`; callers cannot supply
another target path. Before resume, only those exact backfills may be reserved. Every required item
must have one terminal result and no reservation may remain unresolved.

`run-diagnostic-backfill` is the sole result-recording interface. It invokes
`run_reserved_score_diagnostic`, derives CPU and wall time from the trusted runner, and hashes the
exact six owner-only artifacts itself. A completed private summary must bind the reservation and
contain exact replay evidence, pooled IC, six fold ICs, and six fold observation counts. The public
audit exposes only five derived booleans; numeric score evidence remains below the organizer-private
Git administrative path. Failed or interrupted runs record a bounded reason and no artifacts or
outcomes.

## Resume and ordinary orchestration

`resume-amendment` uses the trusted clock to toll the common research deadline by the exact
start-to-resume duration. The immutable activation-baseline state and journal hashes remain in
schema 3; after resume, the current legacy projection and current journal binding may advance.

`read_amendment_aware_legacy_state` and `amendment_aware_legacy_state_edit` validate the complete
Phase-0, notice, draft, review, integration, freeze, chain, audit, and private-evidence authority for
every ordinary operation. The edit adapter requires an inactive hold, validates append-only research
journal replacements and matching team trial counts, rejects protected or duplicate staged paths,
and publishes worktree outputs plus schema-3 state in one recoverable transaction. New one-shot
diagnostics remain available during resumed research.

The hash-bound `scripts/crypto_trade/__init__.py` canonical-script guard rejects ordinary canonical
Python invocation of the frozen legacy entrypoint once the state is no longer exact schema 2. This
closes accidental use of its destructive `init-teams --force` and arbitrary `--json-out` paths;
ordinary commands must use `scripts/top40_v2_amended_tournament.py` after activation. As throughout
this local tournament, a same-user administrator deliberately changing Python path semantics,
copying/running source through another loader, or writing files directly is outside the command
interface threat boundary and remains capable of destructive override.
