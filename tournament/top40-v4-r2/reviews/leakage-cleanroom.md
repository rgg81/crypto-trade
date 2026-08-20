# Top-40 V4-R2 leakage and clean-room final release re-review

Review date: 2026-08-20
Reviewer: independent leakage/clean-room adversarial agent
Gate status: **PASSED**
Unresolved findings: **0**

## Scope and executed evidence

This final-byte re-review inspected the sanitized team kit, all 15 physical lane roots, Codex
permission profile, offline broker, strategy-worker namespace, source capture/archive path,
nomination review, organizer command serialization, phase lifecycle, and disclosure-safe status
projections. It rechecked every previously reported LC-01 through LC-06 attack class.

Executed evidence on the final implementation:

- R2 contract/security suite: **55 passed**.
- R1 compatibility suite: **24 passed**.
- Ruff on the R2 clean-room, runner, orchestrator, broker, CLI, and tests: **passed**.
- `git diff --check`: **passed**.
- Organizer isolation audit: **passed**, exactly 15 lanes.
- Physical filesystem inspection found no symlink, FIFO, socket/device, or multiply-linked regular
  file under `tournament/top40-v4-r2`.
- The documented Team-01 probe was run outside the enclosing workspace sandbox against the final
  bytes. All five effective controls were true: allowed lane reads, denied organizer/prior/
  cross-lane reads, denied cross-lane writes, denied network, and hidden host processes.

## Finding closure

### LC-01 and LC-02 — local, cross-lane, prior-edition, process, and web access: closed

The effective Codex profile is deny-by-default and approval-free. It exposes only the sanitized
kit, the selected lane, and the minimal Codex runtime; disables web search, apps, plugins, and
subagents; and denies command networking. The real profile probe verifies the effective boundary,
not merely its configuration. Teams cannot read the repository, snapshot, organizer state, prior
editions, another lane, host process command lines, or public web data, and cannot write outside
their own candidate/work/outbox roots.

### LC-03 and LC-06 — hidden, encoded, or ordinal executable payloads: closed

Only the exact archived `strategy.py` is executable. Markdown, JSON, TOML, YAML, notes,
attestations, certificates, and other captured evidence never enter the worker source mount.

Every nominee must pass the frozen stateless causal AST subset on the exact captured bytes:

- exactly one `strategy.py`, bounded to 128 KiB and 2,000 AST nodes (5,000 aggregate ceiling);
- one direct method in one module-level class, exact
  `target_weights(self, context, *, seed)` signature, and no defaults, decorators, inheritance,
  helper functions/classes/modules, or alternate factory behavior;
- scalar-only module assignments and no top-level executable control flow; the target cannot read
  module bindings, candidate-class state, `self`, or `context.decision_time`;
- no persistent iterator/default state, while/named-expression/global/nonlocal/augmented mutation,
  dynamic code, file/data loaders, bytes, dunder access, `ord`/`chr`/encoding, RNG APIs,
  bit/floor/modulo/power/packing arithmetic, or literal indexing;
- calls inside the target are restricted to a positive allowlist of transparent operations;
  forbidden calls/attributes are also rejected when merely loaded, closing alias and operator/
  NumPy substitute paths;
- operational strings must come from the frozen API column/option allowlist; nonempty literal
  containers are forbidden; numerics are non-scientific, at most six significant digits,
  bounded by 10,000 (14 bits for integers), with at most 24 numeric and 64 total literal nodes;
  executable docstring access is rejected while inaccessible explanatory docstrings remain inert;
- target complexity is bounded to 160 statements.

These structural rules close self/default/module/class counters, helper and local-module aliases,
bare or attribute docstring access, literal-table indexing/iteration/`.get`, encoded strings,
opaque numeric payloads, operator substitutes, and deterministic RNG ordinal schedules.

The nomination gate then executes the same archived Python bytes in three fresh workers against
past-only, appended-future, and corrupted-future inputs. It requires exact target-frame equality,
records all three equal target SHA-256 values, and binds that evidence and the static-check list to
the accepted source-bundle SHA-256. Nomination revalidates the immutable review receipt against
that same accepted authority.

### LC-04 — capture, archive, and audit substitution races: closed

Candidate traversal pins every absolute directory component with `O_NOFOLLOW | O_DIRECTORY`,
walks child directories descriptor-relatively, and reopens the complete chain to verify device/
inode identity. File reads use `O_NOFOLLOW`, descriptor `fstat`, regular-file/single-link/size
checks, before/after identities, and a final descriptor-relative lexical stat. A second pinned
traversal must reproduce the manifest.

Admission parses metadata and clean-room attestations from those captured bytes, archives them
content-addressably, and journals the same bundle digest. Official workers materialize source from
the immutable archive, validate every staged byte and manifest entry, and mount only the Python
file. Existing regressions cover symlink, FIFO, hard-link, open-time substitution, and
intermediate-directory substitution.

### LC-05 — progress oracles, overlap, and lifecycle races: closed

Pre-selection `validate` and `status` both project the constant genesis journal head and disclose
no record count, team dispositions, peer errors, ordering, or timing. During sealed historical
evaluation they expose only the fixed selection boundary until the atomic release. Lane audits
inspect only the requested lane, team feedback is lane-local, and result-lock contention queues
without a distinct busy outcome.

After the one-time activation bootstrap, one blocking, re-entrant kernel lease encloses the broker
CLI, every non-activation tournament CLI command, every broker/model session, and every direct R2
model/evaluator orchestrator entrypoint. Its parent and lock node are opened descriptor-relatively
with no-follow, owner, regular-file, single-link, and post-lock identity checks; a second process
blocks rather than learning a busy state. The broker enforces the exact 0/8/12-trial
discovery/refinement/decision transitions, validates immutable prior feedback and
content-addressed outbox archives, rejects terminal/post-selection launches, and processes teams
serially. The language-model subprocess must exit successfully before its outbox is captured or
any evaluator runs.

Activation is the sole bootstrap exception to the broker lease because its committed-scope pytest
child must be able to acquire that lease. Activation remains enclosed by the organizer result
lock, so it cannot overlap an evaluator mutation. Before the atomic freeze exists, every direct or
brokered team launch fails activation validation before starting a model; after it exists, all
model and evaluator commands use the lease. A redundant activation cannot rerun bootstrap tests
or evaluate a candidate, and its organizer-only failure/output is outside every lane. The focused
regression verifies that the activation CLI does not hold the parent broker lease across its child
test process.

Every result-bearing orchestrator entrypoint performs a fail-fast activation validation before it
can acquire the broker lease, then repeats validation after acquiring its ordinary broker/result
locks. The canonical organizer CLI supplies no outer lease for these commands and delegates to the
same decorated entrypoints, preserving that order. Consequently a pre-activation direct or CLI
result call cannot hold broker while waiting for activation's result lock, and a scope change
between the precheck and lock acquisition still fails the authoritative in-lock validation. The
cross-process regression exercises both paths while activation's result lock is held; both return
without waiting on broker or running an evaluator.

The exported low-level launcher now validates the frozen activation itself, while holding the
same lease, before any model process or candidate receipt can be created. Refinement and decision
launches reconstruct prior feedback from the content-addressed outbox, accepted journal records,
terminal records, and hash-verified summaries; a contradictory lane-local packet cannot authorize
the next phase. Deterministic candidate execution or invalid-target failures in causal review are
typed as candidate rejections, while launch, protocol, timeout, and storage failures remain
resumable infrastructure errors. Neither path discloses peer state or creates an extra holdout
observation.

## Gate decision

**PASSED — zero unresolved leakage or clean-room findings.** The OS boundary, network denial,
single-lane filesystem authority, exact-byte capture/archive/replay chain, stateless causal source
subset, three-scenario future invariance, receipt binding, global serial lease, phase lifecycle,
and disclosure-safe projections are ready for activation.
