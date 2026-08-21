# Adversarial evaluator, data, incident, and compatibility re-review

Review date: 2026-08-21

Review target: exact R7 implementation commit
`e4b87be0e49362e321fb3e2781d8c10812918d31` on branch
`quant-portfolio-blind-top40-v4-r1-v2-restart5`; review-assembly HEAD at final write was
`fcee2c7aaf5376715732418e41e229086cb309b4`.

The review covered the evaluator/scoring and past-only contract, July-2026-inclusive snapshot,
A6 universe authority, candidate capture/archive/receipt identity, R2 lifecycle-journal v2 and its
new whole-batch authority, selection/release compatibility, the exact stopped R6 incident, fresh
15-lane non-reuse, activation bindings, and default-edition R1 behavior. It did not activate R7,
launch a team or model, evaluate a candidate, or decode any R6 score or summary payload.

## Gate status

**PASSED. Unresolved findings: 0.**

The evaluator/data/R1/incident-compatibility gate is closed for the implementation bytes above.
The remaining reviewer report and aggregate still require their normal final commit and activation
binding; this report does not itself authorize activation or team launch.

## Fresh R7 and exact R6 incident authority

- `FRESH-RESTART-AUTHORITY.json` is canonical schema 4 evidence with SHA-256
  `7610daae55d4f9cec3e242162cf100d4236e5f5a3d330f07349715f94dd47910`, exactly matching
  the activation constant. Read-only recovery validation accepts it and reports no pending
  pretrial recovery.
- The authority binds the exact stopped R6 branch
  `quant-portfolio-blind-top40-v4-r1-v2-restart4` and implementation
  `aec9b2ae911e81a3b8fb55c6655dfcaebec909bf`. Independent read-only hashing reproduced its
  activation file `51ff34df...ace0f`, activation record `bb3942b4...ea1af`, activation-test
  output `a2b325a8...94cfe`, Team-02 discovery launch `08a21e53...cafcb`, and live outbox
  `de29894b...2f85` authorities.
- Pure byte replay of the R6 journal reproduced file hash `7452d4a5...b9229`, head
  `2d918690...38c26`, and 37 records. Team 02 has exactly six accepted and six terminal trials,
  three success event types, no pending request, no nomination, and no selection. No summary body
  or score was opened.
- The two rejected, never-accepted R6 candidates retain exact bundle/receipt identities:
  `ad51a1d4...14e56` / `81b4acbd...16dbf` and
  `82d8793e...a26` / `2fb7bb1a...2eec`. Neither has a trial receipt, source archive, or result.
  Team-02 discovery feedback was not disclosed and its outbox was not archived before the stop.
- R7 has exactly 15 seed lanes. Every lane contains only `ACCESS-POLICY.json`, `TEAM-BRIEF.md`,
  `candidates/README.md`, and newline `.keep` files in `feedback`, `outbox`, and `work`; all are
  regular single-link nodes. The activation seed binding contains 94 files and an empty synthetic
  journal authority.
- There is no R7 activation freeze/test output, journal, result lock, research-session/private
  runtime tree, candidate, feedback, outbox request, source archive, trial receipt, IS result,
  nomination, selection, historical observation, or release. The only report artifacts are the
  two frozen common BTC files; the permitted broker lock is byte-empty. Thus no competitive R6
  byte, trial, feedback, score, receipt, or source authority is reused.

## Whole-batch journal and evaluator admission

- R2 alone uses lifecycle schema
  `quant-portfolio-blind-top40-v4-r2-lifecycle-journal-v2`; R1 remains on journal v1.
  `batch_preflighted` can occur only once at the exact discovery-zero or refinement-eight boundary,
  with no pending request or terminal lane. It binds phase, exact outbox hash, ordered candidate
  IDs, ordered source-bundle hashes, and ordered receipt hashes.
- Journal replay refuses every R2 `is_accepted` record unless its trial position, candidate,
  source-bundle identity, and accepted research-session hash equal the durable whole-batch record.
  `batch_preflighted` itself does not increment trial counts, create a success, or enter ranking.
- The canonical broker score-blind validates the entire outbox, source tree, metadata/mechanism
  sequence, static-source policy, prior-phase evidence, and private canonical receipt set before
  appending the preflight record or opening evaluator data. Deterministic failure can append only
  a sealed `batch_rejected` disposition; infrastructure/OSError chains remain resumable and do not
  retire the lane.
- The in-memory evaluation capability is sealed to the exact live canonical broker frame, root,
  team, phase, outbox, ordered candidates, sources, receipts, and durable preflight record. Before
  every acceptance, `run_is` rechecks the live outbox, source capture, expected receipt phase, and
  exact receipt SHA-256. The post-preflight receipt-substitution regression leaves the journal
  byte-exact and creates no result path.
- Candidate receipts are current-owner mode-0600 regular nlink-1 files read with no-follow stable
  descriptor/lexical identity checks. Duplicate JSON keys, non-finite constants, noncanonical
  ordering/whitespace, a missing newline, wrong phase, wrong authority, and concurrent replacement
  all fail closed.
- Direct `run_is`, direct preflight/rejection calls, and the organizer `is-run` CLI cannot issue a
  capability. Refusal happens before pending-trial recovery, candidate acceptance, snapshot/score
  access, or result creation; regressions preserve a pending journal byte-for-byte.
- `batch_rejected` maps to the existing retired disposition for resolution and close-IS purposes,
  while ordinary retirement still requires at least eight accepted trials. Accepted-trial counts,
  field-adjusted confidence, nomination ranking, finalist selection, historical terminal ordering,
  and atomic release logic are otherwise unchanged. Selection still advances nominated teams only.

## Snapshot, July 2026, and A6

- The manifest SHA-256 is
  `c21fdcefc39961cd4408277e6cbb4833c31178cf86fa5d166499a3df6a8e7af7`. All 12 declared
  published files match exact size/hash authority and are regular nlink-1 files.
- The complete local raw authority contains 94,816 regular nlink-1 files, zero symlinks, and
  316,214,915 bytes. The prior mandatory one-core replay passed over the same frozen snapshot and
  produced the exact manifest above; this re-review intentionally did not duplicate that expensive
  replay, and instead rechecked the unchanged manifest, every published hash, raw topology/count,
  timestamp boundary, and regenerated A6 report.
- Config, manifest, and historical-OOS split all use exclusive hard end
  `2026-08-01T00:00:00Z`, so all of July 2026 is included. Direct scans found 59,605 July bars,
  42,138 July funding rows, 28,494 July mark rows, and 160 July membership rows, with zero rows at
  or after August 1. Maxima are July 31 16:00 for bars/marks, July 31 23:00 for funding, and July
  27 for membership.
- Deterministic A6 regeneration returned hash
  `a1f9175b7728efde33d9d421b08c6cbcfe904783ba0f856b52504a28a453776e`, status `passed`,
  and zero violations. It binds 670 contract-metadata symbols, 328 distinct membership symbols,
  and 13,026 membership rows. Activation and every result command retain the required pre/post A6
  enforcement.

## Evaluator, scoring, source archive, and activation

- `engine_v2`, `scoring_v4`, `runner_v4`, `_score_worker_v2`, `source_archive_v4`, `snapshot`,
  `pure_crypto_universe_v4_r2`, `top40_v4`, config, and manifest are byte-identical to the final
  reviewed R6 versions. The current evaluator authority is
  `5a84bb354bfa85c88c1c95dd99a0aa3fcc2985ebe5eb02deb531f91589438b74`; its change from R6
  is the expected frozen layout/branch binding, not evaluator behavior.
- Strategies receive only eligible-symbol bars closed by the decision and funding strictly before
  the decision. Targets fill at the next executable transaction open. Boundary funding is charged
  to carried pretrade positions; interior and forced-exit funding remain included. Mark prices size
  notional exposure while transaction opens determine fills, participation, fees, and slippage.
- Base, double-cost, and triple-cost paths are independent reruns on the same canonical grid,
  including risk-action costs. Participation limits, residual delisting settlement, insolvency,
  grid drift, malformed/nonfinite values, and output substitution fail closed.
- Sign inversion requires a cited accepted baseline, matching mechanism/grid/control metadata and
  risk authority, identical target index/columns/rebalance flags, and exact elementwise target
  negation. Team confidence remains the bounded Bonferroni adjustment; close-IS recomputes the
  inclusive field adjustment over accepted trials only. Historical winner eligibility remains nine
  quarters through July 2026 with at least five positive quarters.
- Candidate source capture pins every candidate directory component and enumerates/opens files
  descriptor-relatively with no-follow, regularity, size, owner/link, and final identity checks.
  Symlink, FIFO, hardlink, parent replacement, lexical substitution, and concurrent replacement
  regressions fail closed.
- The content-addressed R2 archive schema remains
  `quant-portfolio-blind-top40-v4-r2-candidate-source-archive-v1`. It binds candidate root,
  entrypoint, ordered manifest, exact bytes, and bundle fingerprint; the worker is staged only from
  those archived bytes and the staged manifest is reverified before execution.
- The frozen launcher-v11 smoke file hash is
  `7896fadce3923654b790014d6e6429287e4be44290116b17ac58b4d33a7ce5a1`, with record hash
  `3fe6257ef1df37ecf03879a4875ec835be155e30e232d98432dffaa44a327873`. Read-only semantic
  validation passed its Codex 0.148.0, command, prompt, environment, model-runtime, profile,
  session UUID, empty skill catalog, denied peer/host/private access, isolated TMPDIR, sentinel,
  and cleanup bindings.
- The active branch equals the R7 layout branch, and the clean implementation check resolved exact
  HEAD before report assembly. Activation scope and fresh-seed binding recompute from exact report
  bytes; activation must wait for all final reviews/aggregate to be committed. No activation or
  runtime artifact was created by this review.

## R1 compatibility and focused evidence

R2 selection remains explicit; the default edition retains 12 teams, a five-team advance count,
R1 paths, lifecycle-journal v1, source-archive v1, missing-journal behavior, direct R1 `run_is`, and
the original evaluator/runner behavior. The default-edition suite passed 24 tests and the legacy
source-archive suite passed 5 more.

```text
Exact R7 contract/activation/evaluator/security suite                 165 passed
Default-edition R1 external-contract suite                             24 passed
Legacy source-archive regression suite                                  5 passed
R7-changed-file Ruff / git diff --check                        passed / passed
Published manifest                                   12 files / hashes exact
July rows / rows at or after 2026-08-01                    present / zero
A6 deterministic report                                    passed / zero violations
R6 incident journal                 37 records / Team02 6 accepted + 6 terminal
R7 copied competitive artifacts                                      zero
R7 seed                                                15 lanes / 94-file binding
```

**Final result: PASSED, zero unresolved findings.**
