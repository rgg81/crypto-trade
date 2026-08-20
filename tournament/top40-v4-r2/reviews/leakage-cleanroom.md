# Top-40 V4-R2 third-restart leakage and clean-room re-review

Review date: 2026-08-20
Reviewer: independent leakage/clean-room adversarial agent
Implementation commit: `c117f3b32c34de496cef651383e31cc34e1cc3fc`
Gate status: **PASSED**
Unresolved findings: **0**

## Scope and executed evidence

This review inspected the exact R5 third clean-restart implementation after the installed-skill
incident. It covered the fresh-restart authority, predecessor denial, per-team private model
runtime, rendered skill catalog, exact Codex command and environment, permission profile, physical
OS isolation, phase-fresh client-state cleanup, smoke and candidate receipts, broker behavior,
progress oracles, holdout separation, source capture, and the previously approved compact causal
source gate. It did not activate the edition, launch a research model phase, evaluate a candidate,
or inspect predecessor score or summary contents.

Executed evidence:

- Exact-current R2 suite: **121 passed**; the four focused cleanup topology tests were also rerun
  independently and passed.
- Intended R1 compatibility suite (`tests/tournament/test_top40_v4.py`): **24 passed**.
- Ruff on the changed runtime and tests: **passed**.
- `git diff --check`: **passed** before this report rewrite.
- Frozen smoke receipt SHA-256
  `c11c3e5bd22d809a7483188c6e24138183f2d21028a8f6d400936153607fc6d0`
  and record SHA-256
  `67b59accec854ee9f825f81580124eb97bfd21acdb132b1854500252ea83a4f9`
  passed exact semantic validation against the current Codex 0.148.0 command, profile,
  environment, model runtime, prompt, skill marker, and strict UUID session identity.
- Fresh authority SHA-256
  `aac191864a05460fa379e8b628a31e5739ce81141edf31c4a007d9470ccd146c`
  matched the activation constant and exact tracked bytes.
- The canonical real Team-01 profile probe passed all **11** returned controls: allowed sanitized
  reads and own-lane write; denied organizer/holdout/peer reads, peer-lane write, network,
  host-process visibility, both host skill roots, private auth, peer-private read, and peer-private
  write; the rendered skill catalog was empty.
- Separate bounded real-profile checks denied the exact previously exposed
  `cup50-team02-monitor/SKILL.md`, host authentication, the current restart authority, both stopped
  R4/R3 authority and journal paths, the original-worktree journal, and the peer private-runtime
  root.
- After every probe, both created private runtimes contained only a `0600` authentication file and
  the exact `0600` empty-system-skill marker under `0700` directories. Their private `HOME` and
  `TMPDIR` were empty; no database, log, queue, memory, shell snapshot, wrapper, installation ID,
  or sandbox scratch survived. The disposable runtimes were then exactly inspected and removed;
  fresh seed validation passed with 15 lanes, 94 files, and a byte-empty journal. All lanes remained
  seed-only and the broker lock remained byte-empty.

## LC-01 — installed skills and private model state: closed

Each team receives a distinct organizer-private `HOME`, `CODEX_HOME`, and `TMPDIR`. The only
durable client bytes are authentication and the exact empty-system-skill marker. The actual model
profile cannot read even its own private authentication or any peer runtime. The pinned CLI renders
the model-visible prompt before every launch; admission rejects skill instructions, a `SKILL.md`
locator, or host skill/plugin roots. The physical profile independently denied both host catalog
roots and the exact skill that caused the predecessor incident.

Every Codex child starts under umask `0077`. The runtime exact-enumerates bounded client artifacts,
rejects unexpected names, unsafe types, links, ownership, topology, permissions, and aggregate
size, then explicitly removes every admitted state-bearing node. Cleanup runs before prompt
inspection, after it in `finally`, at successful probe completion, and after a completed, failed,
or interrupted live phase in `finally`. A later retry starts with the same pre-clean, so a failed
probe cannot carry residue into a model phase. Cleanup is crash-idempotent: an interrupted deletion
may leave only a strict subset of the exact arg0-wrapper children or an otherwise exact private
sandbox directory whose lock was already removed. Present children still require their exact
name, type, owner, mode, link target, and bounds; unexpected children and wrong targets reject
unchanged before cleanup resumes.

The first exact-current physical attempt against the superseded cleanup correctly failed closed
because Codex explicitly created `installation_id` as `0644` despite the child umask. The final
implementation narrows only that named, owner-owned, regular, single-link, at-most-1024-byte leaf
from exact mode `0600` or `0644` through an `O_NOFOLLOW` descriptor. It fsyncs, checks stable
device/inode/owner/link/size identity against the lexical path, then performs the complete surface
validation and explicit cleanup. Symlinks and all broader permission exceptions still reject. The
rerun passed and left the exact auth-plus-marker postcondition.

## LC-02 — exact launch, smoke, and receipt authority: closed

There is one live model launcher and it accepts no caller-supplied model or prompt. It internally
derives the fixed model, high reasoning effort, phase prompt, post-reset argv, profile, disabled
features, and sanitized environment. `--ignore-user-config` precedes every security override and
disabled-feature flag; no legacy `-s` or `--sandbox` option can supersede the custom permission
profile. `--ephemeral`, approval `never`, no network, no web/browser/plugins/apps/subagents, and the
per-team paths are part of the exact command or semantic profile authority.

Launch authority schema 2 binds the exact command, model, prompt, environment, model-runtime,
profile, team-kit, team, and phase hashes. Candidate receipt schema 2 repeats those bindings and
adds the exact launch receipt and captured source-bundle identities. Validation requires canonical
bytes, so compact/reordered/duplicate-key residue and path substitution do not create alternative
authority. The frozen v9 smoke additionally binds the actual organizer-observed empty catalog,
host/private/peer denials, isolated temp path, custom-permissions sandbox, requested lane-local
sentinel, exact model reply, current CLI, and self-hash. Activation and every direct launch validate
that receipt before model admission.

## LC-03 — predecessor, cross-lane, network, and holdout boundaries: closed

`FRESH-RESTART-AUTHORITY.json` records the stopped predecessor incidents, no result reuse, and the
fresh score-blind restart. It is exact-hashed in activation scope and outside every team profile.
The physical profile denied the authority and every tested R4, R3, and original-worktree path.
Neither the private runtime nor its sanitized environment supplies a host catalog, configuration,
history, plugin, memory, scratch path, or predecessor byte.

The deny-by-default OS profile exposes only the sanitized team kit and the selected lane, with
writes limited to that lane's `candidates/`, `outbox/`, and `work/`. Real probes denied peer reads
and writes, private-runtime reads and writes, host process visibility, and network. Teams cannot
read the frozen common reports, raw snapshot, organizer configuration, Git metadata, source
archives, result directories, journal, authority, activation, selection, or historical release.
The July 2024 through July 2026 holdout is evaluated only after research processes exit and remains
one sealed observation with no interim feedback.

## LC-04 — lifecycle, progress oracles, and broker behavior: closed

The broker lease serializes model sessions and evaluation commands; no two teams run together, and
the language-model process exits before any outbox is evaluated. Direct launch repeats activation,
completed-restart, smoke, phase, and lane-surface admission inside the shared lifecycle. A later
phase receives only its own lane and journal-bound normalized feedback. Shared pre-selection status
always projects the genesis head and fixed sealed message, so lane counts, dispositions, order,
timing, journal growth, and predecessor progress are not disclosed.

Broker recovery requires the exact immutable launch authority, reruns physical isolation, and binds
the final candidate bytes before accepting a recovered outbox. Pre-acceptance admission errors are
preserved for the organizer; only a genuinely accepted request with a durable terminal runtime
failure is normalized. Nomination gate detail is reduced to a type-only terminal retirement after
the model process has exited, preventing a repair session or score oracle.

## LC-05 — exact candidate bytes and executable-surface leakage: closed

Descriptor-relative capture rejects symlinks, FIFOs, devices, sockets, hard links, path
substitution, unexpected files, oversized aggregate data, and hidden executable payloads. The same
captured bytes become the content-addressed archive, research receipt, source review, evaluation
input, and nomination identity. Only archived `strategy.py` is executable; notes and JSON remain
non-executable evidence.

The frozen semantic AST subset still permits one direct, stateless `target_weights` method with the
exact factory shape. It rejects module/class/self state, helpers, alternate functions or classes,
decision-time branching, iterator state, while loops, bit/modulo/power packing, ordinal/character
or encoding tricks, executable docstrings, imports outside the positive allowlist, RNG/operator
substitutes, opaque or excessive literals, module binding reads, dynamic loading, and multiple
executable files. Exact archived-source append and corrupt-future invariance runs three scenarios
and must remain identical before nomination. Candidate execution failures are separated from
infrastructure failures so an OS fault cannot be mislabeled as causal evidence.

## Gate decision

**PASSED — zero unresolved leakage or clean-room findings.** The installed-skill path is removed
from model context and physically unreadable, private client state is phase-fresh, exact live
command/runtime authority is receipt-bound, predecessor and peer paths are denied by the real OS
profile, holdout/progress channels remain sealed, and exact captured candidate bytes retain the
previously approved stateless causal and future-invariance gates. No team phase or evaluation was
started during this review.
