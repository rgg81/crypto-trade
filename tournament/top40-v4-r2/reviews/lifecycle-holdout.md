# Independent adversarial lifecycle, holdout, and pretrial-recovery final re-review

Review date: 2026-08-20
Scope: exact current Top-40 V4-R2 bytes after the Team-01 pretrial infrastructure incident;
activation supersession, v7-to-v8 launch recovery, crash/idempotency behavior, runtime gating,
journal/trial accounting, broker serialization, and the complete holdout/result lifecycle.
Method: read-only source and exact-state inspection plus focused low-CPU adversarial tests in
temporary roots. No candidate, journal, activation, launch authority, or tournament result state was
modified; this report is the only reviewed repository file changed.

## Gate status

**PASSED. Unresolved findings: 0. RECOVERY AND TOURNAMENT START APPROVED.**

Every lifecycle/holdout finding from the failed passes is closed on the exact current bytes. The
known incident remains provably pretrial, the recovery transition preserves its old authorities,
and canonical restart converges across every reviewed durable boundary without consuming a trial.

## Exact incident and recovery properties verified

- The real `research-journal.jsonl` is byte-empty and replays to zero records. All 15 lanes remain
  seed-only. The exact old activation, activation-test output, and Team-01 v7 discovery launch are
  still at their active paths; neither staging nor completed recovery exists. This review did not
  execute recovery against the tournament.
- Prepare requires the exact empty journal/lanes/result surface, exact old activation file and
  record, exact activation-test output, exact v7 launch, and exact research-session tree before its
  first mutation. Missing, mismatched, symlinked, hard-linked, unrelated-staged, or extra evidence
  fails closed before authority moves.
- Old activation and test evidence move into a self-hashed prepared stage with destination-before-
  source durability. Same-inode/nlink-2 crash duplicates are accepted only at the exact source and
  staged names with matching device, inode, hash, and topology; unrelated hard links are rejected.
  Resume removes only the redundant source and normalizes the archive to one link.
- A prepared-stage restart distinguishes the valid new v8 activation from the archived old freeze.
  Canonical `recover_pretrial` resumes both before and after new activation publication, and with or
  without a same-inode stale-launch duplicate.
- Fresh activation's pre-freeze test output remains non-authoritative. With no freeze, only a
  bounded regular single-link successor output distinct from the archived old tests is accepted for
  atomic replacement by a full activation rerun. Old-output replay and unsafe file topology reject.
  Once the new freeze exists, its test path, exit status, size, and hash must bind the exact active
  output; mismatch rejects.
- Completion validates the fresh committed v8 activation before moving the stale v7 launch. The
  final atomic incident archive binds the exact reason, empty-journal hash, old activation/test/
  launch identities, new activation file/record/commit identity, launcher v8, and the exact
  self-hashed model-smoke receipt. Recomputed manifest metadata, archive mutation, current activation
  drift, and hard-link corruption reject.
- Prepare, activation, launch movement, manifest writing, and final publication are idempotent after
  interruption. No recovery error path appends journal evidence, accepts or fails a trial, retires a
  lane, runs an evaluator, or discloses competitive feedback.

## Runtime lifecycle and serialization verified

- All team launches and result commands require a valid current activation and completed incident
  authority before model/evaluator work. Result commands precheck before broker acquisition and
  repeat authority checks under broker and result locks; the direct launcher repeats its complete
  phase/journal/feedback/archive validation inside the broker lease.
- The process-wide broker lease remains no-follow, owner-controlled, regular, single-link,
  inode-verified, process-reentrant for one root, and exclusive across processes. Activation remains
  result-lock serialized while its test child can use the broker, and the precheck ordering prevents
  the previously reproduced three-party ABBA cycle.
- Batch and decision consumption require exact launch authority, expected phase/trial range,
  accepted journal prefix, completed prior feedback/archive, terminal/sealed state, and strict
  decision value types. Session feedback is bound to exact journal trial sequence and immutable
  outbox evidence.
- Deterministic source, certificate, eligibility, and exact invalid-target strategy failures retire
  the lane. Raw/wrapped infrastructure, timeout, protocol, storage, and `OSError` failures remain
  resumable and do not consume or retire a trial before accepted journal evidence exists.
- All 15 lanes terminate before field adjustment. Finalist acceptance precedes private snapshot
  access; each historical start is one-shot, and interruption is a terminal non-retryable DNF.
  Empty/no-winner outcomes remain valid. Release inventory binding, atomic promotion, and restart
  recovery remain intact.

## Holdout, disclosure, and cash accounting verified

- The private historical interval remains exactly
  `[2024-07-01T00:00:00Z, 2026-08-01T00:00:00Z)`: every July 2026 observation is included and no
  August timestamp is eligible. The activation manifest independently enforces the August 1 hard
  end, and no interim field result is disclosed.
- Critical configuration mutations enabling holdout access, immediate disclosure, unrestricted
  eligibility, research networking, or a winner-eligible ensemble fail closed.
- Finalist, DNF, retry, field-adjustment, breadth, and no-winner rules remain one-shot and
  deterministic. A DNF sleeve is explicitly transferred to effective cash; active weight plus cash
  equals one, disclosure matches evaluator accounting, and the ensemble cannot win.

## Focused verification executed

```text
tests/tournament/test_top40_v4_r2.py                              85 passed
tests/tournament/test_top40_v4.py                                 24 passed
Ruff on changed runtime/CLI/tests                                passed
git diff --check                                                  passed
missing/mismatched old-authority preflight                       rejected; no mutation
unrelated hard-link topology                                     rejected; no mutation
same-inode activation and launch crash duplicates                resumed; normalized nlink1
canonical restart after successor tests, fresh freeze, launch    resumed
successor scratch regular / hard-link / old replay               accepted / rejected / rejected
freeze-present test-output mismatch                              rejected
self-consistent incident reason/record/commit tamper             rejected
real journal bytes / replayed records                             0 / 0
15-team count / holdout hard end                                  15 / 2026-08-01T00:00:00Z
model-smoke file hash / self-hash                                exact / exact
```

No unresolved lifecycle, holdout, broker, journal, recovery, terminal, DNF/cash, activation, or
release condition remains before canonical pretrial recovery and serial Team-01 discovery retry.
