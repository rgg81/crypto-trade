# Top-40 V4-R2 fourth-restart leakage and clean-room review

Review date: 2026-08-21
Reviewer: independent leakage/clean-room adversarial agent
Implementation commit: `9d95e7c69706744c357c0b10bd20472a38942862`
Branch: `quant-portfolio-blind-top40-v4-r1-v2-restart4`
Gate status: **PASSED**
Unresolved findings: **0**

## Scope and method

This review inspected the exact R6 fresh-successor bytes and physical preactivation surface. It
covered the R5 worker-bootstrap incident and non-reuse authority, the worker's temporary frozen
source bootstrap before repository masking, namespace/Landlock/seccomp/audit isolation, launcher
v10 and its private Codex runtime, the frozen model smoke, cross-team and predecessor denial,
phase-state cleanup (including SQLite companions), lane-marker recovery, lifecycle-journal
substitution resistance, progress/holdout boundaries, source capture, and the previously approved
compact causal source gate. It did not activate R6, launch a competitive model phase, evaluate a
candidate, or inspect predecessor score/summary contents.

Release evidence supplied with the exact target was **135 passed** for the R2 suite and **24
passed** for the intended R1 suite. I independently reran 18 focused current-byte regressions for
the namespaced worker, sanitized source bootstrap, Python-only executable mount, marker recovery,
private-runtime cleanup, frozen smoke/authority, preactivation journal immutability, runtime
hardlink/path-substitution rejection, and missing-journal non-recreation; all 18 passed. Ruff over
the security/runtime scope and `git diff --check` passed.

The exact fresh authority SHA-256 is
`f71896a9cd2da6071441bd65f5eeb42f2c2b0c953de016998019d082bc234e68`.
The frozen v10 smoke SHA-256 is
`596bdbe528f3648f250c471feb591b40af2d3c84d195015d8b3a775e6786a6f8`, with canonical
self-hash `55d83cfa8c277a07b9f31db4341ba641f788139e91cba1fc16e2576929390660`.
Both exact semantic validators passed, and `_implementation_commit` returned the reviewed commit.

## LC-01 — worker bootstrap and pre-mask exposure: closed

The trusted parent constructs, rather than inherits, the worker environment. `PYTHONPATH` contains
only this frozen checkout's `src` long enough for Python to resolve
`crypto_trade.tournament._strategy_worker_v4`; `HOME` and XDG paths are `/nonexistent`, user site
loading is disabled, credentials/proxies/loader controls are absent, and the candidate bundle is
neither the child working directory nor an initial import path. The active venv has only the
standard virtualenv hook and the editable source path; no `sitecustomize.py`, `usercustomize.py`,
or candidate-controlled `.pth` startup hook exists.

Before candidate import, the worker creates user/mount/network/PID namespaces, mounts the frozen
repository and staged runtime read-only, masks the entire common repository parent, removes every
repository/bundle-parent/site-packages entry from `sys.path`, remaps loaded dependency paths to the
staged read-only runtime, changes into the copied bundle, applies resource limits, and installs
Landlock, seccomp, and the audit hook. Only then does it execute archived `strategy.py`. The
candidate therefore has no pre-mask execution opportunity and no post-mask path to R6, R5, any
other worktree, Git metadata, organizer data, `/proc` host state, or the network. The real
namespaced-worker regression started successfully and confirmed the Python-only executable mount.

## LC-02 — R5 incident authority and zero reuse: closed

The canonical schema-3 `FRESH-RESTART-AUTHORITY.json` exactly binds the stopped R5 worker incident:
16 journal records, eight accepted/failed discovery trials, zero successful trials, disclosed
Team-01 discovery feedback, no holdout-row disclosure, no result artifact, no nomination, and an
interrupted refinement with no outbox. It separately binds all listed candidate/source/receipt
identities and the declared 75-file incident surface. Most importantly,
`research_provenance_reused` and `results_reused` are both false.

The R6 physical lane surface is trial-zero: all 15 lanes contain only their committed team kit and
the three one-byte-LF `.keep` markers; there are no candidate implementations, outboxes, feedback,
research-session receipts, source archives, results, nominations, certificates, selection, or
activation freeze. No private model runtime exists and the lifecycle journal is absent before the
canonical bootstrap. The predecessor identities retained in the organizer-only authority are
evidence, not input to any lane or evaluator. The profile and repository mask deny both predecessor
worktrees and the authority itself.

The authorized raw market archive is data authority, not team research provenance. It contains
94,816 regular single-link files and no symlinks; it was admitted only after manifest size/hash
validation. The full raw replay reproduced manifest SHA-256
`c21fdcefc39961cd4408277e6cbb4833c31178cf86fa5d166499a3df6a8e7af7` and the exclusive
hard end `2026-08-01T00:00:00Z`, preserving the complete July 2026 holdout without importing any
predecessor result or feedback.

## LC-03 — launcher v10, installed skills, and private state: closed

There is one live model launcher; callers cannot supply an alternate model or prompt. Its exact
authority binds Codex CLI `0.148.0`, `gpt-5.6-sol`, high reasoning effort, command ordering,
sanitized environment, custom no-network permission profile, disabled web/browser/plugin/app/skill
and multi-agent features, team kit, phase, per-team runtime, and empty system-skill marker.
`--ignore-user-config` precedes every security override and disabled flag, with no legacy sandbox
flag. Launch and candidate receipts bind those identities to the exact captured candidate bytes.

Each team has a distinct organizer-private `HOME`, `CODEX_HOME`, and `TMPDIR`. The model profile
cannot read its authentication, another team's private runtime, host skill/plugin roots, organizer
files, predecessors, peers, holdout, or process state; writes are restricted to its own lane and
network is denied. The frozen organizer-observed v10 smoke binds custom permissions, the empty
catalog, denied host skills/private auth/peer-private access, isolated TMPDIR, exact sentinel and
reply, verified cleanup, zero durable lane delta, and removal of the disposable private runtime.
The previously executed physical profile evidence passed all 11 controls; this review did not
recreate a private runtime merely to repeat a frozen preactivation mutation.

Cleanup exact-enumerates and validates owner, mode, type, link count, link target, per-node and
aggregate bounds before deleting admitted volatile state. The v10 allowlist includes all named
database companions (`-wal` and `-shm`) for goals, logs, memories, queue, and state. Cleanup runs
before prompt admission and in subprocess/phase `finally` paths, and restart-idempotent partial
wrapper/TMP states remain narrowly validated. Unknown names or unsafe topology reject unchanged.
Only authentication and the empty skill marker may persist between phases.

## LC-04 — marker, journal, concurrency, and progress boundaries: closed

The shared broker lease keeps teams strictly serial and the model exits before evaluation. Direct
and broker launch paths repeat activation, recovery, smoke, phase, and lane admission under the
same lifecycle authority. Marker recovery is limited to an absent `outbox/.keep` or `work/.keep`:
it pins the parent with `O_NOFOLLOW`, creates exact LF bytes descriptor-relatively, fsyncs, and
revalidates owner, regular type, single link, mode, inode, size, time, and lexical parent identity.
All existing markers are validated before any missing marker is created, so a conflicting marker
causes no partial normalization.

The preactivation journal bootstrap either creates the one exact private empty journal or verifies
an already empty owner-regular-single-link file; status, validate, and `run_team` never invoke tail
recovery before activation. After activation, reads and appends pin both parent and existing journal
with no-follow descriptors, require exact owner/mode/single-link topology, validate lexical inode
identity while locked, and revalidate around recovery/append. R2 never recreates a missing live
journal. Hardlink and path-substitution regressions reject without mutating the substituted lexical
file.

Shared pre-selection status projects the fixed genesis head and sealed state, not trial counts,
dispositions, order, timing, journal growth, or predecessor progress. A team sees only its own
journal-bound normalized phase feedback. All research processes exit before the single silent
July-2026-inclusive holdout observation, and no interim historical feedback is released.

## LC-05 — exact source and executable-surface leakage: closed

Descriptor-relative capture and archive validation reject symlinks, hard links, FIFOs/devices,
path substitution, hidden executables, unexpected files, and excessive aggregate data. The exact
captured bytes are the source archive, review subject, worker staging input, evaluation input, and
nomination identity. Only `strategy.py` is executable.

The sole module-level class/factory shape remains restricted to one stateless `target_weights`
method with the exact signature. The positive semantic AST subset rejects imports and calls outside
its allowlists, alternate functions/classes, module or candidate-class state, `self` state,
decision-time branches, iterators, while/bit/modulo/power/packing tricks, ordinal/character and
encoding channels, executable docstrings, opaque/high-capacity literals, RNG/operator substitutes,
and dynamic loading. Exact archived-source append and corrupt-future invariance is bound across all
three scenarios before nomination. Candidate failures remain distinct from infrastructure faults.

## Gate decision

**PASSED — zero unresolved leakage or clean-room findings.** The worker has no candidate-controlled
pre-mask execution surface, the R5 incident contributes no research provenance/result/feedback to
R6, launcher v10 and private client state are exact and phase-fresh, predecessor/peer/network/
holdout/progress channels remain sealed, marker and journal recovery fail closed under substitution,
and exact captured source retains the stateless causal and future-invariance gates. No activation,
competitive team phase, candidate evaluation, or predecessor score inspection occurred during this
review.
