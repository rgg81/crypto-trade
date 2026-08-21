# Top-40 V4-R2 sixth-restart leakage and clean-room review

Review date: 2026-08-21
Reviewer: independent leakage/clean-room adversarial agent
Reviewed exact HEAD: `8335719049ddce0fb5b928a3905017b388b1fccd`
Branch: `quant-portfolio-blind-top40-v4-r1-v2-restart6`
Gate status: **PASSED**
Unresolved findings: **0**

## Scope and method

This review inspected the exact R8 source, canonical broker, research runtime, journal and
orchestrator, team kit, frozen restart/smoke authorities, tests, and physical preactivation
filesystem. It concentrated on score-blind whole-batch repair, repeated model processes, durable
attempt/issue/feedback chains, direct-call and capability bypass, receipt/archive substitution,
crash idempotency, terminal-evidence recovery, private Codex state, predecessor isolation,
candidate/source identity ordering, and the established source, worker, network, peer, progress,
and holdout boundaries. No activation, competitive model/team phase, candidate evaluation,
historical release, or predecessor score/summary inspection occurred.

The complete R8 suite was independently run on the immediately preceding implementation bytes:
**176 passed**; the sole final change was inspected and its new historical-release regression
independently passed on this exact HEAD. The intended R1 suite independently produced **24 passed**.
The release owner reports the exact-current totals as **177 R8 and 24 R1 passed**, with scoped Ruff
and diff checks clean. The exact restart-authority SHA-256 is
`20df6a9f7e325e8fa999ebe8482153bd4c006bd884dfd9c1987c08f97752f896`. The frozen v12 smoke
SHA-256 is `8ce7c6adab43167b54dffdffce8a42b01717762b4d7f821e8d46c996ee5ce5b5`, with canonical
self-hash `4194ba3f54e6986877024eac0b0a12d673cdcdba00dbe4547fe09b8eda05c62b`.

I also ran the canonical bounded Team-01 permission-profile probe on this exact HEAD. All eleven
controls returned true: allowed reads, denied organizer/repository reads, own-lane write,
cross-lane write denial, network denial, host-process hiding, host skill-root denial, empty skill
catalog, private-auth denial, and peer-private read/write denial. Afterward, the only private state
was the expected 18-node Team-01/02 auth-plus-empty-marker tree: owner-only 0700 directories and
0600 regular single-link files, with no links or volatile session data. It was removed using exact
nonrecursive unlink/rmdir targets. No probe file or lane delta remains.

## LC-01 — fresh R8 provenance and predecessor isolation: closed

The schema-5 restart authority is organizer-only and exact-binds the stopped predecessor
incidents. In particular, the R7 incident completed with no admissible candidate: zero IS result
files, zero source archives, zero selected finalists, no winner, and no feedback disclosure. Both
the top-level successor and each incident explicitly bind `results_reused: false` and
`research_provenance_reused: false`. Incident hashes and counts are genesis evidence, not team or
evaluator inputs.

The physical R8 surface is trial-zero. All 15 lanes contain only their tracked brief/policy,
candidate README, and one-byte-LF `.keep` markers in candidate/feedback/outbox/work seed
directories. There is no lifecycle journal, activation, candidate, outbox, feedback, research
session, source archive, result, nomination, selection, release, or private model runtime. No R7
competitive file was copied into R8.

The team profile grants reads only to the current sanitized kit and the team's current lane; the
R7 sibling worktree, its authority, artifacts, and Git metadata are outside that allowlist. The
real OS profile demonstrated the corresponding default-deny boundary, including organizer and Git
denial. The worker masks the repository/common parent before candidate import. Teams cannot read
the R8 restart authority either.

## LC-02 — fixed score-blind repair sessions and disclosures: closed

Only the canonical broker's live `consume_batch` frame can start or finish admission. Direct
library calls, result CLI paths, forged/replayed capabilities, copied frame metadata, wrong
root/team/phase, and broker exception composition fail before trial acceptance or evaluator access.
The shared reentrant broker lease remains held across the initial model process, all repair
processes, outbox consumption, and result-bearing work, so lanes, evaluators, and repair sessions
cannot overlap.

Every initial or repair process uses the same internally derived phase prompt, exact Codex command,
model, environment, team kit, and profile authority. The prompt tells the model only to inspect its
newest lane-local `feedback/admission-*.json`, the exact checker, and the supplied template. The
kit discloses the complete enforced static call/name subset, machine-readable allowlist,
neighborhood/material-parameter identity, whole-batch semantics, and the uniform maximum of three
score-blind repairs. It discloses no predecessor identity, result, field state, score, trial
outcome, or holdout row.

Before each process, an organizer-private canonical session-issue receipt is durably written. The
initial issue plus at most three repair issues form an exact `phase-00..03` chain. Each completed
check writes an organizer-private canonical attempt receipt `phase-01..04`, binding the launch,
input attempt, outbox bytes, ordered candidate IDs/source hashes, and deterministic findings. These
directories, filenames, schemas, byte encodings, modes, owners, and single-link topology are
pinned; teams cannot read them. Unexpected names, links, modes, owners, duplicates, noncanonical
JSON, oversized content, or chain discontinuity fail closed.

The lane-readable admission report is a deterministic projection of that private attempt: source,
metadata, request, static-AST, mechanism, and batch-consistency findings only. It is created or
reconstructed and revalidated before another issue or model process. Thus a crash after the
private attempt but before feedback cannot skip or change disclosure, while a crash after an issue
cannot create an extra repair allowance. Unchanged model output still consumes its issued attempt;
the process-local history cannot reset the durable four-process bound.

## LC-03 — whole-batch admission, terminal evidence, and resume safety: closed

No score data opens until the complete batch passes deterministic admission. Preflight stably
captures the exact live outbox and every candidate bundle; validates requests, metadata,
attestations, source, phase uniqueness, neighborhood coordinates, and mechanism history; and
recovers exact private candidate receipts. One durable `batch_preflighted` event and its live
capability bind the ordered candidate IDs, source-bundle hashes, canonical candidate-receipt
hashes, phase, and outbox hash. Each final `run_is` repeats the expected-phase and exact-receipt-SHA
checks before acceptance or evaluator output.

Candidate receipts and repair receipts use strict duplicate/nonfinite-rejecting JSON, canonical
bytes, no-follow stable reads, and owner/mode/regular/single-link checks. Source and outbox archives
likewise bind exact content and reject symlink, hardlink, FIFO/device, changed-path, changed-byte,
or ambiguous filename substitution. An accepted candidate's archived bytes are the static-review,
worker, evaluation, and nomination identity.

If no outbox exists after all four authorized processes, exact attempt 04 becomes durable
`batch_abandoned` evidence; no outbox or candidate is fabricated. A persistently malformed batch
becomes `batch_rejected` only through the canonical broker, with its exact organizer-private outbox
archive. Neither disposition opens score data or consumes a trial. Infrastructure and topology
failures remain errors rather than deterministic team retirements.

`close_is` revalidates every rejected archive and every abandoned missing-outbox attempt before
registry or selection mutation. The final `historical_release` path now independently repeats the
same terminal-evidence validation before opening selection, recovering a release, appending a
historical request, or touching the sealed snapshot. This closes post-selection deletion,
substitution, and recovery seams. Refinement also revalidates its exact discovery feedback/archive
before terminal mutation.

## LC-04 — private model runtime and real OS boundary: closed

Launcher v12 pins Codex CLI `0.148.0`, `gpt-5.6-sol`, prompt and environment hashes, the custom
permission profile, approval `never`, network off, and disabled web/browser/app/plugin/skill and
multi-agent features. `--ignore-user-config` precedes all profile overrides and disabled flags;
there is no legacy sandbox override. Each team has a distinct organizer-private `HOME`,
`CODEX_HOME`, and `TMPDIR`.

Only private authentication and the empty system-skill marker may persist between subprocesses.
All admitted volatile databases and SQLite companions, logs, queues, caches, snapshots, wrappers,
installation marker, and sandbox scratch are exact-enumerated, owner/mode/link checked, bounded,
and removed in `finally`. Crash cleanup admits only strict known partial prefixes and fails closed
on an unexpected name or target. The frozen v12 smoke independently binds custom permissions,
network disabled, empty prompt/skill catalog, original-home exclusion, host-skill/private-auth and
peer-private denials, isolated TMPDIR, one intended own-lane sentinel, zero durable lane delta, and
full disposable-runtime removal. The exact-current real probe reproduced the boundary without
launching a model session or tournament phase.

The strategy worker receives only a frozen R8-source bootstrap long enough to resolve the trusted
worker. Candidate code is not in its initial working directory or import path. Before candidate
import, the worker establishes namespaces, masks the repository and common parent, rebuilds
`sys.path` around the staged Python-only source/runtime, changes to the staged bundle, then applies
Landlock, seccomp, audit, resource, credential, process, network, and write restrictions. There is
no candidate-controlled pre-mask execution surface.

## LC-05 — source, holdout, peer, and progress boundaries: closed

Descriptor-relative capture rejects links, FIFOs/devices, hidden executables, unexpected files,
path swaps, and aggregate-content excess. Only `strategy.py` is executable. The exact stateless
semantic AST subset continues to reject imports, candidate/module/class state, decision-time
branching, helper delegation, iterators/comprehensions, RNG, dynamic loads, executable docstrings,
ordinal/encoding channels, opaque/high-capacity literals, and packing/arithmetic substitutes.
Exact archived-source future append/corruption invariance remains nomination-bound.

The live profile and worker deny peer lanes, predecessor worktrees, repository history,
organizer-private state, host auth/skills, host `/proc`, raw data, and network. The only permitted
write roots are the team's own candidates/outbox/work directories. Pre-selection status remains a
fixed genesis projection, not a journal/count/order/timing oracle. Admission reports are self-only
deterministic diagnostics and never expose a score or peer state.

The holdout still includes all of July 2026 behind the exclusive
`2026-08-01T00:00:00Z` boundary. Research and repair model processes exit before deterministic
batch consumption; evaluation and historical release are serialized afterward, with no interim
or cross-team disclosure path.

## Gate decision

**PASSED — zero unresolved leakage or clean-room findings.** R8 is a physically clean trial-zero
successor with no reused competitive provenance. Its fixed, bounded repair loop is score-blind,
durably attempt/issue/feedback bound, substitution-resistant, and crash-idempotent. Whole-batch
source/receipt authority remains exact through acceptance and terminal recovery; private model,
skill, predecessor, peer, progress, network, and July-2026 holdout boundaries remain sealed.
