# Top-40 V2 Amendment 0003 — read-only orchestration compatibility

Status: **IMPLEMENTED — REVIEW AND FREEZE REQUIRED**

After Amendment 0001's administrative hold resumed, the frozen amended entrypoint rejected
`research-status` with `read-only operation 'research-status' cannot edit legacy state`. The
legacy status implementation opens its state-edit context to validate and, when necessary,
recover journal projections. Amendment 0001's adapter routed that context through an API that is
intentionally restricted to result-bearing operations.

This additive correction does not modify Phase 0, Amendment 0001, Amendment 0002, canonical
state, research evidence, team files, budgets, deadlines, gates, or evaluator behavior. During
one command it replaces only the frozen adapter's transaction-context binding. Read-only
commands receive a validated schema-2 projection and must leave both that projection and the
staged-output list unchanged. Result-bearing commands delegate to the exact frozen Amendment
0001 transaction implementation. The original binding is restored in `finally`.

The corrected entrypoint is `scripts/top40_v2_tournament_current.py`. Its implementation and
tests must be reviewed and committed before it is used for result-bearing team operations.
