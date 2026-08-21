# Independent adversarial R7 lifecycle and holdout review

Review date: 2026-08-21
Implementation reviewed: `e4b87be0e49362e321fb3e2781d8c10812918d31`
Branch: `quant-portfolio-blind-top40-v4-r1-v2-restart5`

Scope: fresh all-15-team trial-zero genesis; exact preservation of the stopped R6 incident with no
competitive reuse; activation, restart, crash, and idempotency; canonical-broker-only whole-batch
preflight and rejection; ordinary retirement; immutable rejected-batch recovery; one-team-at-a-time
execution; July-2026 holdout, selection, and release; and R1/source-archive compatibility.

Method: exact-byte source inspection, read-only physical R7 topology checks, bounded temporary-root
adversarial regressions, and the complete R7 and R1/source-archive test suites with one CPU. No
predecessor score, result summary, feedback value, evaluator, model, or team was read or run. This
review did not activate R7 or mutate competitive runtime state; this report is the only modified
file.

## Gate status

**PASSED. Unresolved findings: 0.**

The reviewed R7 bytes are activation-ready. They enforce whole-batch admission before any score or
trial is consumed, distinguish a zero-trial batch rejection from ordinary retirement, preserve
retryable infrastructure failures, and retain the July-inclusive holdout and one-shot release
rules.

## Fresh genesis and predecessor boundary

- The exact physical R7 root was clean at the reviewed HEAD and branch before this report edit. All
  15 lanes are at trial zero: the journal, activation freeze/output, research sessions, feedback,
  and populated outboxes are absent. All 45 committed lane markers are regular single-link one-byte
  LF files; the broker lock is an owner-controlled, regular single-link, byte-empty mode-0600 file.
- The frozen fresh-restart authority binds the stopped R6 incident by exact artifact identities and
  records the partial Team-02 discovery boundary without importing it into R7. R7 contains no
  predecessor candidate, receipt, feedback, accepted trial, result, or private research runtime;
  its authority explicitly forbids research provenance and result reuse.
- Activation still requires the exact clean implementation commit, restart branch, authority,
  manifest/snapshot, smoke receipt, frozen seed surface, 15-lane topology, and canonical empty
  journal. These checks are repeated around activation tests and before the atomic freeze, so an
  interrupted or contaminated bootstrap remains non-authoritative and retryable only from a
  validated prefix.

## Whole-batch admission and terminal lifecycle

- Discovery and refinement batches are completely preflighted before the first evaluator call or
  accepted trial. Admission binds the stable outbox bytes, ordered candidate IDs and source hashes,
  exact phase range and accepted prefix, purpose, entrypoint, mechanism history, current source
  authority, and candidate receipt. Refinement additionally requires IDs disjoint from discovery
  and revalidates the completed discovery feedback and immutable archive before either preflight or
  rejection can create a refinement terminal transition.
- Preflight success is durably journaled as `batch_preflighted`; replay must reconstruct the exact
  phase, outbox hash, candidate order, source hashes, canonical receipt hashes, and accepted-prefix
  boundary. Replay also binds each accepted request's research-session hash to the corresponding
  receipt hash. A crash after that append resumes from the same authority rather than rerunning
  model research or admitting a different batch.
- Batch capabilities are process-local and valid only in the live canonical broker call frame. The
  frame is bound by Python `FrameType` identity, exact script/code identity, root, team, phase,
  outbox, candidate IDs, sources, and module seal. Direct-library/CLI preflight-to-`run_is` bypass,
  fabricated rejection, stale capability, and a pending accepted request all reject before result
  mutation.
- A deterministic whole-batch defect at discovery trial 0 or refinement trial 8 writes the distinct
  `batch_rejected` transition and archives the rejected outbox. It does not fabricate a trial or
  weaken ordinary retirement, which still requires the normal accepted-trial threshold. The final
  rejection path repeats activation, journal-head, phase-boundary, outbox, source, and prior-phase
  checks under the broker lease.
- Candidate receipts are stable nofollow reads of owner-owned regular single-link mode-0600 files.
  They must be exact canonical pretty-printed JSON with one trailing LF; duplicate keys, non-finite
  values, reordered or compact encodings, missing LF, substitution, and permission drift reject.
  Final `run_is` admission repeats validation against the capability-bound phase and exact receipt
  hash before mechanism validation, journal acceptance, evaluator creation, or score access.
  Deterministic receipt/source mismatches are terminal batch defects, while base or wrapped
  `OSError` infrastructure failures remain resumable without consuming a trial.
- Malformed launcher output with a safely published exact outbox is routed through the same broker
  preflight and terminal classification without a second model launch. If no authoritative outbox
  was published, the failure remains an infrastructure interruption. No score is read on either
  preacceptance path.
- Rejected archives require exact owner-private topology and stable nofollow owner/regular/
  single-link files whose content digest matches the archive name and journal record. Crash recovery
  accepts only the exact journal/archive state; missing, corrupt, symlinked, hardlinked, substituted,
  or mismatched evidence fails closed without mutation.

## Restart, serialization, selection, and release

- One reentrant process-wide broker lease covers direct-library and canonical CLI model/evaluator
  entrypoints. `run-all` retains that lease across the fixed 15-team traversal, and each result path
  repeats activation and phase authority checks under the broker/result-lock order. Teams therefore
  run strictly one at a time.
- Accepted requests are never replaced or repeated. Unterminated infrastructure work remains
  retryable; deterministic preacceptance rejection is terminal; accepted evaluator failures follow
  the existing terminal record rules. Exact phase counts, immutable feedback/outbox evidence,
  nomination retirement, finalist one-shot/DNF handling, and restart reconstruction remain bound to
  the journal sequence.
- Selection counts only accepted trials. A batch-rejected zero-trial lane can be represented as
  terminal without inflating field size or trial count. Trial/field multiplicity adjustment,
  minimum-positive-quarter eligibility, deterministic empty/no-winner behavior, and minimum
  two-sleeve ensemble construction remain fail closed.
- Started historical failures are terminal DNF and cannot be retried or replaced; accepted but
  unstarted work resumes exactly once. DNF sleeve weight becomes cash rather than being redistributed,
  including the all-DNF case. Historical results remain undisclosed until the single atomic cohort
  release.

## July 2026 holdout

- Config, manifest, activation, runner, and scoring share the exclusive hard end
  `2026-08-01T00:00:00Z`: all of July 2026 is included and August is excluded. Historical assessment
  remains the configured nine quarters with the minimum-positive-quarter eligibility gate.
- The tests exercise the July boundary, truncated/out-of-range snapshot rejection, finalist
  one-shot behavior, DNF-to-cash disclosure, empty/no-winner handling, and atomic release. No
  holdout value was inspected during this review.

## Verification evidence

```text
exact implementation HEAD                          e4b87be0e49362e321fb3e2781d8c10812918d31
focused batch/receipt/archive/restart adversarial regressions                     26 passed
complete R7 lifecycle/security/contract suite                                    165 passed
R1 and source-archive compatibility suites                                        29 passed
Ruff / git diff --check                                            clean / clean before report
physical seed lanes / markers / journal records                            15 / 45 / 0
activation / model launch / team launch by this review                       0 / 0 / 0
holdout exclusive hard end                                      2026-08-01T00:00:00Z
```

Canonical activation must still bind this final PASS/0 report and rerun its own frozen activation
checks before any team is started. This review neither activated R7 nor launched a team.
