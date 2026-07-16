# Top-40 V2 Amendment 0003 — read-only orchestration compatibility

Status: **IMPLEMENTED — REVIEW AND FREEZE REQUIRED**

After Amendment 0001's administrative hold resumed, the frozen amended entrypoint rejected
`research-status` with `read-only operation 'research-status' cannot edit legacy state`. The
legacy status implementation opens its state-edit context to validate and, when necessary,
recover journal projections. Amendment 0001's adapter routed that context through an API that is
intentionally restricted to result-bearing operations.

This additive correction does not modify Phase 0, Amendment 0001, Amendment 0002, canonical
state, research evidence, team files, budgets, deadlines, gates, or evaluator behavior. Each
invocation loads a fresh private copy of the Amendment 0001 adapter from its frozen SHA-256; it
does not monkeypatch the process-wide imported module. During that one private execution it
replaces only the adapter's transaction-context binding.

Read-only commands receive a validated schema-2 projection. Checks run from `finally`, so a
command cannot hide a projection or staged-output mutation by raising. Canonical tournament
authority, organizer journals/ledgers, and the complete report tree are snapshotted byte-for-byte;
any direct mutation is restored atomically and rejected. Result-bearing commands forward the
exact root, config, operation, staged-change list, and clock to the frozen Amendment 0001
transaction implementation. The private binding is restored and its authority identities are
checked on successful, failed, and interrupted exits. Concurrent wrapper invocations use distinct
module instances, while the unchanged Amendment 0001 state lock continues to serialize actual
result-bearing transitions.

The corrected entrypoint is `scripts/top40_v2_tournament_current.py`. Its implementation and
tests must be reviewed and committed before it is used for result-bearing team operations.
