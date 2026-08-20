# Independent adversarial fresh-restart lifecycle and holdout review

Review date: 2026-08-20
Scope: exact current restart worktree on branch
`quant-portfolio-blind-top40-v4-r1-v2-restart`; fresh-restart authority, pretrial
alternative, activation and crash lifecycle, runtime validation, mechanism epochs, broker error
classification, seed state, July-2026 holdout, release accounting, and R1 compatibility.
Method: source and runtime-state inspection plus focused low-CPU adversarial tests in temporary
roots. No activation, team launch, candidate, journal record, result, selection, or release was
created in the tournament; this report is the only reviewed file modified.

## Gate status

**PASSED. Unresolved findings: 0.**

The exact restart is score-blind and seed-only. The fresh activation path now proves that fact at
the correct one-time boundary, binds it to the immutable activation scope, remains resumable across
test-output crash windows, and permits normal runtime artifacts only after activation. The earlier
static-authority, activation-test retry, and result-lock findings are closed.

## Fresh-restart and activation findings

- `FRESH-RESTART-AUTHORITY.json` has the exact hardcoded SHA-256
  `bae6aa65e9689c6c19b302bd3284cdda118449187705b05314392ae5853b5431`. Its
  predecessor activation, journal identity/count/head, two accepted/successful prefix records,
  discovery outbox, rejected preacceptance receipt, and source archive bindings match the preserved
  incident evidence. The authority explicitly forbids feedback disclosure and result reuse. No
  predecessor score value was read during this review.
- The real restart is on the required distinct restart branch. It has no activation freeze,
  activation-test output, research journal, research session, candidate, active outbox/feedback,
  IS/source result, nomination, selection, or historical release. All 15 lanes contain their exact
  frozen seed policy/brief/README and empty `.keep` markers; only the two frozen common reports are
  present under the report root. Canonical pre-activation status reports the genesis head, zero
  records, and no activation.
- Fresh activation exact-scans every expected frozen tournament/report seed file, all 45 lane
  markers, and the byte-empty journal created by the canonical organizer. Exact directory entry
  sets reject missing or extra residue. Files must be owner-controlled, regular, single-linked,
  stable, and bounded; symlinks, hard links, special nodes, unsafe parents, nonempty journal/marker,
  candidate/outbox/feedback/work residue, research receipts, results, selection, release, and
  incident ambiguity all fail closed.
- The competitive seed surface is checked before activation work and again after focused tests.
  The only transition artifacts admitted are a safe broker lock, the canonical actively owned
  result-lock marker, and a safe prior activation-test scratch file. Test scratch is never
  authoritative: every retry reruns and atomically replaces it. A focused failure-then-retry probe
  now reaches a successful freeze; failures and crashes before publication leave no freeze and do
  not strand the next canonical attempt.
- The activation record binds restart mode, exact authority hash, empty-journal hash, 15-lane
  count, 94-file competitive surface count, and chained surface head. Activation compares that
  head to the committed activation-scope entries before tests. Validation recomputes the expected
  count and head from the immutable scope entries rather than accepting an arbitrary digest, then
  repeats the normal record hash, branch, config, manifest, review, Git ancestry, current scope,
  test-output, and universe checks.
- Post-activation validation deliberately does not rescan the genesis runtime tree. This is the
  correct lifecycle split: accepted candidates, journal records, feedback, and results may then
  exist, while the immutable activation record continues to prove the earlier clean boundary.
  Appearance/removal of an incident final after activation changes the required record schema and
  fails closed; result and launcher entrypoints also require the exact fresh/incident authority
  both before and under their serial leases.
- Canonical activation is serialized by the result lock but remains outside the broker lease so
  its focused-test child can acquire the broker without ABBA deadlock. The result lock now uses
  no-follow directory/file opens, owner/regular/single-link checks before mutation, and a post-flock
  lexical inode check. Hard-link and symlink probes reject before changing the aliased target.
  Canonical activation with its live PID marker reaches the exact 94-file fresh binding.
- Freeze publication remains exclusive, atomic, file-and-parent-fsynced, and one-shot. A concurrent
  or resumed publisher cannot overwrite an existing freeze. Pre-activation result calls fail before
  broker acquisition, preserving the established activation/result lock order.

## Tournament lifecycle, broker, and holdout findings

- Mechanism history is ordered by accepted trial number. The first candidate establishes an epoch.
  A descriptive `control-ablation` or `role-check` may differ in prose only when it names an already
  accepted parent in the current epoch. Unparented and old-epoch controls reject. A real
  `mechanism-pivot` must change mechanism, cannot be the first candidate, and is allowed once;
  no-op and second pivots reject before acceptance. The rules and clean-room prompts disclose this
  contract equally to all teams without predecessor information.
- Batch consumption preserves the original preacceptance exception when no accepted journal record
  exists. It consumes only a deterministic candidate-source rejection that has a durable terminal
  disposition; accepted infrastructure failures without a terminal remain resumable. Decision
  values and schemas are strict, launch authority and exact phase/trial prefixes are revalidated,
  and completed feedback is reconstructed from the journal and immutable archived outbox.
- All model/evaluator work remains protected by the owner-controlled process-wide broker lease and
  runs serially. Direct-library and CLI paths repeat activation, incident/fresh authority, journal,
  terminal, archive, and launch checks inside their locks. Seed-only restart therefore cannot
  inherit a trial, terminal, nomination, or selection from the aborted predecessor.
- The frozen hard end remains exclusively `2026-08-01T00:00:00Z`: every July 2026 daily bar and all
  nine required holdout quarters are present, while August observations are excluded. Config and
  manifest mutations that shorten the boundary fail activation.
- Previously reviewed DNF-to-effective-cash disclosure, ensemble weight accounting, trial/field
  adjustment, one-shot finalist handling, no-winner/empty release behavior, journal sequencing,
  and atomic historical publication remain unchanged and covered by the focused suite.

## Focused verification executed

```text
tests/tournament/test_top40_v4_r2.py                    106 passed
tests/tournament/test_top40_v4.py                        24 passed
Ruff                                                        passed
git diff --check                                             passed
canonical pre-activation validate/status         0 records / not activated
fresh seed residue/link/transition mutations                 rejected
failed activation tests followed by retry           rerun / freeze succeeds
canonical live result lock / linked lock targets      accepted / unchanged
mechanism current-parent control / old parent        accepted / rejected
mechanism no-op pivot / second pivot                rejected / rejected
broker preacceptance / terminal / infrastructure   preserved / consumed / resumable
holdout hard end                              2026-08-01T00:00:00Z
```

The lifecycle/holdout gate is clear for the organizer to commit the reviewed frozen bytes and run
the separate canonical activation step. This review did not activate the tournament or start a
team.
