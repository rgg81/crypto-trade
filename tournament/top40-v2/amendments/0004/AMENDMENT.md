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

Compatibility is restricted to `run-window development`. Private and finalist runner paths fail
closed until separately reviewed. `research-status` delegates to frozen Amendment 0003; all
non-runner commands delegate unchanged to Amendment 0001. A one-time administrative replacement
candidate may repeat Team 01's exact H14 bytes under a new candidate ID because the first attempt
revealed no model result. The failed event is not deleted or rewritten.
