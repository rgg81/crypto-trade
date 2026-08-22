# Independent adversarial R9 evaluator, data, and compatibility review

Review date: 2026-08-22

Review target: exact implementation commit
`d5fc45d1c7ee9efe493b5304af9a30ae9cbdf84b` on branch
`quant-portfolio-blind-top40-v4-r1-v2-restart7`.

This review covered evaluator/scoring and past-only behavior; the complete July-2026-inclusive
snapshot and A6 authority; candidate capture, source archive, receipt, and pre-acceptance causal
review authority; R9 journal/selection/release behavior; exact R8 incident preservation and zero
competitive reuse; activation bindings; and default-edition R1 compatibility. It did not activate
R9, launch a team or model, evaluate a candidate, open the historical holdout through an organizer
command, or open/decode any predecessor score or summary payload.

## Gate status

**PASSED. Unresolved findings: 0.**

The evaluator/data/R1/selection-compatibility gate is closed for the exact implementation bytes
above. This report does not itself authorize activation; the final three reports and aggregate
still require their normal committed hash binding.

## Fresh R9 and exact R8 incident authority

- `FRESH-RESTART-AUTHORITY.json` is canonical schema-6 evidence with SHA-256
  `c8dbc0b55a465b785b6cfe7ca960a894617d3c86882fcf45af9d9f5eb2e8a60b`, exactly matching
  activation's compiled constant. Read-only validation reports no pending pretrial recovery,
  `results_reused=false`, and `research_provenance_reused=false`.
- The authority binds the stopped R8 `restart6` incident at implementation
  `27b66a2d039447788ba2d1a66bf73cd3d6fc5fd0`: activation
  `49b8af37...128e1d`, activation tests `c61208a3...0d4`, journal file
  `8be8b3df...fa71`, and journal head `cde4a71f...03f`. Independent score-blind replay with the
  exact R8 journal implementation found 85 records, 38 accepted trials, 37 terminal trials (36
  successes and one failure), one pending trial, three retired lanes, zero nominations, and no
  selection. No score-bearing body was read.
- R9 imports none of those competitive artifacts. Its 15 lanes contain exactly the 90 committed
  seed files: no candidate child files, populated feedback/outbox/work files, research sessions,
  private runtime, source archives, trial receipts, IS results, nominations, selection, historical
  observations, or release. The journal and activation files remain absent at preactivation
  genesis. There are no lane symlinks or non-regular nodes.
- The frozen v13 model-smoke receipt SHA-256 is
  `a11bc30bfbb59e5aa328d7e44eea9257a6d1dfb66d0e838a1abd9cc41ed2fbe9`; exact semantic
  validation is covered by the R9 suite. Activation creates/verifies the byte-empty journal under
  its result lock before scanning the 15-lane, 94-file seed binding.

## Snapshot, July 2026, and A6

- The mandatory single-core full raw replay previously passed on the exact R8 snapshot authority
  and reproduced manifest SHA-256
  `c21fdcefc39961cd4408277e6cbb4833c31178cf86fa5d166499a3df6a8e7af7`, all 12
  published file size/hash/semantic authorities, and hard end
  `2026-08-01T00:00:00+00:00`. Snapshot builder/config, raw and published data, manifest, runner,
  engine, and source-archive bytes are byte-identical from that replay through this exact R9
  commit, so the expensive replay was not duplicated.
- The replayed raw tree has 94,816 regular nlink-1 files, no symlinks or non-regular nodes, and
  316,214,915 file bytes. Config, manifest, and historical-OOS split all use exclusive hard end
  `2026-08-01T00:00:00Z`, including all of July 2026 and excluding August.
- Direct scans found 59,605 July bars, 42,138 July funding rows, 28,494 July mark rows, and 160
  July membership rows, with zero rows at or after August 1. Maxima are July 31 16:00 for bars and
  marks, July 31 23:00 for funding, and July 27 for membership.
- Deterministic A6 regeneration returned exact hash
  `a1f9175b7728efde33d9d421b08c6cbcfe904783ba0f856b52504a28a453776e`, status
  `passed`, and zero violations. It binds 670 contract-metadata symbols, 328 membership symbols,
  and 13,026 membership rows. Result commands retain pre/post A6 and activation enforcement.

## Evaluator, scoring, and source identity

- Current evaluator authority is
  `6efdf2782c42ccb0b353ff2e9f97155819d5dae874a56b2837f2b1b50626c960`; current config
  SHA-256 is `d2409d8590c68baf5c1484795ea55de86330d9e06058349c09624f5b5767a881`.
  R9 selection changes do not alter the frozen engine, runner, data, source archive, or snapshot
  bytes.
- Strategies receive only eligible-symbol bars closed by the decision and funding strictly before
  it. Targets fill at the next executable transaction open. Boundary funding applies to carried
  pretrade positions; interior and forced-exit funding remain included. Mark prices size risk,
  while transaction opens determine fills, participation, fees, and slippage.
- Base, double-cost, and triple-cost paths remain independent reruns on the same canonical grid,
  including risk-action costs. Participation, residual delisting settlement, insolvency, grid
  drift, malformed/nonfinite values, and output substitution fail closed.
- Exact sign inversion still requires the cited baseline, matching mechanism/grid/control and risk
  authority, identical target index/columns/rebalance flags, and elementwise target negation. A
  genuinely failed inversion is now an honest qualification shortfall and can only produce a
  labeled unqualified representative; missing, changed, or malformed successful target authority
  remains a hard integrity error.
- Robust ranking orders missing gross-edge density after measured values instead of raising on
  `None`. Strongest-team comparison recomputes every successful candidate at the same final
  selection-trial count and keeps the frozen candidate-ID tie break.
- Candidate capture pins/rechecks directory components and opens enumerated files
  descriptor-relatively with no-follow, bounded regular owner-owned single-link checks. The
  content-addressed R2 source archive binds candidate root, entrypoint, ordered manifest, exact
  bytes, and bundle fingerprint; worker staging uses only archived bytes and rechecks the staged
  manifest before execution.

## Pre-acceptance source review and journal binding

- Every complete discovery/refinement batch is strictly parsed and fully inspected before its
  first acceptance. Ordered source bundle, private receipt, and causal source-review SHA-256 lists
  are committed in `batch_preflighted`. Journal replay binds each `is_accepted` record to its exact
  phase/index, candidate, source bundle, and receipt; the live sealed capability additionally binds
  the exact source-review hash before acceptance and evaluator access. Nomination revalidates the
  representative's pre-acceptance review against the same durable list.
- Causal review uses captured source plus synthetic appended/corrupt-future invariance inputs; it
  does not open tournament scores or the sealed snapshot. The review is strict canonical finite
  JSON, private mode 0600, owner-owned, nlink 1, and content-addressed by source bundle.
- Publication now pins every organizer-private directory component and writes a fixed private
  staging inode, fsyncs it, creates the final name with an atomic no-replace hard link, fsyncs the
  directory, then removes/fsyncs staging. A staging-only crash prefix is safely replaced; an exact
  two-name same-inode prefix is normalized to one link; unrelated hardlink or unsafe topology
  fails closed without target mutation. Partial final-path bytes are never published.
- Direct/CLI `run_is` still cannot manufacture the broker-frame capability. Invalid batches can
  become only score-blind terminal evidence; infrastructure failures remain restart-resumable and
  cannot be converted into an accepted trial or evaluator call.

## Representative selection, field adjustment, and release

- A team with any successful trial cannot retire through the ordinary path. After a complete
  12-trial lane, the broker automatically writes the exact tag-to-journal evidence certificate and
  nominates the strongest success. Direct decision consumption and direct/canonical decision-model
  launch paths refuse before a model is invoked; legacy decision outbox residue invalidates batch
  admission.
- A score-blind refinement rejection/abandonment after successful discovery is durably preserved,
  its exact archive/attempt evidence remains mandatory, and the serial broker promotes the
  strongest discovery success. The nomination truthfully records `trial_count=8` and the disclosed
  R2-only `selection_trial_count=12`. Charging all 12 planned slots for team ranking, nomination,
  field multiple-testing adjustment, selection freeze, and historical scoring prevents a
  score-conditioned stop advantage after discovery feedback. R1 emits neither new field.
- A crash after the refinement disposition but before promotion is restart-safe. `run_team`
  resumes promotion at both terminal-entry and phase-tail seams. `close_is` detects every pending
  successful promotion after exact terminal-evidence validation and fails before nomination
  registry, selection freeze, or journal mutation; journal replay independently refuses selection
  that discards such a lane.
- Close-IS ranks fully qualified representatives first. Five or more qualified teams yield the
  strongest five or six; fewer than five are filled to exactly five by robust-ranked successful
  representatives. Fallback labels remain `robust-ranked-representative`, and frozen candidate,
  neighborhood, IS gate, and field-confidence results are not changed or concealed. Fewer than
  five successful team representatives fails closed.
- Field confidence is recomputed over the disclosed selection-trial count across the complete
  field while retaining the separate accepted-trial count in the freeze. Zero/invalid-volatility
  finalists remain in the bracket and receive weight 0; unused capped inverse-volatility capacity
  stays cash. Ensemble `available` is true only when at least the configured number of positive-
  weight constituents exists.
- Journal schema v2 enforces five or six unique nominated finalists. Every finalist receives at
  most one historical observation. DNF never triggers replacement or reweighting: its frozen
  sleeve moves to cash. All batch-rejection/abandonment evidence, including evidence for a later
  promoted team, is revalidated at close and again before historical selection/recovery, snapshot
  access, or release mutation. Release remains simultaneous, journal-authorized, and atomic.

## R1 compatibility and evidence

R2 selection remains explicit. Default-edition behavior retains 12 teams, five advancing teams,
R1 paths, lifecycle-journal v1, source-archive v1, direct R1 `run_is`, and the original evaluator,
nomination, selection-freeze, and release schemas. The R2-only source-review batch list,
`selection_trial_count`, and truncated-lane lifecycle are edition-guarded.

```text
Exact R9 contract/activation/evaluator/security suite                 198 passed
Default-edition R1 external-contract suite                             24 passed
Legacy source-archive regression suite                                  5 passed
R9 scoped Ruff / git diff --check                              passed / passed
Full single-core snapshot replay on identical data bytes              passed
Published manifest                                      12 files / hashes exact
July rows / rows at or after 2026-08-01                    present / zero
A6 deterministic report                                    passed / zero violations
R8 incident journal                        85 records / 38 accepted / no selection
R9 copied competitive artifacts                                      zero
R9 seed                                           15 lanes / 94-file activation binding
```

**Final result: PASSED, zero unresolved findings.**
