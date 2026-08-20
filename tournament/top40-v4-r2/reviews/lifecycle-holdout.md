# Independent adversarial R5 lifecycle and holdout review

Review date: 2026-08-20
Implementation reviewed: `c117f3b32c34de496cef651383e31cc34e1cc3fc`
Branch: `quant-portfolio-blind-top40-v4-r1-v2-restart3`

Scope: R5 all-15 trial-zero genesis, exact R4 incident authority and zero reuse, activation and
restart/idempotency, frozen v9 launch/candidate authority, per-team private model-state lifecycle,
strictly serial broker transitions, July-2026 holdout, and R1 compatibility.

Method: exact-byte source inspection, physical score-blind seed validation, focused temporary-root
mutation tests, and independent real permission-profile evidence. No predecessor score, result
summary, or feedback content was inspected. This review did not activate R5, launch a model, create
a private runtime in R5, or change competitive runtime state; this report is the only file modified
by this review.

## Gate status

**PASSED. Unresolved findings: 0.**

R5 is a genuine seed-only successor. Its schema-2 restart authority binds the abandoned R4
installed-skill incident, while the physical activation gate independently proves that no
predecessor artifact enters any lane. Launcher v9 binds the exact prompt, model command,
deterministic environment, private runtime, profile, and team kit. Per-phase Codex state is removed
before another prompt, including after normal failure and from validated partial-cleanup states
left by a process/host crash.

## Physical genesis and exact predecessor boundary

- Read-only `_fresh_restart_seed_state(..., activation_tests_present=False)` passed on the real R5
  root with mode `score-blind-fresh-restart`, 15 lanes, 94 files, byte-empty journal SHA-256
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
  The exact surface head is
  `20e5acba60e204dd850223d769e166ab6b0482c339ae496b1b22aaa6f839d73e`.
- The real tournament surface contains the committed seed files, all 45 one-byte-LF lane markers,
  and only the owner-controlled byte-empty journal and broker lock as ignored tournament nodes. It
  contains no activation freeze/output, research session, private model runtime, candidate,
  outbox, feedback, result, certificate, nomination, selection, or release. All 15 teams begin at
  trial zero.
- `FRESH-RESTART-AUTHORITY.json` has exact frozen SHA-256
  `aac191864a05460fa379e8b628a31e5739ce81141edf31c4a007d9470ccd146c`. Its R4
  `skill_boundary_incident` binds the stopped activation and activation test, implementation
  commit, 49-record journal and head, Team-02 decision launch, exposed skill hash, exact 478-file
  artifact-surface digest, no decision/outbox/certificate/nomination, invalid research provenance,
  and `results_reused=false`.
- The authority also retains the earlier private incident identities without importing them. The
  physical seed scanner admits no R4 candidate, source archive, research receipt, model output,
  work note, outbox, feedback, result/summary, certificate, journal record, or decision. The
  authority and all predecessor worktrees are outside every team profile.

## Activation, restart, and serial tournament lifecycle

- Activation requires the exact `restart3` branch and committed frozen scope. It validates the
  restart authority and self-hashed smoke receipt, exact-scans the 15-lane seed surface before and
  after the focused tests, binds the empty journal/94-file surface head, verifies the July-inclusive
  snapshot, and publishes one atomic freeze. Interrupted activation-test output remains bounded,
  non-authoritative scratch and is always replaced by a complete rerun.
- Genesis rejects every pre-existing research-session receipt, including old v7/v8 authorities and
  even a semantically current v9 receipt. A launch becomes admissible only after activation and
  must byte-equal the root/team/phase-current canonical v9 authority. Noncanonical JSON,
  duplicate-key/substituted payloads, wrong root/team/phase, stale profile, and changed team-kit or
  private-runtime identities fail closed.
- One owner-controlled regular/single-link kernel broker lease encloses direct-library and CLI
  model/evaluator entrypoints. `run-all` retains that lease while traversing the fixed 15-team list,
  so teams cannot overlap. Result commands retain the established pre-activation fail-fast check,
  broker/result lock order, and under-lock activation revalidation.
- Exact phase trial counts, accepted journal prefixes, immutable outbox archives, reconstructed
  feedback, terminal lanes, one-shot finalists, deterministic retirement on nomination-gate
  rejection, infrastructure-error resumability, strict decisions, DNF-to-cash accounting,
  empty/no-winner behavior, and atomic release remain intact.
- A crash before a team outbox permits an identical launch-authority retry. A complete authorized
  outbox can reconstruct candidate receipts before acceptance. Accepted trials resume from the
  exact journal prefix and are never repeated; an accepted request without a durable terminal is
  handled by the existing journal recovery rather than fabricating a new trial.

## Frozen v9 model runtime and phase-state cleanup

- Every team has a distinct organizer-private `HOME`, `CODEX_HOME`, and `TMPDIR`. The deterministic
  environment, exact Team/phase prompt, `gpt-5.6-sol` model, reasoning setting, command, Codex
  0.148.0 identity, skill-empty runtime, profile, and team kit are content-addressed in schema-2
  launch and candidate receipts.
- Child umask `077`, owner checks, owner-only directory/file modes, regular/single-link validation,
  bounded allowlists, and nofollow reads protect authentication and transient client state. The
  exact empty skill marker is the only admitted skill-catalog entry. Independent real-profile
  evidence passed all 11 assertions, including host skill/plugin denial, empty prompt catalog,
  own/peer private-auth denial, peer private-runtime read/write denial, network denial, lane
  isolation, and verified cleanup. Its disposable Team-01/02 runtimes were removed before the
  physical seed check above.
- Codex's known `installation_id` mode exception is narrowly normalized. Only an owner-controlled
  regular single-link file of at most 1024 bytes and mode `0600` or `0644` can be opened using
  `O_NOFOLLOW`; descriptor `fchmod(0600)`, file and parent-directory `fsync`, pre/post `fstat`,
  lexical inode/size/owner/link identity, and final mode are checked. Symlink, hard-link,
  non-regular, foreign-owner, oversized, and other-mode cases reject without following or mutating
  an external target. The complete tree is validated again before deletion.
- `ensure_private_model_runtime` resets admitted transient state before the catalog check and in
  that subprocess's `finally`. The live phase also calls it in its subprocess `finally`, so normal
  completion, nonzero exit, timeout, and Python-level interruption leave only authentication and
  the empty skill marker. If process/host death bypasses `finally`, the next probe performs the same
  reset before any new model prompt.
- Cleanup is restart-idempotent at nested kill points. The validator admits only subsets of the
  exact five known arg0 wrapper children; every present lock remains bounded owner-only regular
  single-link state, and every present wrapper remains an owner-controlled symlink to the exact
  pinned Codex binary. Private sandbox-TMP directories admit only the optional known `lock`, with
  the same regular-file checks when present. Unexpected names, types, modes, owners, or link targets
  reject before cleanup. Conditional unlink/rmdir then safely completes a prior crash prefix.
  Focused end-to-end tests proved retry from partial arg0 and missing-TMP-lock states and proved a
  wrong-target partial wrapper fails without mutation.

## July 2026 holdout and release semantics

- Config, manifest, activation checks, runner, and scoring retain the exclusive hard end
  `2026-08-01T00:00:00Z`. The manifest includes every July 2026 bar, excludes August, and the
  historical assessment counts all nine configured quarters.
- Each finalist still receives at most one silent serial historical observation. Failure consumes
  it, retry/replacement is forbidden, interim disclosure is absent, and the cohort is released
  atomically. Trial/field adjustment and the reporting ensemble's failed-sleeve-as-cash rule remain
  unchanged.
- No eligible historical candidate still means no winner; an empty finalist field and all-DNF
  field remain valid, deterministic terminal outcomes.

## Verification evidence

```text
exact implementation HEAD                          c117f3b32c34de496cef651383e31cc34e1cc3fc
R2 focused lifecycle/security/contract suite                                     121 passed
R1 compatibility suite                                                            24 passed
independent real OS permission-profile assertions                                  11 / 11
targeted partial-cleanup retry / wrong-target regression                          2 passed
physical seed lanes / bound files / journal records                           15 / 94 / 0
physical seed head                                                   20e5acba... exact
private runtime / activation / model launch created by this review                 0 / 0 / 0
holdout exclusive hard end                                      2026-08-01T00:00:00Z
```

The implementation gate is clear. Before activation, the organizer must update the adversarial
review record to bind the final three PASS/0 reports and commit the exact reviewed bytes; canonical
activation will correctly reject stale report hashes or a dirty frozen scope. This review neither
activated R5 nor launched a team.
