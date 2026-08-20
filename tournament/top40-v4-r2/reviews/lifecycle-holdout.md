# Independent adversarial activation-concurrency and lifecycle final re-review

Review date: 2026-08-20
Scope: final Top-40 V4-R2 activation bootstrap, broker/result lock ordering, direct-library and
canonical CLI overlap, pre-freeze model/evaluator gating, restart artifacts, and previously approved
lifecycle/holdout protections.
Method: exact-byte read-only inspection, focused single-process tests, and isolated multiprocess
lock-order simulations under `/tmp`. No tournament, candidate, or implementation state was changed;
this report is the only reviewed file modified.

## Gate status

**PASSED. Unresolved findings: 0. ACTIVATION APPROVED.**

The activation/pytest self-deadlock and the subsequent three-party ABBA finding are both closed on
the current bytes. No new overlap, activation bypass, lifecycle, holdout, journal, ensemble, or
release defect was found.

## Activation concurrency remediation verified

- Canonical activation is the sole bootstrap exception to the broker lease. It remains serialized
  by `.result-command.lock`, while its focused-test child is free to exercise broker-protected public
  commands.
- `serialized_activated_r2_command` performs a complete frozen-authority validation with raw
  snapshot replay disabled before broker acquisition. `run_is`, `nominate`, `retire`, `close_is`,
  and `historical_release` all use this boundary for direct-library calls.
- Each result function repeats activation validation after broker acquisition and while holding the
  result lock. This second check is the authoritative TOCTOU boundary; the first check exists only
  to prevent a pre-activation command from retaining the broker while activation owns the result
  lock.
- The canonical CLI no longer wraps result, status, or validation commands in an outer broker
  lease. It delegates serialization to their internal decorators. Only the read-only isolation
  audit receives a CLI-supplied broker lease; activation remains outside it.
- Team broker launch/consume commands validate activation before model or evaluator work and do not
  wait for the result lock while activation is incomplete. A valid freeze can appear only after the
  activation test child has exited.

## Exact former deadlock reproduced after remediation

The former sequence was tested while an activation analogue held the result lock:

1. Direct `orchestrator_v4.run_is` was started pre-activation.
2. Canonical CLI `is-run` was independently started pre-activation.
3. For each case, an activation-child analogue requested the broker lease.

Both result attempts failed within five seconds while the result lock remained held, and the child
acquired/released the broker in both cases. A stronger probe held both the result lock and broker
lease in the parent; direct and canonical CLI result attempts still failed within the bound. That
proves their precheck occurs before broker acquisition rather than merely acquiring and releasing
the broker quickly.

```text
direct result:         failed before locked broker; rc=0 (caught precondition error)
canonical CLI result: failed before locked broker; rc=2
direct child broker:   acquired
CLI child broker:      acquired
blocked processes:     0
```

The previous cycle—activation result lock -> result-command broker -> result-lock wait -> activation
child broker wait—can therefore no longer form.

## Complete lifecycle and holdout properties retained

- Activation freeze creation remains exclusive and atomic after snapshot verification,
  adversarial-review binding, committed-scope tests, durable test output, and repeated commit/scope
  verification. Canonical concurrent activation attempts serialize on the result lock.
- The interrupted bootstrap left no activation freeze or activation-test output. Its empty research
  journal and small result-lock node are ignored runtime artifacts outside the committed activation
  scope.
- The protected broker lease remains no-follow, owner-controlled, single-link, inode-verified,
  process-reentrant for one root, and exclusive across processes.
- Batch and decision consumption retain exact activation, launch-authority, phase-range, accepted
  prefix, terminal, journal-feedback, archive, and decision-authority checks before evaluation or
  nomination.
- Deterministic candidate source/certificate/eligibility failures retire a lane; raw or wrapped
  infrastructure/storage failures remain resumable. Restart recovery is idempotent and pending
  accepted trials are consumed as failures.
- Critical mutations enabling holdout access, immediate disclosure, unrestricted eligibility,
  research networking, or a winner-eligible ensemble fail closed. No interim field result is
  disclosed.
- The holdout remains exactly `[2024-07-01T00:00:00Z, 2026-08-01T00:00:00Z)`, including all of July
  2026 and no August timestamp. The release contains 761 daily rows through July 31, and winner
  breadth remains five positive quarters among nine touched quarters.
- All 15 lanes terminate before field adjustment. Finalist acceptance precedes private snapshot
  access; each historical start is one-shot; interruption is a non-retryable DNF. Empty/no-winner
  outcomes remain valid.
- Release authorization, inventory binding, atomic promotion, and crash recovery remain intact.
  DNF sleeve weight is explicitly transferred to effective cash, active weight plus cash equals
  one, and the ensemble cannot win.

## Focused verification executed

```text
tests/tournament/test_top40_v4_r2.py                                  55 passed
focused shared journal/empty/release/DNF recovery tests                8 passed
direct pre-activation call with result+broker held       failed within bound
canonical CLI pre-activation call with result+broker held failed within bound
activation-child broker acquisition after direct attempt              passed
activation-child broker acquisition after CLI attempt                 passed
```

This review found no unresolved condition requiring remediation before tournament activation.
