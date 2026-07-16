# Top-40 V2 Amendment 0003 — read-only orchestration compatibility

Status: **IMPLEMENTED — REVIEW AND FREEZE REQUIRED**

After Amendment 0001's administrative hold resumed, the frozen amended entrypoint rejected
`research-status` with `read-only operation 'research-status' cannot edit legacy state`. The
legacy status implementation opens its state-edit context to validate and, when necessary,
recover journal projections. Amendment 0001's adapter routed that context through an API that is
intentionally restricted to result-bearing operations.

This additive correction does not modify Phase 0, Amendment 0001, Amendment 0002, canonical
state, research evidence, team files, budgets, deadlines, gates, or evaluator behavior. It no
longer patches any transaction binding. Each invocation loads a fresh private copy of the
Amendment 0001 adapter from its frozen SHA-256. Every command except `research-status` delegates
directly to that unchanged adapter.

The corrected `research-status` path is structurally read-only. It holds the exact Amendment 0001
cross-process state lock across amended-state validation, effective-deadline projection, organizer
journal validation, all ten team-ledger validations, and report construction. It invokes the
frozen journal loader with `recover_projection=False`, so divergence is reported rather than
repaired. It contains no state edit, file write, staging, rollback, or mutation branch. The shared
lock therefore serializes it with result-bearing transitions without any possibility of treating
a legitimate transition as tampering or rolling one back.

The corrected entrypoint is `scripts/top40_v2_tournament_current.py`. Its implementation and
tests must be reviewed and committed before it is used for tournament operations.
