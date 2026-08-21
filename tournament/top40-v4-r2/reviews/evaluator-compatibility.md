# Independent adversarial R8 evaluator, data, and compatibility review

Review date: 2026-08-21

Review target: exact implementation commit
`8335719049ddce0fb5b928a3905017b388b1fccd` on branch
`quant-portfolio-blind-top40-v4-r1-v2-restart6`.

This review covered evaluator/scoring and past-only behavior; the complete July-2026-inclusive
snapshot; A6; candidate capture, archive, and receipt authority; R8 score-blind admission repair;
the `batch_abandoned` lifecycle extension; terminal selection/release compatibility; exact R7
incident preservation and zero competitive reuse; activation bindings; and default-edition R1
behavior. It did not activate R8, launch a team or model, evaluate a candidate, or open/decode any
R7 score or summary payload.

## Gate status

**PASSED. Unresolved findings: 0.**

The evaluator/data/R1/incident-compatibility gate is closed for the exact implementation bytes
above. This report does not itself authorize activation: the three final reports and aggregate
must still receive their normal committed hash binding before activation.

## Fresh R8 and exact R7 incident authority

- `FRESH-RESTART-AUTHORITY.json` is canonical schema-5 evidence with SHA-256
  `20df6a9f7e325e8fa999ebe8482153bd4c006bd884dfd9c1987c08f97752f896`, exactly matching
  activation's compiled constant. Read-only pretrial validation reports the completed fresh
  restart, no pending recovery, and `results_reused=false`.
- Independent hashing of the preserved R7 worktree reproduced activation
  `9a9e1d32...d82f2d`, activation tests `5baec893...e7a7b`, adversarial review
  `45fe179e...35f2d`, journal `992cd1f8...90a4`, selection freeze `f88ce0e3...60a1`, and
  historical release manifest `108bfc1e...a12d`, exactly as declared by R8 authority.
- Pure journal replay produced head `78357089...7e29`, 17 records, 15 `batch_rejected` records,
  one `selection_frozen`, and one `release_authorized`. All 15 lanes have trial count zero; there
  are no IS requests, IS terminals, nominations, finalists, historical requests, or historical
  terminals. No score-bearing body was inspected.
- The stopped R7 surface has 15 discovery launches, 15 archived outboxes, and 120 private
  research receipts, but zero source archives and zero IS result files. R8 reuses none of those
  artifacts: its 15 lanes contain only the 90 committed seed files, with no candidate files,
  non-marker feedback/outboxes/work, research-session/private tree, source archive, trial receipt,
  result, nomination, selection, historical observation, or release.
- R8 has no activation freeze or activation-test output. The journal is absent before bootstrap,
  which is the canonical genesis state: `orchestrator_v4.activate` creates/verifies the exact
  byte-empty journal under the result lock before activation's seed scan. Independent inventory
  found that journal to be the only not-yet-created expected entry and found no unexpected
  tournament or report entry. The permitted broker lock is byte-empty, owner-only mode 0600, and
  nlink 1. The frozen launcher-v12 smoke receipt hash is
  `8ce7c6adab43167b54dffdffce8a42b01717762b4d7f821e8d46c996ee5ce5b5` and semantic
  validation passed with record hash `4194ba3f...5c62b`.

## Score-blind repair and final admission parity

- Repair inspection strictly parses the exact stable outbox bytes, captures each candidate source
  bundle, and applies the same captured-candidate, metadata, static-source, prior-ID, and open-lane
  mechanism-history validators as final whole-batch preflight. Refinement begins with the exact
  eight accepted discovery metadata records, so current-epoch parent and one-pivot semantics match
  final admission. Canonical `OrchestratorError` metadata failures are candidate repair findings,
  not misclassified infrastructure errors.
- The inspection call graph reads only config, journal metadata, the candidate/outbox surface, and
  synthetic causal-review inputs. It does not call the evaluator, scoring worker, snapshot loader,
  result reader, or source archive. Candidate receipts are issued only after a fresh inspection
  returns zero findings. Final broker preflight then repeats the entire live outbox/source/metadata
  validation and binds the ordered source and receipt SHA-256 values before any trial acceptance or
  evaluator call.
- Repair opportunity authority is durable and crash-idempotent. Private session issues and
  attempts are strict canonical JSON, mode 0600, owner-owned, nlink 1, bounded, and read/written
  through descriptor-pinned directory components with no-follow and final lexical/descriptor
  identity checks. Session 0 is the initial process; sessions 1-3 are the only repairs. A crash
  after issue or model completion consumes that durable opportunity and cannot grant an extra
  model process.
- If a crash lands after a private attempt is fsynced but before lane feedback publication, the
  exact feedback bytes are recovered and validated before another session issue or process. Wrong
  bytes fail closed. The model profile has read-only access to feedback and write access only to
  its candidates, outbox, and work roots.
- An invalid published outbox remains live for canonical preflight, which can append only a sealed
  score-blind `batch_rejected`. Four exact missing-output attempts instead authorize
  `batch_abandoned`; no outbox, archive, receipt, trial, source archive, or result is fabricated.
  Both dispositions are legal only at discovery trial zero or refinement trial eight, with no
  pending request or prior batch preflight, and neither changes accepted-trial counts or ranking.
- Close-IS revalidates every `batch_rejected` archive hash and every `batch_abandoned` private
  attempt/session chain before registry/selection. Historical release repeats the same validation
  immediately after its journal read and before selection recovery, historical identity
  acceptance, snapshot access, or journal mutation. Thus damaged terminal evidence cannot be
  converted into a selection or holdout observation.

## Snapshot, July 2026, and A6

- The mandatory single-core full replay passed on the R8 raw authority and reproduced manifest
  SHA-256 `c21fdcefc39961cd4408277e6cbb4833c31178cf86fa5d166499a3df6a8e7af7`, all 12
  published file size/hash/semantic authorities, and hard end
  `2026-08-01T00:00:00+00:00`. The snapshot implementation, manifest, build config, and data bytes
  did not change between the replay start and final implementation commit.
- The raw tree contains 94,816 regular nlink-1 files, no symlinks or non-regular nodes, and
  316,214,915 file bytes. The 12 published files are likewise exact regular nlink-1 authorities.
- Config, manifest, and historical-OOS split use exclusive hard end
  `2026-08-01T00:00:00Z`, including all of July 2026 and excluding August. Direct scans found
  59,605 July bars, 42,138 July funding rows, 28,494 July mark rows, and 160 July membership rows,
  with zero rows at or after August 1. Maxima are July 31 16:00 for bars/marks, July 31 23:00 for
  funding, and July 27 for membership.
- Deterministic A6 regeneration returned exact hash
  `a1f9175b7728efde33d9d421b08c6cbcfe904783ba0f856b52504a28a453776e`, status
  `passed`, and zero violations. It binds 670 contract-metadata symbols, 328 membership symbols,
  and 13,026 membership rows. Activation and result execution retain pre/post A6 enforcement.

## Evaluator, scoring, source archive, and selection

- `engine_v2`, `scoring_v4`, `runner_v4`, the score worker, `source_archive_v4`, `snapshot`,
  `pure_crypto_universe_v4_r2`, `top40_v4`, config, and manifest are byte-identical to the final
  reviewed R7 implementation. The current evaluator authority is
  `f6fc9e62cbabaa6d38f85e5134ae951fa08f4e4b17578bbc81e3ae1e98bb7798`; R8's changes are
  admission/lifecycle and branch bindings, not evaluator behavior.
- Strategies receive only eligible-symbol bars closed by the decision and funding strictly before
  it. Targets fill at the next executable transaction open. Boundary funding applies to carried
  pretrade positions; interior and forced-exit funding remain included. Mark prices size exposure,
  while transaction opens determine fills, participation, fees, and slippage.
- Base, double-cost, and triple-cost paths are independent reruns on the same canonical grid,
  including risk-action costs. Participation limits, residual delisting settlement, insolvency,
  grid drift, malformed/nonfinite values, and output substitution fail closed.
- Sign inversion still requires a cited accepted baseline, matching mechanism/grid/control and
  risk authority, identical target index/columns/rebalance flags, and exact elementwise target
  negation. Team confidence remains bounded Bonferroni adjustment; close-IS recomputes inclusive
  field adjustment over accepted trials only. Historical winner eligibility remains nine quarters
  through July 2026 with at least five positive quarters.
- Candidate capture pins and rechecks directory components, opens enumerated files
  descriptor-relatively with no-follow, and enforces bounded regular owner-owned single-link
  identities. The content-addressed R2 archive binds candidate root, entrypoint, ordered manifest,
  exact bytes, and bundle fingerprint. Worker staging uses only the archived bytes and rechecks the
  staged manifest before execution. Repair does not weaken or bypass that final archive authority.

## R1 compatibility and evidence

R2 selection remains explicit. Default edition behavior retains 12 teams, five advancing teams,
R1 paths, lifecycle-journal v1, source-archive v1, missing-journal behavior, direct R1 `run_is`, and
the original evaluator/runner semantics.

```text
Exact R8 contract/activation/evaluator/security suite                 177 passed
Default-edition R1 external-contract suite                             24 passed
Legacy source-archive regression suite                                  5 passed
R8 scoped Ruff / git diff --check                              passed / passed
Full single-core snapshot replay                                      passed
Published manifest                                      12 files / hashes exact
July rows / rows at or after 2026-08-01                    present / zero
A6 deterministic report                                    passed / zero violations
R7 incident journal                      17 records / 15 batch rejections
R8 copied competitive artifacts                                      zero
R8 seed                                              15 lanes / 94-file binding
```

**Final result: PASSED, zero unresolved findings.**
