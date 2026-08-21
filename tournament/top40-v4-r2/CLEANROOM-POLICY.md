# Clean-room policy

Each team's `ACCESS-POLICY.json` is the complete authority enforced by a dedicated OS permission
profile: unlisted paths are unavailable. Teams may read the sanitized common kit and their own
lane. They may write only `candidates/`, `work/`, and `outbox/` in that lane.

The effective phase probe must create, verify, and remove a file inside the lane's `work/` root
while still denying a write to every peer lane. Model execution selects the named permission
profile as its sole filesystem authority. It must not pass a legacy `--sandbox` setting, because
that setting supersedes rather than composes with permission profiles. The profile's more-specific
child grants keep the rest of the lane read-only while making the three declared write roots usable.
Because Codex `--ignore-user-config` rebuilds the exec-layer configuration, it must precede every
`-c` security override and every disabled-capability flag in the frozen model command.

Model execution uses a distinct organizer-private `HOME`, `CODEX_HOME`, and `TMPDIR` for each team,
outside every team profile. Each home is phase-fresh and retains only authentication plus the empty
system-skill marker. Bounded client databases, logs, queues, shell snapshots, wrappers, and sandbox
scratch are accepted only long enough to validate and remove them after each Codex subprocess;
none can reach a later phase. Unknown configuration, history, memory, plugin, skill, `.agents`, or
scratch residue is rejected before any removal, and every admitted node is owner-only. Before every
model launch, the known Codex installation marker's explicit `0644` mode is narrowed through a
no-follow descriptor to `0600`, then the complete surface is validated before cleanup. Cleanup is
crash-idempotent: a strict subset of the exact wrapper or sandbox-lock surface is recognized only
as a resumable deletion prefix; unexpected names, types, owners, modes, or link targets still fail
closed. The organizer renders the exact
model-visible prompt with the pinned CLI and rejects any skill instructions, `SKILL.md` locator, or
host skill/plugin root. Physical probes separately deny the original host roots, the team's private
auth file, and both reading and writing a peer team's private runtime. The frozen model, prompt,
post-reset argv, sanitized environment, per-team temp path, runtime identity, marker, profile, CLI,
and disabled features are bound into the launch authority and every candidate receipt. The sole
live launcher derives these values internally and accepts no caller-supplied prompt or model.

The following categories are denied: other team workspaces, earlier tournament artifacts,
organizer-private or sealed state, repository history, legacy research/reports, command network,
native web/browser tools, plugins, apps, and subagents. External precomputed signals, fitted
objects, weights, performance tables, and strategy code are not allowed.

This clean worktree is score-blind with respect to its privately preserved predecessor. The
frozen `FRESH-RESTART-AUTHORITY.json` records the private predecessor incidents and that no
candidate, feedback, result, receipt, or research provenance is reused. It is organizer-only and outside every team
profile. A launch requires either
the exact completed v7 incident archive or this exact clean-restart authority; a stale v7 launch,
missing authority, unsafe file, or changed hash fails closed.

For the clean-restart alternative, activation also proves the physical genesis state rather than
trusting the authority's assertion alone. It requires a byte-empty journal, exact 15-lane seed
trees, exact frozen common reports, no research sessions or result/selection/release residue, and
only regular single-link files. The same score-blind seed digest must survive the activation tests
and is then frozen into the activation record. This is a one-time bootstrap invariant; runtime
validation binds the receipt but does not expose or require post-start journal state.
The journal bootstrap exclusively creates a private empty file, or stably verifies an already
empty owner-regular single-link file after an interrupted creation. It never invokes runtime tail
recovery before the genesis gate, so corrupt or linked preactivation bytes are rejected unchanged.
After activation, every recovery read and append pins the journal parent and existing file through
no-follow descriptors, requires exact owner/mode/single-link topology, and repeats lexical inode
checks while locked. R2 appends never recreate a missing journal; only an unterminated tail on the
same verified live authority can be truncated after its complete prefix replays successfully.
An interrupted pre-freeze test output is bounded non-authoritative scratch and is always replaced
by a complete test rerun. Volatile result/broker lock files are excluded from the digest and are
accepted only with their exact safe owner/topology and current canonical lock marker.

Every candidate carries `cleanroom-attestation.json` with exactly these affirmative facts:

- the lane access policy was followed;
- no other-team or legacy tournament artifact was accessed;
- no sealed data were accessed; and
- no timestamp-to-target table is embedded.

The organizer checks the attestation, file types, hard links, symlinks, prohibited artifact
markers, and exact descriptor identity during source capture. Only Python files from that
content-addressed archive are mounted for official execution; notes and configuration remain
non-executable evidence. The worker masks the repository, network, process creation, credentials,
and host writes. Its reconstructed process environment contains the exact frozen worktree `src`
path only for initial organizer-module resolution; before candidate import, the repository is
masked, `sys.path` is rebuilt around the staged runtime, and Landlock confines reads to the staged
candidate/runtime plus Python's non-repository base runtime. A real namespaced startup regression
binds this bootstrap. A false attestation is an integrity violation and cannot be repaired after a
result.

Mounted Python is not general-purpose: the exact archive must pass the organizer's narrow,
stateless causal AST subset. It rejects self/counter state, decision-time ordinal branching,
while loops, bit/modulo/power packing, literal indexing, ordinal/character conversion, executable
docstrings, opaque numerics, and aggregate executable/literal surfaces above the frozen bounds.
This review is bound to the source hash and is followed by exact-source append/corrupt-future
invariance before a nomination can become eligible.

Each language-model process exits before the organizer evaluates its outbox. A later fresh process
receives only lane-local normalized feedback. Organizer commands silently queue, lane validation
never scans peers, and shared status exposes no counts, dispositions, journal growth, timing, or
ordering.

Before opening score data or appending the first accepted record for a batch, the organizer captures
and validates the entire batch against exact receipts, metadata/attestations, the static source
subset, and a simulated mechanism history. Before receipts exist, the launcher applies the same
checks, records the initial finding, and may issue at most three immutable score-blind repair
sessions. A private, canonical issue receipt is durably written before every model process, so a
host crash can consume but can never duplicate a session. Each post-session report contains only
deterministic findings and explicitly binds that no score data was opened; every repair runs under
the same offline profile, fixed prompt/command, cleaned private runtime, launch authority, and
global serial lease. A durable private attempt is the source of truth for recreating or validating
the exact lane-visible repair feedback before another session is issued. Deterministic batch
defects—or a batch that remains absent—after all repairs retire the lane at that score-blind
boundary without fabricating an outbox. Before selection, the organizer revalidates each terminal
batch's journal-bound archive or exhausted-attempt evidence. This includes a
deterministic immutable receipt schema, phase, hash, or
binding conflict. Filesystem I/O, isolation-probe, lock, or other infrastructure failures before
session issuance do not retire the lane and remain safely resumable. After issuance, an ambiguous
process/host failure conservatively consumes only that already-authorized slot. The journal binds
the exact ordered preflight,
source hashes, and private canonical receipt hashes,
and only the live canonical serial-broker consume frame receives the capability to reject or admit
that batch; direct library and organizer CLI trial calls are fail-closed before mutation.

One blocking process-wide broker lease encloses every model session and evaluation command. The
pre-activation bootstrap runs under the distinct result lock so its committed-scope test child can
acquire the broker lease; no model or evaluation is authorized before that bootstrap atomically
freezes. The organizer records a deterministic launch authority before a model starts; after a
crash, the broker can validate that authority, rerun the physical isolation probes, bind final candidate
bytes, and resume without repeating accepted trials. Feedback, outbox archives, certificates, and
terminal decisions are immutable/idempotent. A rejected nomination gate retires the completed
lane without exposing details to another team.

Every result-bearing command performs a read-only activation precheck before acquiring the broker
lease, then repeats activation validation inside its result lock. This fixed lock order makes an
in-progress bootstrap fail-fast rather than allowing a broker-lease/result-lock inversion.
