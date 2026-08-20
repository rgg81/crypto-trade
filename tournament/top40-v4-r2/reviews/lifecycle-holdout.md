# Independent adversarial successor-restart lifecycle and holdout review

Review date: 2026-08-20
Scope: exact current successor worktree on branch
`quant-portfolio-blind-top40-v4-r1-v2-restart2`; stopped-r3 evidence, fresh-restart
authority, current-launch transition, activation/restart lifecycle, fairness, July-2026 holdout, and
R1 compatibility.
Method: read-only inspection of r3/r4 runtime evidence, focused temporary-root mutation probes, and
low-CPU regression tests. No activation, team launch, candidate, journal record, evaluation,
feedback, result, selection, or release was created in r4; this report is the only reviewed file
modified.

## Gate status

**PASSED. Unresolved findings: 0.**

R4 is an exact seed-only successor. R3 stopped after its discovery model produced a batch and eight
content-addressed research receipts but before acceptance, evaluation, feedback, or archive. The
new authority binds that stopped state without reusing any model output. The repaired launch check
rejects the exact superseded v7 receipt, arbitrary residue, noncanonical/duplicate-key encodings,
and a copied r3 v8 receipt, while allowing only the exact canonical bytes of a root-current v8
receipt after the immutable genesis activation boundary.

## Stopped-r3 evidence and fresh authority

- `FRESH-RESTART-AUTHORITY.json` has the exact code-bound SHA-256
  `f33d4ac0fdbea88a75b8c8d8cd6f4bbbd799a4095dfbb3e9147c1c1a483d3f0b`.
  Its original two-trial predecessor evidence remains bound without score disclosure or result
  reuse. Its separate `restart_attempt` object identifies r3's activation, activation record,
  implementation commit, branch, current discovery launch, unarchived outbox, byte-empty journal,
  and eight research receipts.
- Independent comparison against the stopped r3 runtime matched every declared identity: activation
  file `0082eab1...`, self-consistent activation record `ebd5b977...`, implementation commit
  `79758b44...`, current discovery launch `d3f4da4c...`, batch outbox `fd620a26...`, and all
  eight receipt hashes. The activation record also binds its exact activation-test output.
- The r3 journal is byte-empty and replays to zero records. There is no feedback JSON, IS result,
  source archive, or archived outbox. Thus there is no accepted/evaluated trial, disclosed
  feedback, or result to carry forward. Candidate/model files remain only in the stopped r3 runtime;
  none exists in r4.
- The preservation statement is now exact: stopped runtime/model artifacts remain byte-for-byte
  available, while r3's tracked branch later advanced in committed history to carry the recovery
  fix. The authority no longer claims that the entire worktree stayed unchanged.
- The authority file is exact-hash checked and schema checked. Its restart evidence requires false
  feedback disclosure, an empty-journal hash, zero journal/accepted/evaluated counts, an unarchived
  outbox, Team 01 identity, and eight well-formed receipt hashes. Any authority byte change fails
  before activation.

## R4 genesis, launch transition, and restart behavior

- R4 is on the distinct `restart2` branch required by the current layout. It contains all 15 exact
  seed lanes, 45 committed one-byte-LF markers, the two frozen common reports, and no activation
  freeze, activation-test output, journal, research session, candidate, active outbox/feedback,
  result, nomination, selection, or release. Canonical pre-activation status/validation reports the
  genesis head, zero records, and no activation.
- Canonical activation will initialize the byte-empty journal and live result-lock marker, then
  exact-scan the owner-controlled regular single-link seed surface before and after tests. The
  activation record binds restart mode, exact authority hash, empty-journal hash, 15 lanes, 94
  competitive files, and the scope-derived chained head. Activation remains clean-commit,
  exact-branch, test-bound, atomic, exclusive, fsynced, one-shot, and crash-resumable.
- With no discovery receipt, fresh authority is repeatedly valid. If the historical Team-01
  discovery path exists, the validator first rejects the exact hardcoded v7 SHA-256. Every other
  payload must byte-equal the shared canonical launch payload for exactly Team 01 discovery:
  canonical schema/status/tournament, launcher v8, current root-specific profile hash, and current
  team-kit hash. Semantically equivalent whitespace/order variants, duplicate keys, symlink,
  hard-link, malformed, changed, and arbitrary nodes fail closed.
- Fresh restart reads the launch pathname once through the stable regular/single-link capture, tests
  the old-v7 hash on those bytes, and passes those same captured bytes to exact current validation.
  It never reparses or rereads the pathname during that authority decision. A substitution after
  capture cannot alter which bytes were validated; the normal pre-lease/under-lease repetition
  catches a changed current pathname before a protected runtime action.
- A copied r3 v8 launch fails in an r4 fixture because its root-specific profile identity differs.
  An independently constructed exact current receipt passes the authority check, but the
  pre-activation genesis scanner still rejects its research-session residue. Therefore a current
  receipt cannot survive into an activation freeze; it becomes admissible only when the activated
  organizer creates it at the normal first-launch transition.
- The current launcher validates activation and fresh authority before recording a receipt.
  `_write_immutable` makes an identical receipt idempotent, allowing a retry after a crash between
  launch authorization and model completion. Once a legitimate v8 receipt exists, repeated
  authority checks accept it so an outbox/receipt crash can resume. Broker consumption recreates
  exact candidate receipts from the unarchived outbox before accepting any trial.
- Result, launcher, and broker entrypoints repeat activation, fresh/incident authority, launch,
  journal, phase, terminal, and archive checks under the established serial locks. Pre-activation
  result calls fail before broker acquisition; no r3 candidate, receipt, outbox, trial, or feedback
  is imported into r4. Every one of the 15 teams therefore restarts at trial zero under the same
  disclosed mechanism rules.
- The layout branch update and this reviewed report are frozen-scope changes, so canonical activation
  will reject until the organizer commits the exact reviewed bytes. This is the intended final
  clean-commit gate, not a runtime exception.

## Fairness and holdout

- Mechanism epochs remain trial-ordered. A parented `control-ablation` or `role-check` may use
  descriptive prose only with a current-epoch accepted parent. Unparented/old-epoch controls,
  first-candidate pivots, no-op pivots, and second pivots reject before acceptance.
- Preacceptance broker errors remain unmasked and consume no trial. Only an accepted deterministic
  source rejection with a durable terminal is consumed; infrastructure failures without a terminal
  remain resumable. Strict decisions, immutable feedback/outbox reconstruction, DNF-to-cash
  accounting, field adjustment, one-shot finalists, empty/no-winner behavior, and atomic release
  remain unchanged.
- The hard end is still exclusively `2026-08-01T00:00:00Z`. The manifest includes every July 2026
  daily bar and all nine required holdout quarters and excludes August. Shortened-window and
  config/manifest mutation tests fail closed.

## Focused verification executed

```text
tests/tournament/test_top40_v4_r2.py                         109 passed
tests/tournament/test_top40_v4.py                             24 passed
Ruff / git diff --check                                  passed / passed
r4 pre-activation status                         0 records / not activated
r3 activation / record / tests binding                         exact
r3 journal / accepted / evaluated                          empty / 0 / 0
r3 launch / outbox / eight receipts                             exact
r3 feedback / results / outbox archive                         0 / 0 / 0
fresh authority SHA-256                                f33d4ac0... exact
absent current launch / repeated authority checks           accepted
copied r3 v8 / arbitrary launch residue                     rejected
noncanonical / duplicate-key current launch                 rejected
single stable capture / pathname substitution            exact / isolated
exact superseded v7 launch                                  rejected
exact root-current v8 authority                             accepted
root-current v8 before genesis seed gate                    rejected
holdout hard end                               2026-08-01T00:00:00Z
```

The lifecycle/restart/fairness/holdout gate is clear for the organizer to commit the reviewed bytes
and run the separate canonical activation step. This review did not activate r4 or launch a team.
