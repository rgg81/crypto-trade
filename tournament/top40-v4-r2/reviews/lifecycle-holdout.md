# Independent adversarial R6 lifecycle and holdout review

Review date: 2026-08-21
Implementation reviewed: `9d95e7c69706744c357c0b10bd20472a38942862`
Branch: `quant-portfolio-blind-top40-v4-r1-v2-restart4`

Scope: R6 all-15 trial-zero genesis; exact R5 evaluator-worker incident preservation and zero
reuse; activation, crash recovery, and restart idempotency; frozen launcher v10 and worker
bootstrap; broker admission, terminal, and infrastructure transitions; strictly serial execution;
July-2026 holdout, selection, and release; and R1 compatibility.

Method: exact-byte source inspection, read-only physical seed/data-topology checks, focused
temporary-root adversarial attacks, and the complete R2 and R1 test suites. No predecessor score,
result summary, or feedback value was inspected. This review did not activate R6, launch a model or
team, create a private model runtime, or mutate competitive runtime state; this report is the only
file modified by this review.

## Gate status

**PASSED. Unresolved findings: 0.**

R6 is a genuine seed-only successor. Its schema-3 authority preserves the stopped R5 worker
bootstrap incident without importing any candidate, receipt, feedback, research state, or result.
The activation transition, live journal, missing-marker recovery, worker startup, one-team-at-a-time
broker, and July-inclusive holdout all fail closed on the reviewed bytes.

## Physical genesis and predecessor boundary

- The real R6 root is on the exact `restart4` branch and clean reviewed HEAD. It has no lifecycle
  journal, activation freeze/output, research session, IS report, nomination, selection, private
  historical release, or team/model runtime. Canonical activation exclusively creates the exact
  empty journal before proving the 94-file, 15-lane seed binding.
- All 15 lane roots contain only their committed seed files. All 45 frozen `.keep` markers are
  one-byte LF regular single-link files. The only ignored tournament node is the owner-controlled,
  byte-empty, regular single-link mode-0600 broker lock. Every lane therefore begins at trial zero.
- `FRESH-RESTART-AUTHORITY.json` has frozen SHA-256
  `f71896a9cd2da6071441bd65f5eeb42f2c2b0c953de016998019d082bc234e68`.
  Its R5 `worker_bootstrap_incident` binds the stopped activation/test/journal and launch identities,
  16-record journal, eight accepted infrastructure failures and zero successes, exact 75-file
  competitive-surface digest, disclosed discovery feedback but no holdout disclosure, interrupted
  refinement, preserved private residue, and explicit `research_provenance_reused=false` and
  `results_reused=false`.
- The physical raw authority contains 94,816 regular single-link files and no symlink. The mandatory
  single-core full replay passed manifest SHA-256
  `c21fdcefc39961cd4408277e6cbb4833c31178cf86fa5d166499a3df6a8e7af7` with exclusive hard end
  `2026-08-01T00:00:00Z`.

## Activation, journal, and crash/restart semantics

- Activation requires the exact `restart4` branch, a clean exact implementation HEAD, the frozen
  authority and smoke receipt, the complete manifest-authorized raw surface, and the exact seed-only
  topology before and after focused tests. It atomically binds the 15 lanes, synthetic empty-journal
  identity, 94-file seed chain, full snapshot, and reviewed infrastructure. Interrupted test output
  remains bounded non-authoritative scratch and is always replaced by a complete rerun.
- Journal initialization pins an owner-controlled parent and opens or exclusively creates only an
  owner-owned regular single-link mode-0600 byte-empty file through nofollow descriptors. It never
  invokes runtime tail recovery. Arbitrary fragments and hardlinked external evidence reject without
  mutation; a crash after valid exclusive creation is an idempotent activation prefix.
- Preactivation `status`, `validate --pre-activation`, `run-team`, and `run-all` cannot invoke journal
  tail recovery. The read-only commands accept only an absent or exact empty bootstrap journal;
  `run-team` validates activation before its first journal read, including its terminal fast path.
  Direct and canonical CLI fragment-preservation regressions passed.
- Runtime `read` and `append` pin both parent and journal, require owner/regular/single-link/mode-0600
  authority, lock the descriptor, and recheck lexical inode and parent identity before and after any
  recovery or append. Hardlink and pathname-substitution attacks reject without altering either
  object. R2 append never recreates a missing journal. An unterminated append can still recover only
  to a completely replayable newline-committed prefix.
- A model or host crash that removes only an `outbox/.keep` or `work/.keep` cannot strand a lane.
  Direct launch and every broker consume/launch/run-team resume path restore absent one-byte markers
  under the broker lease before activation validation. A two-pass full-lane check rejects wrong
  bytes, modes, ownership, links, targets, or unsafe parents before creating any missing marker;
  partial restoration is itself safely retryable.

## Launcher v10, worker bootstrap, and serial broker lifecycle

- Launcher v10 preserves the reviewed private, networkless, empty-skill model runtime and exact
  prompt/command/profile/team-kit bindings. Per-phase client state is removed before another prompt
  and in subprocess `finally`; validated partial cleanup prefixes remain retryable, while unexpected
  names, types, modes, owners, or targets fail closed.
- The R5 failure occurred before candidate initialization because the reconstructed worker
  environment omitted the frozen package bootstrap. R6 supplies only the exact worktree `src` path
  so Python can resolve `_strategy_worker_v4`; the worker then masks the repository, remaps the
  staged runtime, installs namespace/Landlock/seccomp restrictions, and only then imports candidate
  code. The real sanitized namespaced-startup regression passes.
- One reentrant process-wide broker lease covers direct-library and CLI model/evaluator entrypoints.
  `run-all` holds it while traversing the fixed 15-team sequence, so no two teams overlap. Result
  commands retain the preactivation fail-fast check, broker/result lock order, and under-lock
  activation revalidation.
- Exact phase counts and accepted journal prefixes, immutable outbox archives, reconstructed
  feedback, terminal lanes, strict decision values, deterministic nomination-gate retirement,
  infrastructure-error resumability, one-shot finalist/DNF handling, empty/no-winner outcomes, and
  atomic historical release remain intact. Accepted requests are never repeated or replaced.

## July 2026 holdout and release invariants

- Config, manifest, activation, runner, and scoring share the exclusive hard end
  `2026-08-01T00:00:00Z`: every July 2026 bar is included, August is excluded, and historical
  assessment spans all nine configured quarters.
- Each finalist receives at most one silent serial historical observation. A started failure is a
  terminal DNF, retry or replacement is forbidden, and accepted-but-unstarted finalists retain
  their one authorized observation across restart. No interim finalist result is disclosed.
- Trial/field multiple-testing adjustment, minimum-quarter eligibility, failed-sleeve-as-cash
  ensemble accounting, deterministic all-DNF/empty-field behavior, and one atomic cohort release
  remain unchanged.

## Verification evidence

```text
exact implementation HEAD                          9d95e7c69706744c357c0b10bd20472a38942862
focused journal/marker/activation adversarial regressions                          12 passed
complete R2 lifecycle/security/contract suite                                     135 passed
R1 compatibility suite                                                             24 passed
physical seed lanes / activation / journal records                              15 / 0 / 0
physical raw authority regular single-link files                                  94,816
full raw snapshot replay / manifest authority                              PASSED / c21fdcef...
private runtime / model launch / team launch by this review                       0 / 0 / 0
holdout exclusive hard end                                      2026-08-01T00:00:00Z
```

The lifecycle/holdout gate is clear on the exact reviewed bytes. Canonical activation must still
bind the final PASS/0 review record and run its own focused tests before any team is started. This
review neither activated R6 nor launched a team.
