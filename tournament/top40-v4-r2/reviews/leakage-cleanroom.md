# Top-40 V4-R2 fifth-restart leakage and clean-room review

Review date: 2026-08-21
Reviewer: independent leakage/clean-room adversarial agent
Reviewed implementation commit: `e4b87be0e49362e321fb3e2781d8c10812918d31`
Review-integration HEAD before this report: `fcee2c7aaf5376715732418e41e229086cb309b4`
Branch: `quant-portfolio-blind-top40-v4-r1-v2-restart5`
Gate status: **PASSED**
Unresolved findings: **0**

## Scope and method

This review inspected the exact R7 fresh-successor code, broker, runtime, team kit, frozen
authorities, tests, and physical preactivation filesystem. It specifically re-attempted the known
clean-room seams: predecessor/provenance reuse, direct-library and CLI admission bypass, forged or
replayed batch capabilities, partial-batch score opening, receipt substitution and ambiguous JSON,
malformed-batch termination, archive link/content substitution, progress disclosure, private model
state, installed skills, worker bootstrap order, and holdout/network/peer boundaries. It did not
activate R7, launch a competitive model phase, evaluate a candidate, or open predecessor score or
summary contents.

I independently ran the exact current R7 suite with one CPU and temporary pytest state: **165
passed**. The intended R1 compatibility and source-archive suites produced **29 passed**. Ruff
passed over the current V4 security/runtime, broker, and R7 test scope, and `git diff --check`
passed. The fresh-authority, completed-recovery, and frozen-smoke semantic validators passed.
Before this report edit, `_implementation_commit` resolved the clean integration HEAD
`fcee2c7aaf5376715732418e41e229086cb309b4`; the implementation under review is its parent
`e4b87be0e49362e321fb3e2781d8c10812918d31`, while the intervening commit contains only the
final lifecycle review.

The exact `FRESH-RESTART-AUTHORITY.json` SHA-256 is
`7610daae55d4f9cec3e242162cf100d4236e5f5a3d330f07349715f94dd47910`.
The frozen v11 smoke SHA-256 is
`7896fadce3923654b790014d6e6429287e4be44290116b17ac58b4d33a7ce5a1`, with canonical
self-hash `3fe6257ef1df37ecf03879a4875ec835be155e30e232d98432dffaa44a327873`.

## LC-01 — fresh R7 provenance and predecessor isolation: closed

The schema-4 restart authority binds every stopped private incident, including R6's 37-record
batch-admission incident, six accepted-and-terminal Team-02 trials, the two exact rejected candidate
bundle/receipt identities, no discovery feedback disclosure, and no outbox archive. The two rejected
candidates were neither accepted nor evaluated. The authority separately declares
`research_provenance_reused` and `results_reused` false at both the R6-incident and successor levels.
It is organizer-only, outside every team profile, and is evidence for genesis admission rather than
input to a team or evaluator.

The physical R7 surface independently confirms that assertion. All 15 lanes are trial-zero and
contain only their tracked brief/policy, candidate README, and three one-byte-LF `.keep` markers;
all 45 markers are regular single-link files. There is no R7 lifecycle journal, activation freeze,
candidate, outbox, feedback, work product, research receipt, source archive, result, certificate,
nomination, selection, release, or private model runtime. The only report data are the two frozen
common BTC regime/return files. No R6 candidate, receipt, feedback, journal record, model state,
research context, or result is copied into R7.

Activation's fresh-start gate exact-enumerates the frozen tournament/report surface, permits only
the narrowly defined empty lock/bootstrap nodes, rejects residue and links, and binds the 15-lane
count, empty-journal hash, file count, and chained seed head. The predecessor worktrees, their Git
metadata, and the authority itself are denied by the team permission profile and worker repository
mask.

## LC-02 — sole whole-batch admission authority: closed

Only the canonical `consume_batch` frame in `scripts/top40_v4_r2_team_broker.py` can obtain a batch
capability. The check binds the exact broker pathname, module `__file__`, original function code,
live `FrameType` identity, root, team, and phase. A copied frame identifier, reconstructed dataclass,
replayed capability, direct library call, or disabled `is-run` CLI path cannot satisfy it. Those
attempts fail before result-lock mutation, journal append, receipt recovery, or evaluator access.

Before request one is accepted, preflight stably captures the exact live outbox and every candidate
source bundle; validates the full request, metadata, attestation, compact stateless source subset,
phase uniqueness, and simulated mechanism history; recovers and validates all private candidate
receipts; and durably appends one ordered `batch_preflighted` record. The journal and live capability
bind the outbox hash plus ordered candidate IDs, source-bundle hashes, and canonical receipt hashes.
Replay rejects an accepted trial whose candidate, source, phase position, or receipt hash differs.
Each final `run_is` reopens the exact receipt with the expected phase and requires its SHA-256 to
match that ordered batch authority before mechanism validation, the accepted record, or evaluator
output. The post-preflight wrong-phase/receipt-substitution regression leaves the journal byte-exact
and creates no evaluator directory.

The immutable receipt reader uses no-follow stable reads and requires a current-owner, mode-0600,
regular, single-link file. Parsing rejects duplicate keys at every object level, nonfinite values,
invalid UTF-8/JSON, extra or missing fields, wrong phase/runtime/source/profile/launch bindings, and
any byte representation other than the canonical sorted ASCII form. This closes ambiguous semantic
residue and same-owner replacement after whole-batch preflight.

## LC-03 — score-blind failure classification and resume safety: closed

Deterministic request, metadata, attestation, source, mechanism, and immutable-receipt semantic
conflicts are classified before score data opens. They can produce only a sealed rejection
capability tied to the live broker frame, exact root/team/phase/outbox, candidate prefix, and current
journal head. Terminal rejection revalidates all of that state and, for refinement, revalidates the
exact discovery feedback/archive before appending. It records one fixed bounded reason rather than
candidate-controlled diagnostics, consumes no trial, declares `score_data_opened: false`, and
cannot occur after a durable preflight or pending accepted request.

Filesystem I/O, unsafe topology, locks, isolation probes, runtime faults, and other infrastructure
failures propagate without retirement and remain resumable. A malformed published outbox can be
archived as exact rejection evidence, but no partial candidate is evaluated. Crash recovery accepts
only the event-bound outbox bytes and content-addressed archive. Archive directories and files must
be current-owner, private, regular, and single-link; stable no-follow reads and the filename digest
bind content. Multiple archives, wrong names, hard links, symlinks, substitutions, or changed bytes
fail without journal mutation. Completed refinement also revalidates exact prior feedback and
archive, preventing a malformed new batch from masking lost prior-phase authority.

The shared broker lease serializes model and result-bearing work. Model processes exit before the
organizer consumes an outbox, and accepted trials become durable before the evaluator opens the
snapshot. Interrupted accepted trials are closed only by their journal-bound terminal path; the
broker neither fabricates evidence nor repeats a completed trial. Team-visible feedback is written
only after the whole phase completes and is immutably tied to journal records and the archived
outbox.

## LC-04 — private model runtime, installed skills, and worker bootstrap: closed

Launcher v11 derives the sole model command internally and binds Codex CLI `0.148.0`, model,
prompt, team/phase, team kit, sanitized environment, custom no-network profile, disabled web,
browser, plugin, app, skill and multi-agent features, and per-team runtime. `--ignore-user-config`
precedes every security override and disabled flag, and no legacy `--sandbox` flag can supersede the
profile.

Every team receives distinct organizer-private `HOME`, `CODEX_HOME`, and `TMPDIR`. Only private
authentication plus the empty system-skill marker may persist; volatile databases and SQLite
companions, logs, queues, shell snapshots, wrappers, and sandbox scratch are exact-enumerated,
owner/mode/link checked, bounded, and removed after each subprocess. Cleanup is crash-idempotent
only for strict known prefixes; unknown names or unsafe topology fail closed. Neither a host skill
catalog nor cross-team client state can survive into a later phase.

The exact frozen organizer-observed smoke records `sandbox: custom permissions`, network disabled,
an empty skill catalog/system marker, isolated TMPDIR, host-skill and private-auth denial, peer
private-runtime read/write denial, a single requested own-lane sentinel, no durable lane delta after
verified cleanup, and removal of the disposable private runtime. Its semantic validator passed.
This review did not recreate a real private runtime or model session because R7 was required to
remain unstarted; the frozen physical evidence and current regressions bind the unchanged profile,
argv, runtime, cleanup, and 11-control boundary.

The strategy worker has no candidate-controlled pre-mask execution path. Its trusted parent builds
the child environment and supplies only the exact frozen R7 `src` bootstrap needed to resolve the
organizer worker. The candidate bundle is neither the initial working directory nor an initial
import path. Before candidate import, the worker establishes namespaces, masks the repository and
common parent, rebuilds `sys.path` around staged Python-only source/runtime, changes into the staged
bundle, and applies Landlock, seccomp, audit, resource, process, credential, network, and write
restrictions. The real namespaced startup and Python-only mount regressions passed.

## LC-05 — source, holdout, peer, and progress boundaries: closed

Descriptor-relative capture rejects symlinks, hard links, FIFOs/devices, hidden executables,
unexpected files, path substitution, and excessive aggregate content. The captured bytes are the
archive, static-review subject, worker input, evaluation input, and nomination identity. Only
`strategy.py` is executable. Its sole module-level class/factory shape and exact stateless
`target_weights` signature remain enforced; forbidden state, decision-time branching, helper code,
imports, RNG, dynamic loading, comprehensions, executable docstrings, ordinal/encoding channels,
opaque literals, and packing/arithmetic substitutes are rejected. Exact captured-source
append/corrupt-future invariance remains required before nomination.

The team kit discloses every enforced batch invariant without mentioning a predecessor strategy or
result: full-batch score-blind admission, the exact neighborhood-coordinate/material-parameter
equality, `{}` for non-neighborhood controls, mechanism family/pivot semantics, receipt/static
source rejection, and deterministic retirement behavior. It also states that earlier editions,
other lanes, organizer state, raw data, skills/plugins, web/network, and status are unavailable.

The OS profile and worker deny peer lanes, predecessors, repository history, organizer-private
state, host skills/auth, `/proc` host state, and network. Shared pre-selection status projects a
fixed genesis view rather than journal growth, counts, order, timing, or dispositions. Teams receive
only lane-local normalized phase feedback. The holdout retains the full July 2026 window behind the
exclusive `2026-08-01T00:00:00Z` boundary, is evaluated only after research processes exit, and has
no interim or cross-team disclosure path.

## Gate decision

**PASSED — zero unresolved leakage or clean-room findings.** R7 is a physically clean, trial-zero
successor; predecessor competitive provenance is evidence-only and inaccessible; whole-batch
authority is canonical, durable, and bound through exact receipt bytes at final acceptance; failure
classification is score-blind and resumable; private model/skill and worker-bootstrap boundaries
remain sealed; and source, peer, progress, network, and July-2026 holdout controls remain intact.
No activation, competitive model/team phase, candidate evaluation, or predecessor score inspection
occurred during this review.
