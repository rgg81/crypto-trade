# Independent adversarial lifecycle and holdout final re-review

Review date: 2026-08-20
Scope: final Top-40 V4-R2 lifecycle, direct-library and broker authority, protected serialization,
restart/idempotency, nomination terminal handling, July-inclusive holdout, historical one-shot
execution, release recovery, and DNF ensemble cash.
Method: exact-byte read-only inspection, focused single-process tests, and isolated `/tmp`
simulations. No tournament, candidate, or implementation state was changed; this report is the
only reviewed file modified.

## Gate status

**PASSED. Unresolved findings: 0. ACTIVATION APPROVED.**

The three findings from the preceding failed pass are closed. No new lifecycle, holdout, journal,
broker, ensemble, release, or terminal-disposition defect was found in the current reviewed bytes.

## Remediation verified

### Direct launch and exact lifecycle authority

- `launch_team_phase` is protected by the same process-wide lease as broker commands and performs
  full activation validation inside that lease before any team process or launch authority is
  created.
- The low-level launcher independently rejects sealed selection, a nominated/retired lane, a wrong
  trial count, an existing current-phase archive, an existing outbox, and missing or contradictory
  prior-phase evidence.
- Prior discovery/refinement proof is reconstructed from the unique content-addressed archive and
  journal: exact candidate order, entrypoint, purpose, trials 1-8 or 9-12, terminal status,
  journal-bound successful summary or failure, and the complete feedback object must agree.
- An isolated valid discovery authority permitted refinement; adding a current refinement archive
  rejected the same launch. Eight shape-valid `null` feedback rows are rejected rather than
  treated as completed authority.

### Candidate rejection versus resumable infrastructure

- Exact static/source-identity and append/corrupt-future violations remain explicit
  `CandidateSourceRejectedError` results.
- Deterministic candidate `StrategyExecutionError` and the exact invalid-target response family are
  translated to that rejection type, so decision consumption records one terminal retirement.
- Worker launch, timeout, protocol, sandbox, and storage failures remain infrastructure errors.
  Raw and wrapped `ResearchRuntimeError` storage errors escape without retirement, and an
  `OrchestratorError` carrying an `OSError` cause remains resumable.
- Independent probes produced `CandidateSourceRejectedError` for candidate execution and a
  non-finite target, while a worker timeout remained `StrategySandboxError`.

### Shared value validation

- One bounded-single-line predicate now governs launch-side batch purposes and retirement reasons
  and broker-side consumption. It enforces string type, nonempty trimmed text, the 2,048-character
  limit, and rejection of ASCII controls and DEL.
- Nomination validation at both boundaries also requires the safe candidate-ID grammar and exact
  `work/research-certificate.json` path. Newline, tab, and DEL regressions pass at launch and
  consume.

## Complete lifecycle and holdout properties verified

- The protected broker lease uses no-follow directory/file opens, an owner-controlled single-link
  regular inode, post-flock descriptor/path identity, process reentrancy, and same-root nesting.
  Public broker result functions plus direct organizer/runtime entrypoints are serialized.
- Batch consumption validates activation, launch authority, sealed/terminal state, the exact phase
  trial range, and accepted candidate prefix before `run_is`. Refinement requires completed
  discovery. Pending accepted work is closed as consumed failure and recovery remains idempotent.
- Decision consumption requires exactly twelve terminal trials, journal-bound discovery and
  refinement feedback/archives, and decision launch authority. Deterministic source, certificate,
  and eligibility rejection retires the lane; infrastructure failure leaves it resumable.
- Feedback is lane-local and contains no interim field disclosure. Immutable launch/candidate
  receipts, feedback, archives, accepted requests, terminal records, and selection state form one
  consistent authority chain across crash/restart paths.
- Critical mutations enabling raw holdout visibility, immediate finalist feedback, unrestricted
  eligibility, a winner-eligible ensemble, or research networking fail closed.
- The historical holdout is exactly `[2024-07-01T00:00:00Z,
  2026-08-01T00:00:00Z)`. Verified bars end at `2026-07-31T16:00:00Z`; no August timestamp is
  admitted; the release contains all 761 daily rows through July 31. Winner breadth remains five
  positive quarters among the nine calendar quarters touched.
- Accepted trials are contiguous and hash-chained. All 15 lanes must reach nomination or retirement
  before field adjustment; field confidence uses all accepted trials without leaking interim field
  results.
- Every finalist is durably batch-accepted before the first private snapshot read. Historical start
  consumes the single authorized observation; interruption becomes a non-retryable DNF, and no
  second start or terminal disposition is accepted.
- Empty brackets and no-eligible-winner outcomes are explicit valid results. The ensemble remains
  ineligible to win.
- Release is hash-inventoried, journal-authorized, atomically promoted, and recoverable after an
  interrupted staging/promotion sequence. A DNF sleeve is disclosed and transferred to effective
  cash without redistribution; active weights plus cash must equal one.

## Focused verification executed

```text
tests/tournament/test_top40_v4_r2.py                                  53 passed
focused shared journal/empty/release/DNF recovery tests                8 passed
valid prior phase -> refinement launch                              accepted
existing current-phase archive -> same launch                      rejected
contradictory prior feedback                                       rejected
candidate execution / invalid targets             terminal candidate rejection
worker timeout                                      resumable infrastructure error
newline / tab / DEL decision and purpose values                    rejected
```

This review found no unresolved condition requiring remediation before tournament activation.
