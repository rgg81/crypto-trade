# Adversarial evaluator, data, and compatibility re-review

Review scope: exact-current-byte Top-40 V4-R2 pre-activation implementation inspected on
2026-08-20 after source-boundary, research-runtime, lifecycle/status, and broker remediation. The
implementation was not modified by this review. No broad snapshot replay or full-window strategy
run was performed.

## Gate status

**PASSED.** Unresolved findings: **0**. The evaluator, data, candidate-source, scoring, activation,
and R1-compatibility gates reviewed here are closed for tournament activation.

## Remediation verification

The previously open candidate-directory substitution defect is closed in the final bytes:

- `_PinnedDirectory` opens every absolute component from the filesystem anchor through the
  selected candidate root with `O_DIRECTORY | O_NOFOLLOW`, retains all descriptors during the
  traversal, records `(device, inode)` identities, and reopens the complete lexical chain before
  acceptance to prove that no component was replaced.
- `_team_tree_files()` enumerates pinned directory descriptors, inspects entries with
  `stat(..., dir_fd=..., follow_symlinks=False)`, and opens subdirectories relative to their pinned
  parents. It verifies each subdirectory before and after recursion.
- `_stable_file_bytes()` opens files relative to pinned parent descriptors with
  `O_RDONLY | O_CLOEXEC | O_NOFOLLOW | O_NONBLOCK`; it requires a regular, singly linked,
  at-most-2-MiB descriptor, repeats `fstat()`, and compares it with a no-follow `dir_fd` stat.
  Final symlinks, FIFOs, hard links, non-regular files, oversize files, and identity changes fail
  closed.
- Captured bytes are retained in the pinned tree records and become the content-addressed source
  archive. Worker materialization uses those archive bytes, verifies every staged hash, and mounts
  only Python source in R2; notes, JSON, attestations, and certificates remain evidence but are not
  executable inputs.
- The full `capture_source_bundle()` parent-directory replacement regression now proves that
  replacement after entrypoint resolution is rejected. The final-file symlink/FIFO/hard-link and
  lexical substitution regressions also pass.

## Evaluator and data gates

- **July-2026 snapshot boundary:** config and manifest bind
  `2026-08-01T00:00:00Z` as the exclusive end. The manifest SHA-256 is
  `c21fdcefc39961cd4408277e6cbb4833c31178cf86fa5d166499a3df6a8e7af7`; the final transaction bar
  is `2026-07-31T16:00:00Z`, July funding is present, and focused checks find no August bar or
  funding timestamp. Activation requires the identical July-inclusive authority and performs the
  full canonical manifest verification once.
- **A6 pure-native-crypto authority:** module, dependency, membership, manifest, deterministic
  report, metadata, exchange-info, and count authorities match config. The audit report SHA-256 is
  `a1f9175b7728efde33d9d421b08c6cbcfe904783ba0f856b52504a28a453776e`, with status `passed`, zero
  violations, 670 metadata symbols, 328 membership symbols, and 13,026 membership rows.
- **Past-only strategy context:** bars enter a decision only after their complete 8-hour interval;
  funding is strictly earlier than the decision; out-of-universe rows remain hidden. The strategy
  worker receives only append-only canonical prefixes, while the organizer retains the raw
  snapshot and evaluator.
- **Execution semantics:** targets fill at the next executable transaction open, using boundary
  marks for target sizing. Funding on the boundary applies to the carried position before
  rebalance; interior funding applies once. Base, 2x-cost, and 3x-cost scenarios share the canonical
  grid and charge normal fees, slippage, participation limits, policy actions, risk reductions,
  membership exits, and forced exits.
- **Immutable authorities:** config, manifest, dependency lock, evaluator, A6 report, source
  archive, strategy, risk policy, target artifacts, and result artifacts are hashed and rechecked
  across evaluation and publication. Official execution stages the verified source archive rather
  than the live lane tree.

## Selection, release, and compatibility gates

- **Exact sign inversion:** nomination verifies a cited baseline, matching mechanism/horizon/
  control metadata and risk-policy digest, identical timestamp/column/rebalance grids, and exact
  numerical negation of all target weights. A mislabeled positive copy is rejected.
- **Scoring and multiplicity:** accepted failures consume trials. Team qualification recomputes
  Bonferroni confidence at the final lane trial count; IS close applies the field-wide adjustment
  over every accepted field trial and the frozen 0.90 floor before deterministic ranking. At most
  six candidates advance, with no floor lowering or backfill.
- **Historical release:** July 2024 through July 2026 touches nine calendar quarters, so the frozen
  five-positive-quarter winner gate is computed over the correct interval. Historical observations
  remain serial, one-shot, non-replaceable, and atomically disclosed. DNF constituent weight is
  reported and carried to effective cash without redistribution.
- **Activation/review binding:** activation requires a clean committed explicit scope, the exact
  branch, current A6 authority, the July-inclusive canonical snapshot, three passed report hashes
  with zero unresolved findings, and the review-scope head. The activation record then binds the
  scope, review, tests, manifest, config, commit, and report hashes; later validation recomputes
  them. R2 result, status, validation, close, release, and broker transitions now share the frozen
  serialized command boundary; the expanded lifecycle tests confirm this does not change evaluator
  authorities or disclose per-team or per-finalist progress.
- **R1 external behavior:** a clean default-edition process remains 12 teams, five finalists, and
  the original R1 layout and schema strings. R1 keeps its worker-visible bundle semantics while the
  descriptor-pinned read is a transparent hardening. Shared implementation hashes necessarily
  differ, but the reviewed R1 external contracts and focused behavior remain compatible.

## Focused evidence

- R2 focused suite on the exact reviewed bytes: **53 passed**.
- R1 focused contract suite in a clean default-edition process: **24 passed**.
- Focused next-open, funding, cost, participation, forced-exit, risk, and past-only evaluator set:
  **12 passed**.
- Source-archive boundary suite: **5 passed**.
- Ruff on the changed evaluator/authority modules and R2 tests: passed.
- `git diff --check`: passed at review time.
- Direct current-authority hashing matched the config's manifest, A6 module/dependency, and
  membership identities; deterministic A6 report regeneration matched its frozen report hash.

**Final result: PASSED, zero unresolved findings.**
