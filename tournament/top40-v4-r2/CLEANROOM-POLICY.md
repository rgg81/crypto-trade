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

Model execution uses a distinct organizer-private `HOME` and `CODEX_HOME` for each team, outside
every team profile. Each
home contains authentication plus an exact version marker whose system-skill directory is empty;
it contains no user, system, plugin, or external skill and no prior session/history. Before every
model launch, the organizer renders the exact model-visible prompt with the frozen CLI and rejects
any skill instructions, `SKILL.md` locator, or host skill/plugin root. Physical probes separately
deny the original host skill/plugin roots and that team's private auth file. The team-specific
private-runtime identity,
marker hash, profile, CLI version, and disabled features are bound into launch and candidate
receipts. A model launch fails closed if the catalog is installed, changed, or nonempty.

The following categories are denied: other team workspaces, earlier tournament artifacts,
organizer-private or sealed state, repository history, legacy research/reports, command network,
native web/browser tools, plugins, apps, and subagents. External precomputed signals, fitted
objects, weights, performance tables, and strategy code are not allowed.

This clean worktree is score-blind with respect to its privately preserved predecessor. The
frozen `FRESH-RESTART-AUTHORITY.json` records the private predecessor incidents and that no
candidate, feedback, result, or receipt is reused. It is organizer-only and outside every team
profile. A launch requires either
the exact completed v7 incident archive or this exact clean-restart authority; a stale v7 launch,
missing authority, unsafe file, or changed hash fails closed.

For the clean-restart alternative, activation also proves the physical genesis state rather than
trusting the authority's assertion alone. It requires a byte-empty journal, exact 15-lane seed
trees, exact frozen common reports, no research sessions or result/selection/release residue, and
only regular single-link files. The same score-blind seed digest must survive the activation tests
and is then frozen into the activation record. This is a one-time bootstrap invariant; runtime
validation binds the receipt but does not expose or require post-start journal state.
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
and host writes. A false attestation is an integrity violation and cannot be repaired after a
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
