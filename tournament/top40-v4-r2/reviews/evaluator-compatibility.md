# Adversarial evaluator, data, incident, and compatibility re-review

Review date: 2026-08-20

Review target: exact implementation commit
`c117f3b32c34de496cef651383e31cc34e1cc3fc` on branch
`quant-portfolio-blind-top40-v4-r1-v2-restart3` (R5). The review covered evaluator/scoring
semantics, past-only contexts, the July-2026-inclusive snapshot, A6, immutable source capture and
worker staging, launcher-v9 research receipts, R1 behavior, the exact stopped-R4 incident evidence,
and the clean R5 restart surface. It did not activate R5, launch a team or strategy, decode any
predecessor summary/score, or mutate a runtime artifact.

## Gate status

**PASSED. Unresolved findings: 0.**

The R5 evaluator/data/compatibility gate is closed. Activation remains an organizer action after
the review set and its frozen-scope bytes are committed and rebound; this review did not perform
that action.

## R5 restart authority and clean state

- `FRESH-RESTART-AUTHORITY.json` is canonical, regular, single-link evidence with exact SHA-256
  `aac191864a05460fa379e8b628a31e5739ce81141edf31c4a007d9470ccd146c`, equal to the
  activation constant. It declares both `feedback_disclosed` and `results_reused` false and binds
  the original stopped attempts plus the R4 skill-boundary incident.
- The read-only recovery prerequisite accepts the authority, reports no recovery pending, and
  recomputes the score-blind genesis as 15 lanes and 94 exact seed files. The journal is byte-empty
  (`e3b0c442...`). Every lane has only its six authorized seed files; all 45 `.keep` markers contain
  the committed one-byte newline. The exact-surface validator rejects missing, extra, linked,
  non-regular, wrong-owner, or wrong-marker entries.
- R5 has no activation freeze/test output/result lock, research-session tree, source archive,
  candidate implementation, IS result, result receipt, nomination, selection, certificate,
  private holdout result, or historical release. Its report surface contains only the two frozen
  common BTC return/regime authorities. The permitted broker lock is byte-empty.
- `TOP40_V4_R2_LAYOUT.branch` binds the future activation to
  `quant-portfolio-blind-top40-v4-r1-v2-restart3`; activation remains one-shot, commit-bound, and
  scope-bound. A stopped predecessor activation or launch is evidence only and cannot authorize an
  R5 command.

## Exact R4 incident evidence and non-reuse

The private R4 worktree was inspected by hashes, lifecycle structure, and filenames only; no
summary or score payload was decoded.

- The preserved activation file, activation record self-hash, and activation-test output reproduce
  `839a8499...`, `302528e9...`, and `085eb167...` respectively. The Team-02 decision-launch file
  reproduces `52248abc...`.
- Pure journal replay accepts all 49 canonical chained records and reproduces file hash
  `dc8681fe...` and head `ddfd2104...`. Team 01 has 12 contiguous succeeded trials and is retired;
  Team 02 has 12 contiguous succeeded trials. There is no pending accepted request, selection, or
  Team-02 nomination.
- Team 02's outbox contains only `.keep`; no decision outbox or Team-02 certificate exists. Thus
  the interrupted decision model did not publish a decision, nomination, certificate, or further
  lifecycle transition.
- The exact preserved nontracked artifact surface contains 478 files. Rehashing sorted
  `path<TAB>size<TAB>sha256<LF>` entries independently reproduces
  `b733dd34689b9b8324fd0f3457f558105703be1aa9a54a07f8efe277f68dffb7`.
- The R4 trial artifacts remain structurally terminal but their research provenance is explicitly
  invalid because the model crossed the frozen skill boundary. R5 neither copies nor references
  those results as lifecycle/evaluator inputs; its journal and result surface are empty and its
  authority says `results_reused: false`.

## Snapshot, July 2026, and A6

- The manifest SHA-256 is
  `c21fdcefc39961cd4408277e6cbb4833c31178cf86fa5d166499a3df6a8e7af7`. All 12 declared
  files independently match their manifest sizes and SHA-256 values, are regular single-link
  files, and byte-match the fully reviewed R4 copy.
- Config and manifest use the exclusive hard end `2026-08-01T00:00:00Z`, so July 2026 is included.
  Direct column scans found 59,605 July transaction bars, 42,138 July funding rows, 28,494 July
  mark rows, and 160 July membership rows, with zero rows at or after August 1. Maxima are July 31
  16:00 for bars/marks, July 31 23:00 for funding, and July 27 for membership.
- Deterministic A6 regeneration returns exact report hash
  `a1f9175b7728efde33d9d421b08c6cbcfe904783ba0f856b52504a28a453776e`, status `passed`,
  zero violations, 670 contract-metadata symbols, 328 distinct membership symbols, and 13,026
  membership rows. The runner requires the same A6 authority both before and after every result
  command.

## Evaluator and scoring semantics

The R5 bytes of `top40_v4`, `engine_v2`, `metrics_v3`, `protocol`, `risk_policy`, `runner_v4`,
`scoring_v4`, `source_archive_v4`, `snapshot`, and `pure_crypto_universe_v4_r2` are byte-identical
to R4. Independent focused tests confirm the following unchanged semantics:

- A strategy receives only closed bars and funding strictly before each decision, restricted to
  the eligible membership surface. Fills occur at the next executable transaction open.
- Funding cash flow is `-quantity * mark_price * funding_rate`; funding at a rebalance boundary is
  charged to the carried position before the trade. Interior and forced-exit-boundary funding are
  included. Mark notional sizes targets, while transaction opens size trades/costs.
- Fees, slippage, participation limits, residual delisting settlement, risk actions, insolvency,
  and nonfinite inputs remain fail-closed. Base, double-cost, and triple-cost evaluations are real
  reruns over the same grid, including risk-action costs.
- Nomination-time sign inversion requires a cited accepted baseline, equal mechanism/grid/control
  metadata, equal risk-policy authority, the same canonical target grid and rebalance instructions,
  and exact elementwise target negation.
- Team-level trial adjustment remains the bounded Bonferroni form
  `1 - trials * (1 - probability)`. Selection repeats the adjustment against all accepted field
  trials, applies the frozen inclusive field-confidence floor, then uses the deterministic ranking
  key. The holdout remains nine quarters through July 2026 with a five-positive-quarter winner
  gate.

## Source archive and launcher-v9 receipts

- Candidate capture pins every lexical directory component with no-follow directory descriptors.
  It enumerates descriptor-relative entries, accepts only bounded UTF-8 regular single-link files,
  rejects symlinks/FIFOs/generated or opaque files, and verifies descriptor/final-entry and full
  before/after tree identities. The content-addressed archive binds candidate root, entrypoint,
  ordered file manifest, exact bytes, and source-bundle hash.
- The trusted runner rereads and rehashes the archive, proves it equals the current live capture,
  then materializes the worker exclusively from archived bytes. R2 stages only `.py` files and
  re-verifies the exact staged manifest/fingerprint before execution. Pre/post live-source,
  evaluator, manifest, config, dependency-lock, and A6 authorities must remain identical.
- The archive's intentionally stable schema remains
  `top40-v4-r2-candidate-source-archive-v1`; launcher/research authority is v9. Launch records and
  candidate research receipts now bind `top40-v4-r2-research-runtime-v9`, model `gpt-5.6-sol`,
  high reasoning effort through the exact command hash, frozen phase-prompt and environment
  hashes, launch-authority hash, profile/team-kit hashes, source-bundle hash where applicable,
  passed probes, and the exact `model_runtime_sha256`. The broker cannot supply alternate prompt
  text; the launcher constructs the only authorized prompt and command.
- `PRETRIAL-MODEL-SMOKE.json` has exact file SHA-256
  `c11c3e5bd22d809a7483188c6e24138183f2d21028a8f6d400936153607fc6d0`, equal to the
  activation constant, and its canonical record self-hash recomputes to
  `67b59accec854ee9f825f81580124eb97bfd21acdb132b1854500252ea83a4f9`. Semantic validation
  also recomputes the exact command, prompt, environment `97bf6096...`, model runtime
  `cb4b01fe...`, profile, sentinel, skill-marker, record, and canonical session-UUID bindings.
  The receipt proves an empty skill catalog, isolated TMPDIR, denied host-skill/private-auth and
  peer-private-runtime reads/writes, verified cleanup, and Codex `0.148.0`.
- Runtime construction pins `codex-cli 0.148.0`, uses deterministic private per-team
  `HOME`/`CODEX_HOME`/`TMPDIR`, and retains across phases only authentication plus the empty
  system-skill marker. Before mutation it validates the complete admitted tree, including exact
  names, types, owner, single-link regular files, owner-only modes, bounded sizes, and exact wrapper
  symlink targets. It then explicitly removes every admitted database/log/queue/snapshot/wrapper
  and sandbox-scratch child, fsyncs both affected roots, and revalidates the empty session surface.
  Cleanup runs before and after prompt inspection and after every completed, failed, interrupted,
  or timed-out phase, so hidden client state cannot cross phases; unexpected or unsafe residue is
  rejected without removal.
- Codex 0.148's one known exception, `installation_id` created explicitly as `0644`, is normalized
  before full-tree validation through an `O_NOFOLLOW` bounded read/write descriptor. Only a
  regular, current-owner, single-link file of at most 1 KiB with exact mode `0600` or `0644` is
  admitted; `fchmod(0600)`, file fsync, descriptor-before/after/final-lexical identity, final type
  and mode, and parent-directory fsync must all pass before cleanup. The symlink regression rejects
  and preserves both an outside target's bytes and its `0644` mode.
- Cleanup is crash-idempotent through every admitted nested deletion state. Wrapper and sandbox
  directories may contain only a subset of the exact expected names after a prior unlink prefix;
  every remaining regular file still undergoes owner/mode/link/size checks and every remaining
  wrapper symlink must be current-owner and target the exact pinned Codex binary. Missing children
  are skipped during resumption, then the now-empty parents are removed and roots fsynced. Tests
  exercise a partial wrapper plus missing sandbox lock through successful normalization, while a
  remaining wrong-target wrapper link rejects and is preserved without mutation.
- Every Codex, profile-probe, and prompt-inspection subprocess receives a child-only `umask 077`.
  An independent local subprocess check produced mode `0600` from a requested `0666` file without
  changing the organizer process. Current `codex --version` is exactly `codex-cli 0.148.0`; any
  version, command, prompt, environment, model-runtime, profile, permission, owner, link, residue,
  probe, or receipt drift fails closed.

## R1 compatibility

The default-edition R1 external suite passes 24/24. R1 retains its original branch, 12 teams,
five-team advance count, paths, schemas, worker bundle behavior, and evaluator behavior. R5
restart authority, 15-lane genesis checks, A6-R2 contract, field-wide adjustment, launcher-v9
cleanroom boundary, and model-runtime receipt fields are selected only for R2.

## Focused evidence

```text
R2 exact-current contract/activation/security suite                 121 passed
R1 default-edition external-contract suite                           24 passed
Focused past-only/funding/cost/risk evaluator set                    14 passed
Source-archive boundary suite                                         5 passed
All 12 manifest files: declared hash/size and R4 identity               passed
July rows / rows at or after 2026-08-01                    present / zero
A6 deterministic report                                    passed / zero violations
R4 journal / pending accepted requests                              49 / 0
R4 preserved artifact count/hash                               478 / exact
R5 journal / copied trial-result artifacts                         empty / none
R5 seed authority                                            15 lanes / 94 files
Codex runtime pin                                           codex-cli 0.148.0
isolated child requested 0666 / actual mode                           0600
Ruff (no cache) / git diff --check                            passed / passed
```

**Final result: PASSED, zero unresolved findings.**
