# Top-40 V4-R2 seventh-restart leakage and clean-room review

Review date: 2026-08-22
Reviewer: independent leakage/clean-room adversarial agent
Reviewed exact implementation HEAD: `d5fc45d1c7ee9efe493b5304af9a30ae9cbdf84b`
Branch: `quant-portfolio-blind-top40-v4-r1-v2-restart7`
Gate status: **PASSED**
Unresolved findings: **0**

## Scope and method

This review inspected the exact R9 code, canonical broker, research runtime, journal,
orchestrator, automatic representative/certificate path, team kit, frozen authorities, tests, and
physical preactivation surface. It adversarially checked removal of the decision model, score and
progress disclosure, robust representative ranking, truncated-refinement handling,
pre-acceptance causal review, ordered receipt binding, certificate capture/fallback semantics,
decision/outbox residue, crash and substitution handling, predecessor reuse, private Codex state,
serial execution, and the established source, worker, peer, network, and holdout boundaries. I did
not activate R9, launch a team/model phase, evaluate a candidate, run historical release, or inspect
predecessor score or summary contents.

I independently ran the exact R9 suite with single-thread environment controls: **198 passed**.
The release owner reports **29 compatibility/archive tests passed** and scoped Ruff/diff checks
clean. The exact fresh-restart authority, frozen model-smoke receipt, read-only preactivation
status, and 15-lane isolation audit passed. Preactivation reports the GENESIS head, zero journal
records, and no activation identity; the canonical activation path alone creates the pinned empty
journal under the result lock. The restart-authority SHA-256 is
`c8dbc0b55a465b785b6cfe7ca960a894617d3c86882fcf45af9d9f5eb2e8a60b`; the frozen v13 smoke
SHA-256 is `a11bc30bfbb59e5aa328d7e44eea9257a6d1dfb66d0e838a1abd9cc41ed2fbe9`, with canonical
self-hash `b04c37204929ed15e0c12c711876e84dfebdeef0237c6a406bad3490d5b3de0c`.

Earlier in this exact R9 clean-restart review I ran the canonical bounded Team-01 physical
permission-profile probe. All eleven controls returned true: intended reads and own-lane writes
work; organizer/repository reads, cross-lane writes, network, host process visibility, host skill
roots, private auth, and peer-private reads/writes are denied; the skill catalog is empty. The
post-probe owner-only private runtime was exactly inspected and removed. The later changes through
the reviewed HEAD affect only organizer-private source-review publication, automatic promotion,
selection accounting, documentation, and their tests; the frozen v13 profile, command ordering,
probe implementation, model-smoke authority, and OS permission boundary are unchanged. No private
runtime, probe artifact, or lane delta remains.

## LC-01 — fresh R9 provenance and predecessor isolation: closed

The schema-6 authority exactly records the stopped R8 minimum-finalist incident as private
evidence. It binds 38 accepted trials, 37 terminal trials, one pending trial, no nominations or
selection, and explicitly declares both result and research-provenance reuse false. The top-level
successor authority repeats `results_reused: false`, `research_provenance_reused: false`, and no
feedback disclosure. These hashes and counts are activation evidence only; they are not imported
into a lane, candidate, ranking, or evaluator.

The R9 filesystem is trial-zero across all 15 lanes. It contains no activation freeze, competitive
journal record, candidate, feedback, outbox, work product, research session, source review/archive,
result, certificate, nomination, selection, release, or private model runtime. Only the tracked
brief/policy, candidate README, and one-byte-LF seed markers occupy a lane. No R8 candidate,
feedback packet, source/receipt, result, model state, certificate, or decision is present.

The permission profile grants a team only the current sanitized kit and its own current lane. The
R8 worktree, authorities, results, Git metadata, and the R9 restart authority are outside that
allowlist. The physical profile reproduced the default-deny boundary, and the strategy worker masks
the repository/common parent before candidate import.

## LC-02 — no decision model or team-controlled selection path: closed

The canonical broker launches only discovery and refinement. Its CLI has no decision launch or
consume command; the exported runtime rejects phase `decision` before any process; the broker
launch path rejects it again; and retained legacy `consume_decision` rejects unconditionally before
reading, retiring, nominating, or archiving a team decision. No model, manual repair context, host
skill, or team-authored certificate participates in representative selection.

Unexpected outbox names—including legacy `decision.json`—are detected through a stable pinned
directory capture during score-blind inspection, both preflight passes, every trial acceptance,
automatic finalization, and terminal resume. Before preflight they are deterministic lane-local
repair findings; after durable authority they are integrity failures. They can neither be silently
archived nor converted into a nomination or retirement.

The shared broker lease covers research, evaluation, automatic representative compilation,
nomination, close, and release. The broker immediately promotes a successful discovery lane when
score-blind refinement admission terminates. A crash before that promotion is restart-safe:
`run_team` repeats the exact retired-evidence validation and promotion, while `close_is` detects the
pending promotion immediately after evidence validation and fails before registry, freeze, or
journal mutation. The journal also refuses a selection that discards such a success.

## LC-03 — pre-acceptance causal source receipt and batch authority: closed

Every candidate receives synthetic causal review before its first accepted record and before any
score data opens. The review revalidates the exact phase-bound candidate receipt, recaptures the
source bundle, repeats the compact stateless static gate, and executes the three-scenario
past-only/future-appended/future-corrupted invariance check. Candidate execution or invalid target
responses and invariance mismatches are deterministic score-blind findings. Worker launch,
namespace, protocol, storage, timeout, or unsafe-topology failures propagate as infrastructure
errors and remain resumable rather than retiring the lane.

The organizer-private source-review receipt is canonical duplicate/nonfinite-rejecting JSON in an
owner-only regular single-link file. It binds team, candidate, exact source-bundle SHA-256,
executable set, frozen static-check list, timestamp, six decision rows, and identical
past/appended/corrupt target hashes. Publication pins every organizer-private directory component,
uses a fixed owner-only staging name, fsyncs the staging inode and directory, and creates the final
name by a no-replace hard link. A retry removes a staging-only scratch inode, normalizes only the
exact same-inode two-link crash prefix, rejects unrelated hardlinks or unsafe topology without
mutation, and refuses a disappeared final rather than publishing empty or newly timestamped bytes.
The caller then validates the exact canonical final authority as regular, owner-only, stable, and
single-link.

The durable `batch_preflighted` event and live sealed capability bind ordered candidate IDs,
source-bundle hashes, phase-bound candidate-receipt hashes, source-review hashes, and exact outbox
hash. Each `run_is` revalidates the outbox directory, exact live source capture, candidate receipt
with expected phase, and current source-review SHA before appending acceptance or invoking the
evaluator. Final automatic selection locates the candidate's phase/index in that journal event and
revalidates the same review SHA. A changed, replayed, reordered, wrong-phase, or substituted
receipt therefore fails before score or journal mutation.

## LC-04 — automatic ranking and score confidentiality: closed

The organizer considers successful terminal observations only. The frozen lexicographic order is
higher worst-fold double-cost Sharpe, higher median-fold double-cost Sharpe, higher trial-adjusted
confidence, higher gross edge per turnover, lower annualized turnover, then candidate ID. Missing
edge density ranks last. The broker computes the candidate once, and `nominate` independently
recomputes and requires the same identity before mutation.

A successful discovery lane whose score-blind refinement batch terminates retains the truthful
accepted count of eight but is charged `selection_trial_count: 12`. That full charge is used when
ranking every successful candidate in the lane, computing the nomination selection, computing
field-wide adjusted confidence, freezing an advancing representative, and scoring its historical
run. Valid refinement can only add candidates and certificate evidence; it cannot worsen the
already-successful discovery representative under the same twelve-trial rank. Intentionally
withholding a valid refinement batch after seeing discovery feedback therefore provides no
selection advantage. The team kit, shared policy, runtime prompt, and all 15 lane briefs disclose
the actual-eight/full-twelve rule and its purpose.

No ranking result is written into a lane and there is no later team process to observe it.
Candidate summaries used for ranking are journal-bound organizer results; the only score-bearing
lane files remain that lane's already-authorized normalized phase feedback. Organizer-private
source reviews, certificates, nominations, registry, selection freeze, CLI return values, and field
ranking are outside every team profile. Pre-selection status remains a fixed genesis projection, so
order, timing, success counts, fallback use, and promotion state do not become cross-lane oracles.

At field close, fully qualified representatives rank first. If fewer than five qualify, only the
shortfall is filled with the strongest remaining successful representatives and each is explicitly
labeled `robust-ranked-representative`; failed gates remain failed. Fewer than five successful teams
fails closed. A zero-volatility but successful finalist stays represented with zero risky weight
and unused capacity in cash, avoiding a score-dependent abort or post-selection rewrite.

## LC-05 — single-capture certificate and truthful fallback: closed

The automatic certificate is compiled only from immutable journal request hashes and their
accepted metadata tags, in trial order, under the team-specific organizer-private certificate
namespace. The broker first revalidates the selected candidate's exact preflight source-review
authority. The immutable write is idempotent: a crash before nomination can resume only with the
same compiled bytes; conflicting residue fails.

`_certificate` performs one stable no-follow byte capture and passes that same captured payload to
both strict qualification and fallback validation. There is no second path reopen between a
qualification failure and representative preservation. The parser rejects duplicate/nonfinite or
noncanonical objects, wrong identity/schema, invalid hashes, duplicate citations, and citations
whose immutable request lacks the named tag.

Empty cells, incomplete coverage, insufficient breadth/neighborhood, or a failed sign-inversion
trial are qualification shortfalls, not false integrity claims: diagnostics set `qualified: false`,
the neighborhood gate fails, and the nomination records the exact failed gates and
`fallback_does_not_change_gate_results: true`. Successful sign-inversion evidence still requires
both terminal successes, matching parent/mechanism/horizon/control/risk authority, and exact
negative archived targets. Corrupt or missing underlying artifacts remain hard integrity errors.

## LC-06 — repair, runtime, source, and holdout boundaries: closed

The fixed initial process plus at most three score-blind repairs remain bound by durable private
issue/attempt chains. Lane-visible admission feedback is reconstructed from the exact private
attempt before another process and contains deterministic self-only findings, never scores, trial
outcomes, peer state, or holdout data. Whole-batch admission still precedes every trial; malformed
or absent batches terminate only through exact broker capabilities and archived/missing evidence.

Launcher v13 pins Codex CLI `0.148.0`, model and prompt/environment hashes, approval `never`, custom
permission profile, network off, and disabled web/browser/app/plugin/skill and multi-agent
capabilities. Per-team private `HOME`, `CODEX_HOME`, and `TMPDIR` preserve only auth plus an empty
system-skill marker; volatile databases and SQLite companions, logs, snapshots, wrappers, and
sandbox scratch are exact-enumerated and cleaned after every subprocess. The frozen v13 smoke and
the physical probe bind the same boundary.

Descriptor-relative source capture, the restricted executable/AST subset, worker repository mask,
Python-only staged runtime, Landlock, seccomp, audit/resource/process controls, network denial,
exact archived bytes, and nomination-time review binding remain intact. The holdout still contains
all of July 2026 behind the exclusive `2026-08-01T00:00:00Z` boundary. Model processes exit before
batch evaluation, and the broker lease serializes teams, evaluation, automatic representative
compilation, selection, and historical access with no interim disclosure path.

## Gate decision

**PASSED — zero unresolved leakage or clean-room findings.** R9 remains a clean trial-zero
successor with no competitive R8 reuse. Automatic representative selection eliminates the
decision-model and host-skill surface; exact pre-acceptance causal-review receipts are atomically
published and ordered into batch/candidate authority; truncated successful lanes retain their
truthful accepted count without gaining a lighter selection penalty; score-derived ranking and
certificates remain organizer-private; truthful fallback never changes failed gates; and the
repair, source, peer, network, progress, private runtime, serial lease, and July-2026 holdout
boundaries remain sealed.
