# Independent adversarial R9 lifecycle and holdout review

Review date: 2026-08-22
Implementation reviewed: `d5fc45d1c7ee9efe493b5304af9a30ae9cbdf84b`
Branch: `quant-portfolio-blind-top40-v4-r1-v2-restart7`

Scope: fresh 15-team R9 genesis and exact R8 incident/no-reuse authority; whole-batch
pre-acceptance admission and causal-source review; automatic strongest-successful representative
selection; successful refinement-truncation promotion; crash/restart/idempotency; minimum-five,
maximum-six field selection; zero-volatility and DNF cash accounting; one-team-at-a-time broker
execution; July-2026-inclusive holdout and atomic release; and R1/source-archive compatibility.

Method: exact-byte source inspection, read-only physical genesis checks, bounded temporary-root
adversarial mutation/crash regressions, and complete serial one-CPU test suites. No predecessor
score, summary, or feedback value was inspected. This review did not activate R9, launch a model or
team, invoke an evaluator, or mutate competitive runtime state; this report is the only file this
review modified.

## Gate status

**PASSED. Unresolved findings: 0.**

R9 is activation-ready on the reviewed bytes. Every successfully evaluated lane produces a
truthful strongest-successful representative, including a discovery-success lane whose score-blind
refinement batch cannot complete. Fewer than five successful team representatives fails closed;
no zero-finalist selection can be fabricated.

## Fresh genesis and predecessor isolation

- The physical R9 root remains preactivation genesis: 15 seed-only lanes, no local `.venv`, no
  activation freeze, journal, research-session runtime, candidate, feedback, populated outbox,
  nomination registry, selection freeze, or release artifact. The missing journal is the canonical
  preactivation state; organizer activation exclusively creates and verifies the byte-empty,
  owner-private, regular single-link journal before binding genesis.
- Schema-6 fresh-restart authority binds the stopped R8 minimum-finalist incident, including its
  activation/test/journal counts, one pending request, no nomination/selection facts, and explicit
  false result/research-provenance reuse. No R8 candidate, receipt, feedback, source, journal event,
  score, result, private model state, nomination, or selection is reused by R9.
- Activation still binds the exact clean commit/branch, frozen authority and model-smoke identities,
  15-lane seed surface, manifest-authorized snapshot, adversarial PASS/0 reports, and the canonical
  empty-journal transition across its test run. No model or evaluation can precede the freeze.

## Admission, source review, and trial authority

- Initial plus at most three score-blind repair sessions remain durably issued before process start,
  serialized by the process-wide broker lease, and bounded across crash/restart. Deterministic
  malformed or missing batches use distinct `batch_rejected` and `batch_abandoned` evidence;
  infrastructure failures do not fabricate a terminal, trial, or score.
- Exact causal source review now occurs after phase-bound candidate receipt validation but before
  `batch_preflighted`, acceptance, evaluator creation, market-data access, or score access. The
  durable batch event and process-local broker capability bind ordered candidate IDs, source hashes,
  receipt hashes, source-review hashes, purposes, phase, and outbox hash. Every acceptance and final
  nomination revalidates the exact live source and review authority.
- Deterministic candidate execution, invalid target output, static-source violations, or future
  invariance failure produce a score-blind batch rejection. Worker launch, namespace, protocol,
  timeout, filesystem, and wrapped `OSError` failures remain restart-resumable. Direct-library and
  organizer-CLI per-trial execution cannot mint or bypass the canonical broker capability.
- Source-review receipts use a pinned owner-private directory and a fixed staging inode. Payload
  fsync precedes no-replace hardlink publication; directory fsync makes the publication durable.
  Restart safely discards only an unbound private staging prefix or normalizes an exact same-inode
  two-name prefix. Wrong owner/mode/type/link topology, an unrelated hardlink, changed final bytes,
  or a conflicting final authority fails closed without mutating the outside target.

## Automatic representative and minimum-five lifecycle

- After twelve accepted trials, the broker automatically chooses the strongest successful candidate
  under the frozen robust ranking and compiles the certificate from immutable journal requests. A
  team with twelve failures may retire; a team with a success cannot use ordinary retirement or the
  disabled legacy decision path.
- Certificate breadth, neighborhood, failed sign-inversion, and other truthful qualification
  shortfalls preserve an honestly unqualified representative. Corrupt identity, citations, source,
  summary, target artifacts, or certificate bytes remain hard integrity failures. No fallible
  decision model or team-authored terminal decision participates.
- A score-blind rejected or abandoned refinement batch is first recorded with its exact evidence.
  If discovery contains a success, the serial broker validates that evidence and durably promotes
  the strongest discovery success; journal replay removes the transient retired projection only
  when the nomination references a real team success. Crash after disposition, archive, certificate,
  nomination file, or journal append resumes idempotently without repeating a trial or score.
- The truthful accepted `trial_count` remains eight for a truncated lane, while
  `selection_trial_count` is conservatively twelve for candidate ranking, nomination assessment,
  field confidence, selection freeze, and historical scoring. Deliberately stopping after discovery
  feedback therefore provides no multiplicity-penalty advantage, and missing refinement evidence
  cannot be mislabeled fully qualified.
- `run_team` promotes a successful truncated refinement lane in the same invocation, including the
  missing-batch phase-tail path; `run-all` continues the fixed 15-team order under one lease. On the
  narrow crash prefix before promotion, `close_is` revalidates terminal evidence and rejects before
  nomination-registry, freeze, or journal mutation. Replay independently forbids a selection that
  discards such a success.
- Close requires every lane resolved and at least five nominations. Fully qualified representatives
  rank first; robust-ranked representatives fill only the shortfall to five; at most six advance.
  Fewer than five successful teams raises before any selection freeze. All frozen failed gates and
  actual/selection trial counts remain visible in organizer authority.

## Ensemble, holdout, and release

- A successful zero/invalid-volatility finalist remains in the advancing identities with zero risky
  weight; unused capacity stays cash. Ensemble availability counts positive-weight sleeves, not
  nominal finalists. Historical DNF weights also move to cash without redistribution, and active
  sleeves plus effective cash must sum exactly to one. Empty/all-DNF championship output has no
  fabricated winner.
- Config, manifest, activation, runner, scoring, and release retain the exclusive hard end
  `2026-08-01T00:00:00Z`: every July 2026 day is included and August is excluded. Historical winner
  eligibility retains the configured nine-quarter assessment.
- Every finalist identity is journal-accepted before the first sealed snapshot read. Accepted but
  unstarted observations may resume; a started interruption is one terminal DNF with no retry or
  replacement. All rejected/abandoned batch evidence, including records later promoted to a
  nomination, is revalidated before close and again before historical selection/recovery, snapshot
  access, or release work.
- Release remains one atomic cohort publication. Private staging and journal authorization are
  hash-bound and recoverable; no interim finalist result, DNF, winner, or ensemble update is exposed.

## Verification evidence

```text
exact implementation HEAD                         d5fc45d1c7ee9efe493b5304af9a30ae9cbdf84b
focused final source-review crash-recovery regressions                           3 passed
complete R9 lifecycle/security/contract suite                                   198 passed
R1 and source-archive compatibility suites                                       29 passed
scoped Ruff / git diff --check                                             clean / clean
physical seed lanes / competitive journal records                          15 / 0
activation / evaluator / model launch / team launch by this review          0 / 0 / 0 / 0
holdout exclusive hard end                                     2026-08-01T00:00:00Z
```

Canonical activation must still bind this exact PASS/0 report and rerun its frozen activation
checks before any team starts. This review neither activated R9 nor launched a team.
