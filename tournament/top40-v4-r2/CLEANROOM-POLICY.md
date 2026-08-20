# Clean-room policy

Each team's `ACCESS-POLICY.json` is the complete authority enforced by a dedicated OS permission
profile: unlisted paths are unavailable. Teams may read the sanitized common kit and their own
lane. They may write only `candidates/`, `work/`, and `outbox/` in that lane.

The following categories are denied: other team workspaces, earlier tournament artifacts,
organizer-private or sealed state, repository history, legacy research/reports, command network,
native web/browser tools, plugins, apps, and subagents. External precomputed signals, fitted
objects, weights, performance tables, and strategy code are not allowed.

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
