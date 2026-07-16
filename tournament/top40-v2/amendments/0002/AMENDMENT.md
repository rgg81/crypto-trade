# Top-40 V2 Amendment 0002 — schema-3 score-diagnostic compatibility

Status: **IMPLEMENTED — ORGANIZER REVIEW AND FREEZE REQUIRED**

Amendment 0001's first required diagnostic failed before replay with
`ValueError: run state has an invalid schema`. Its frozen snapshot verifier correctly read the
canonical schema-3 amendment state but passed it to the legacy schema-2 validator. The failure
published no private artifact, disclosed no score, consumed no team trial, and charged no team
CPU or wall budget.

This additive correction never modifies Amendment 0001, Phase 0, the canonical state, or the
scientific diagnostic. It temporarily replaces only `runner_v2`'s local tournament-contract
binding with an immutable three-attribute facade. Schema 3 is fully validated in memory; the
facade dispatches that one state check to `validate_amended_run_state`. Every subsequent branch,
manifest, frozen-file, Git-history, snapshot-immutability, historical-source, deterministic-replay,
canonical-target, label, and IC check remains the frozen Amendment 0001 implementation.

## Immutable authority

1. The six implementation files are uniquely first-added together in one commit whose parent
   contains the exact failed core reservation and result.
2. Canonical `REVIEW.json` is uniquely first-added as the implementation commit's direct child. It
   binds the implementation hashes, Amendment 0001 freeze and integration hashes, the exact failed
   reservation/result, and explicit approval for one non-material retry.
3. `freeze-correction` first-adds deterministic `integration-freeze.json` and `freeze.json`
   together as the review commit's direct child. The freeze is the sole retry reservation; there is
   no mutable Amendment 0002 state or audit.
4. `run-core-retry` executes that exact reservation and creates one canonical terminal
   `core-retry-result.json`. Its first commit must be the freeze commit's direct child. A completed
   result binds the exact six organizer-private artifacts and five public booleans. A failed result
   has no artifacts or outcomes and authorizes no further retry.
5. Only a committed successful retry permits `run-reference`. The reference candidate must first
   be reserved through Amendment 0001; its unchanged recorder then runs through the same reviewed
   compatibility facade and preserves Amendment 0001's state/audit transaction.

The compatibility facade verifies the canonical schema-3 state before and after each runner call
and requires byte-for-byte immutability. It pins the original module and validator identities,
allows only `load_config`, `validate_run_state`, and `PHASE0_FROZEN_FILES`, requires a completed run
to traverse the Phase-0 validator exactly once, and restores the exact original binding in a
`finally` block.

The Amendment 0001 administrative hold stays continuously active. Once the retry and reference
records are complete, the unchanged Amendment 0001 resume command applies the exact original
hold-start-to-resume toll to every team.
