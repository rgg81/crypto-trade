# Top-40 V2 Amendment 0004 — development-runner schema-3 compatibility

Status: **IMPLEMENTED — REVIEW AND FREEZE REQUIRED**

Team 01's preregistered H14 development run failed before snapshot replay with
`ValueError: run state has an invalid schema`. The terminal event contains no artifacts or
metrics. It charged approximately 0.12 seconds of CPU and wall time and revealed no scientific
information. The event remains immutable and visible.

The frozen runner loads canonical Amendment 0001 schema-3 state at its existing Phase-0 fast-path
boundary, then dispatches it to the legacy schema-2 validator imported as `tournament_contract`.
Amendment 0004 replaces only that runner-local contract binding with the same immutable
three-attribute facade reviewed in Amendment 0002. The facade dispatches state validation to the
schema-3 validator while preserving the exact frozen config loader and Phase-0 file list. Every
remaining branch, Git binding, manifest hash, canonical-file hash, snapshot load, strategy worker,
evaluator, cost, risk, artifact, and journal rule remains frozen.

Both reused Amendment 0002 and Amendment 0003 modules are SHA-256 pinned, and every live helper,
lock, facade, loader, validator, and command identity used from them is captured and checked before
and after execution. Amendment 0004 shares Amendment 0002's process lock, restores the runner
contract through a deletion-safe `finally`, rejects repeated or noncanonical validation, and
validates the canonical schema-3 state both before and after the full legacy command. Legitimate
state transitions published by that legacy command remain allowed; they are validated, not
compared to the pre-run bytes.

Compatibility is restricted to `run-window development`. Private and finalist runner paths fail
closed inside both the active entrypoint and the facade helper itself; the helper accepts no
arbitrary callback and requires a private active-entrypoint identity capability before it loads
the frozen adapter. `research-status` delegates to frozen Amendment 0003; all non-runner commands
delegate unchanged to Amendment 0001. Those delegated paths recheck Amendment 0002/0003 authority
after success, exception, or interruption. A one-time administrative replacement
candidate may repeat Team 01's exact H14 bytes under a new candidate ID because the first attempt
revealed no model result. The failed event is not deleted or rewritten. Frozen accounting will
still count the replacement registration as an additional material trial and retain the tiny
failed-run resource charge; no favorable budget refund or multiplicity adjustment is introduced.
