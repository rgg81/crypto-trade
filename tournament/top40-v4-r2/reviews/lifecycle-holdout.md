# Independent adversarial R8 lifecycle and holdout review

Review date: 2026-08-21
Implementation reviewed: `8335719049ddce0fb5b928a3905017b388b1fccd`
Branch: `quant-portfolio-blind-top40-v4-r1-v2-restart6`

Scope: fresh 15-team trial-zero genesis and exact R7 incident/no-reuse boundary; score-blind
whole-batch admission repair with one initial session and at most three repairs; missing, malformed,
unchanged, and source-changing outputs; crash/restart and immutable terminal evidence; refinement
history; terminal versus infrastructure classification; one-team-at-a-time broker execution;
July-2026 holdout, selection, and atomic release; and R1/source-archive compatibility.

Method: exact-byte source inspection, read-only physical R8 topology checks, bounded temporary-root
adversarial crash/corruption regressions, and complete serial one-CPU test suites. No predecessor
score, summary, or feedback value was inspected. This review did not activate R8, launch a model or
team, invoke an evaluator, or mutate competitive runtime state; this report is the only modified
file.

## Gate status

**PASSED. Unresolved findings: 0.**

R8 is activation-ready on the reviewed bytes. Repair sessions are score-blind, globally serial,
durably capped across restart, and incapable of opening a trial or score before exact whole-batch
authority exists. Exhausted malformed and missing batches have distinct evidence-preserving
terminal paths, while infrastructure failures remain fail-closed at their documented boundary.

## Fresh genesis and R7 boundary

- The exact physical R8 root was clean at the reviewed HEAD and `restart6` branch before this report
  edit. All 15 lanes are at trial zero. The journal, activation freeze/output, research sessions,
  candidate receipts, feedback, populated outboxes, results, selection, and release are absent. All
  45 committed lane markers retain their frozen regular single-link one-byte LF identity.
- Schema-5 fresh-restart authority binds the completed R7 zero-candidate incident, including its
  activation/review/journal/selection/release and generated-artifact identities. R8 imports none of
  R7's candidates, receipts, launch records, outboxes, journal events, feedback, selection, private
  runtime, or results; `research_provenance_reused` and `results_reused` are both false.
- Activation still requires the exact clean implementation commit and branch, authority, frozen
  smoke/profile/team-kit identities, manifest-authorized snapshot, 15-lane seed topology, and
  canonical empty journal before and after its tests. Interrupted bootstrap output remains
  non-authoritative and cannot convert runtime residue into genesis.

## Score-blind repair state machine

- The launcher durably issues one private canonical session authority before the initial model
  process and before each of at most three repair processes. Session numbers 0 through 3 bind the
  team, phase, launch authority, session kind, score-data-closed state, and exact preceding attempt.
  A crash can conservatively consume an issued slot but can never duplicate it or grant a fifth
  process.
- Each completed/ambiguous issued session is inspected as a complete batch before candidate receipts,
  journal acceptance, evaluator creation, market-data access, or score access. Admission validates
  strict outbox shape, ordered IDs and purposes, current captured source, attestation, the disclosed
  static semantic subset, metadata, mechanism history, phase range, and refinement disjointness.
  Refinement starts from the exact accepted discovery history and requires the completed discovery
  feedback/archive authority.
- Deterministic findings are stored in owner-private, nofollow, regular single-link canonical
  attempt records. Attempt numbers 1 through 4 bind outbox hash, ordered candidate IDs, source
  hashes, normalized findings, phase, and `score_data_opened=false`. Changed source with unchanged
  outbox creates new authority when its inspection changes; unchanged post-session output still
  consumes exactly the already-issued opportunity.
- Lane-visible admission feedback is derived byte-exactly from each durable attempt. A crash after
  private attempt fsync but before feedback publication is recovered by reconstructing the missing
  file; an existing conflicting file rejects. The complete feedback chain is recovered/validated
  before another session can be issued, so no repair process runs without its authorized guidance.
- A valid repaired batch receives candidate receipts only after its complete score-blind inspection,
  then enters the existing canonical-broker-only durable `batch_preflighted` path. Ordered source
  and canonical receipt hashes, accepted prefix, purpose, entrypoint, phase, and live broker-frame
  capability are revalidated before every accepted trial. Direct-library/CLI trial or fabricated
  rejection/abandonment paths reject before mutation.

## Exhaustion, crash recovery, and serial lifecycle

- A still-malformed batch after the initial session and three repairs retains its exact live outbox,
  is terminally `batch_rejected` without a trial or score, and is moved to an owner-private,
  regular single-link content-addressed archive. Missing, corrupt, substituted, linked, permission-
  drifted, or digest-mismatched archives fail closed.
- A batch that remains absent produces exact attempt-04/session-03 authority and terminal
  `batch_abandoned`; no outbox is fabricated or archived. Restart recognizes the exhausted state
  without another model process. The journal binds the attempt path/hash, exact phase boundary, no
  preflight, no pending accepted request, and zero new trials.
- `run_team` idempotently recovers both terminal forms. `run-all` retains the process-wide broker
  lease across the fixed 15-team order, so a terminal rejection/abandonment advances to the next
  team while infrastructure exceptions stop safely. Direct launch, consume, result, and canonical
  CLI paths use the same reentrant lease and under-lock activation/lifecycle checks; no teams can
  overlap.
- Filesystem, isolation, lock, and other failures before durable session issuance remain resumable
  without consuming a repair or trial. Once a private issue is durable, an ambiguous process/host
  failure consumes only that authorized slot; restart inspects the resulting unchanged, changed,
  malformed, valid, or missing output without issuing a duplicate.
- Selection close revalidates every retired score-blind authority before registry or freeze writes:
  `batch_rejected` requires the exact immutable outbox archive and no live outbox;
  `batch_abandoned` requires exact attempt/session exhaustion and no live/archive outbox. Historical
  release repeats the same validation immediately after journal read and before selection recovery,
  historical acceptance, snapshot access, or release recovery. Evidence loss or corruption cannot
  be hidden by a prior selection freeze.

## July 2026 holdout and release

- Config, manifest, activation, runner, and scoring retain the exclusive hard end
  `2026-08-01T00:00:00Z`: all of July 2026 is included and August is excluded. Historical assessment
  remains the configured nine quarters with the minimum-positive-quarter eligibility gate.
- Every finalist identity is durably accepted before the first sealed snapshot read. Accepted but
  unstarted observations resume once; a started interruption is terminal DNF and cannot be retried
  or replaced. No interim finalist result is disclosed.
- Trial/field multiplicity adjustment counts only accepted trials. Batch rejection/abandonment adds
  none. Minimum-two-sleeve ensemble availability, failed-sleeve weight to cash without
  redistribution, all-DNF/empty-field no-winner behavior, and the single atomic cohort release
  remain intact.

## Verification evidence

```text
exact implementation HEAD                          8335719049ddce0fb5b928a3905017b388b1fccd
focused repair/crash/evidence/serial/holdout adversarial regressions              26 passed
complete R8 lifecycle/security/contract suite                                    177 passed
R1 and source-archive compatibility suites                                        29 passed
scoped Ruff / git diff --check                                      clean / clean before report
physical seed lanes / markers / journal records                            15 / 45 / 0
activation / evaluator / model launch / team launch by this review           0 / 0 / 0 / 0
holdout exclusive hard end                                      2026-08-01T00:00:00Z
```

Canonical activation must still bind this final PASS/0 report and rerun its frozen activation
checks before any team is started. This review neither activated R8 nor launched a team.
