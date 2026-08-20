# Adversarial evaluator, data, incident, and compatibility re-review

Review date: 2026-08-21

Review target: exact implementation commit
`9d95e7c69706744c357c0b10bd20472a38942862` on branch
`quant-portfolio-blind-top40-v4-r1-v2-restart4` (R6). The review covered the evaluator and
scoring contract, past-only execution, immutable source capture and archived worker staging,
the sanitized worker bootstrap, the July-2026-inclusive snapshot and its full raw authority,
A6, the exact stopped R5 worker-bootstrap incident, competitive-artifact non-reuse, activation
bootstrap/journal safety, the frozen launcher-v10 smoke authority, and R1 external behavior.

This review did not activate R6, launch a team or model, evaluate a candidate, or inspect a
predecessor score or summary payload. All R5 incident checks used filenames, hashes, canonical
journal structure, and terminal event types only.

## Gate status

**PASSED. Unresolved findings: 0.**

The evaluator/data/R1/incident-compatibility gate is closed for the exact implementation commit
above. The checked-in adversarial aggregate still describes the superseded R5 review set; the
organizer must refresh that aggregate after all three R6 reports are final and commit the frozen
review bytes before activation. That expected post-review binding step is not an evaluator finding,
and this review does not authorize activation by itself.

## R6 restart authority and exact clean state

- `FRESH-RESTART-AUTHORITY.json` is regular, single-link canonical evidence with exact SHA-256
  `f71896a9cd2da6071441bd65f5eeb42f2c2b0c953de016998019d082bc234e68`, equal to the
  activation constant. Schema 3 binds the predecessor attempts, the R4 skill incident, and the
  R5 worker-bootstrap incident; it explicitly sets `results_reused: false`.
- The active layout branch is exactly
  `quant-portfolio-blind-top40-v4-r1-v2-restart4`, matching Git. The implementation-commit check
  requires the exact clean HEAD rather than an ancestor or dirty frozen-scope tree.
- Read-only prerequisite validation accepts the fresh-restart authority and reports recovery
  pending false. The preactivation journal pathname is absent, as required for this untouched R6
  seed. Canonical activation alone may create it: `journal_v4.initialize` pins its parent, uses
  no-follow exclusive creation, requires a current-owner regular nlink-1 mode-0600 zero-byte file,
  fsyncs the new file and parent, and then the activation seed binds an empty journal. The synthetic
  genesis binding is 15 lanes, 94 seed files, and seed head
  `e7940b2cccf10bf53b45d9ee54af1167d4fb36621685bcfde258b2bd782dc1ba`.
- Every lane contains exactly `ACCESS-POLICY.json`, `TEAM-BRIEF.md`, `candidates/README.md`, and
  newline `.keep` markers in `feedback`, `outbox`, and `work`. All 15 lanes passed exact surface,
  payload, regularity, and single-link checks. No lane contains candidate code, feedback, an
  outbox request, a certificate, or work product.
- R6 has no activation freeze/test output/result lock, research journal, research-session tree,
  private model runtime, source archive, IS result/receipt, nomination, selection, historical
  result, or release. `reports-top40-v4-r2` contains only the two frozen common BTC authorities.
  The permitted broker lock is byte-empty, private, regular, and single-link.

## Journal and activation bootstrap safety

- Preactivation `status` and preactivation `validate` never call recovery-capable journal reads.
  An absent journal maps to an in-memory genesis state; an existing journal must pass the exact
  empty `initialize` gate. Unterminated or hard-linked evidence is rejected without truncation.
- The broker's whole-team entrypoint validates activation before any journal read, including its
  already-terminal branch. Direct and canonical-CLI regressions prove a preactivation fragment is
  preserved.
- Runtime `read` and `append` pin the owner-controlled parent and an existing journal through
  no-follow descriptors, require regular/current-owner/nlink-1/mode-0600 topology, lock the file,
  and compare descriptor, lexical file, and parent identities before and after recovery or append.
  R2 append never recreates a missing runtime journal. Existing hardlinks and injected pathname
  substitutions reject without mutating either the opened inode or replacement path.
- Crash-tail recovery remains limited to an unterminated suffix whose complete newline-committed
  prefix first replays successfully. New no-mutation regressions cover activation, status,
  validation, broker run, hardlinks, substitution, and missing-file cases.

## Exact R5 worker-bootstrap incident and non-reuse

The preserved private R5 worktree remains at implementation commit
`718249a8216245d7d6e29dd0af7f6f2318b189e7`. No R5 score or summary was opened.

- Independent hashes match every schema-3 incident fact: activation file/record/test output,
  discovery and refinement launches, discovery feedback, discovery outbox archive, journal file
  and head, all eight research receipts, all eight source archives, and all eight trial receipts.
- Pure replay accepts exactly 16 chained records: eight `is_accepted` followed by eight
  `is_failed`. There are zero `is_succeeded`, pending requests, nominations, selections,
  historical observations, or releases. No result artifact was created.
- R5 has 12 Team-01 candidate directories, four empty after the interrupted refinement phase.
  Rehashing the declared competitive roots as canonical sorted `{path,size,sha256}` rows produces
  exactly 75 files and digest
  `8a7d2ef7618ee971b623b775af56311f41982e9ae9f666a148580cc7261ae120`, matching the
  R6 incident authority.
- The R5 failures occurred before strategy initialization because the sanitized worker process
  could not resolve the frozen worker module. Discovery feedback was disclosed to Team 01, so the
  entire R5 research provenance is expressly non-reusable even though no score/result existed.
  R6 copies no R5 candidate, feedback, outbox, research receipt, source archive, trial receipt,
  journal, or result byte.

## Snapshot, July 2026, and A6

- The manifest SHA-256 is
  `c21fdcefc39961cd4408277e6cbb4833c31178cf86fa5d166499a3df6a8e7af7`. All 12 declared
  output files independently match their exact sizes and hashes and are regular nlink-1 files.
- The complete ignored raw authority is materialized locally rather than linked to a predecessor:
  94,816 current-owner regular nlink-1 files, zero symlinks/non-regular nodes, and 316,214,915
  bytes. File count and byte count equal the exact R5 neutral-data source.
- An independent single-core `snapshot.verify_snapshot_manifest` replay completed successfully in
  906.487 seconds. It verified 46,608 canonical provenance rows, official archive/checksum pairs,
  REST provenance, builder/config authorities, the 12 published outputs, and the manifest window.
- Config and manifest use the exclusive hard end `2026-08-01T00:00:00Z`; July 2026 is included.
  Direct timestamp scans found 59,605 July transaction bars, 42,138 July funding rows, 28,494 July
  mark rows, and 160 July membership rows, with zero rows at or after August 1. Maxima are July 31
  16:00 for bars/marks, July 31 23:00 for funding, and July 27 for membership.
- Deterministic A6 regeneration returns report hash
  `a1f9175b7728efde33d9d421b08c6cbcfe904783ba0f856b52504a28a453776e`, status `passed`,
  and zero violations. It binds 670 contract-metadata symbols, 328 membership symbols, 13,026
  membership rows, and the explicit exclusion of unreviewed archive-only symbols. The runner
  repeats the same A6 audit before and after every result command and removes a newly created output
  if the postcheck fails or differs.

## Evaluator, scoring, and worker bootstrap

- `engine_v2`, `scoring_v4`, `source_archive_v4`, `snapshot`, `pure_crypto_universe_v4_r2`,
  `top40_v4`, and `_strategy_worker_v4` are byte-identical to the reviewed R5 evaluator. The R6
  runner change is limited to the worker-bootstrap repair: its explicitly sanitized environment now
  sets `PYTHONPATH` to the exact resolved R6 `src` directory so Python can import the frozen worker
  module before that trusted module masks the repository.
- After module resolution, the worker's namespace setup masks the repository and other worktrees,
  rewrites runtime paths to the staged bundle and isolated dependencies, applies resource,
  Landlock, seccomp, audit, network, import, and filesystem restrictions, and only then imports
  candidate code. A real namespaced startup regression runs the exact sanitized environment and
  exits successfully. No organizer credentials, proxies, user site, or arbitrary inherited
  `PYTHONPATH` enter the worker environment.
- The current evaluator authority hash, including the repaired runner and frozen worker, is
  `c32164e30c02a3a9c0ef523bdbfb5f6ca710ca7668d445c2eadb7354ec207b8b`. Candidate
  acceptance and result publication bind and recheck this authority.
- Strategies receive only eligible-symbol bars closed by the decision and funding strictly before
  the decision. Targets fill at the next executable transaction open. Funding at a rebalance
  boundary is charged to the carried pretrade position; interior and forced-exit-boundary funding
  remain included. Mark price sizes notional exposure, while transaction opens determine fills,
  participation, fees, and slippage.
- Base, double-cost, and triple-cost paths are independent reruns over the same canonical grid,
  including risk-action costs. Participation limits, residual delisting settlement, risk actions,
  insolvency, malformed/nonfinite values, and grid drift fail closed.
- Nomination-time sign inversion requires a cited accepted baseline, equal mechanism/grid/control
  metadata and risk-policy authority, equal canonical target index/columns/rebalance flags, and
  exact elementwise negation of every target value.
- Team confidence uses the bounded Bonferroni adjustment
  `max(0, min(1, 1 - trials * (1 - probability)))`. Selection recomputes it over all accepted
  field trials, applies the frozen inclusive field-confidence floor, and uses the deterministic
  ranking key. Historical OOS remains nine quarters through July 2026 with a minimum five positive
  quarters for winner eligibility.

## Source archive and launcher-v10 authority

- Source capture pins every candidate directory component with no-follow directory descriptors,
  enumerates descriptor-relative entries, accepts only bounded UTF-8 regular single-link files,
  and verifies descriptor/final-entry plus full before/after tree identities. Symlinks, FIFOs,
  hardlinks, opaque/generated files, parent substitution, and concurrent lexical substitution are
  fail-closed regression cases.
- The content-addressed archive binds candidate root, entrypoint, ordered manifest, exact bytes,
  and bundle fingerprint. The runner rereads and rehashes that archive, proves equality with the
  accepted live capture, then stages the worker only from archived `.py` bytes and re-verifies the
  staged manifest/fingerprint. The stable schema remains
  `top40-v4-r2-candidate-source-archive-v1`.
- The frozen smoke receipt has file SHA-256
  `596bdbe528f3648f250c471feb591b40af2d3c84d195015d8b3a775e6786a6f8` and record hash
  `55d83cfa8c277a07b9f31db4341ba641f788139e91cba1fc16e2576929390660`. Semantic validation
  recomputes launcher `top40-v4-r2-research-runtime-v10`, Codex `0.148.0`, command, prompt,
  environment, model-runtime, profile, session UUID, sentinel, empty skill catalog, denied peer and
  host-skill access, isolated TMPDIR, and verified cleanup bindings.
- Launcher-v10 restores only absent organizer-owned `outbox/.keep` and `work/.keep` markers after
  a completed, failed, interrupted, or timed-out phase. Restoration pins the lane directory,
  creates exact newline mode-0644 nlink-1 markers exclusively and durably, and rejects conflicting
  bytes or topology. Preactivation broker/direct-launch resume performs the same validation before
  activation authority is consulted.

## R1 compatibility

The default-edition external suite passes 24/24. R1 retains its original branch, 12 teams,
five-team advance count, paths, schemas, worker bundle behavior, evaluator behavior, and missing
journal initialization behavior. R2-only fresh restart, 15-lane, A6, field adjustment, strict
runtime-journal, launcher-v10, marker-resume, and worker-bootstrap rules remain edition-selected.

## Focused evidence

```text
Exact R2 contract/activation/evaluator/security suite                 135 passed
Default-edition R1 external-contract suite                             24 passed
Full raw snapshot replay                                      passed / 906.487 s
Raw authority                                         94,816 files / nlink1
Published manifest                                   12 files / hashes exact
July rows / rows at or after 2026-08-01                    present / zero
A6 deterministic report                                    passed / zero violations
R5 incident journal                         8 accepted / 8 failed / 0 succeeded
R5 receipt/source/trial hash sets                            8 / 8 / 8 exact
R5 declared competitive surface                    75 files / digest exact
R6 copied competitive artifacts                                      zero
R6 seed                                                15 lanes / 94-file binding
R6-changed-file Ruff / git diff --check                        passed / passed
```

**Final result: PASSED, zero unresolved findings.**
