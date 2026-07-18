# Top40-v3 Phase 0 policy

Phase 0 must complete before any result-bearing lab run.

The organizer freezes and records SHA-256 hashes for the V3 charter, configuration, playbook,
team mandates, templates, layout, contract, lab and qualification modules, runner, worker,
evidence and finals boundaries, dependency lock, shared data manifest, every shared evaluator
module imported by V3, and the organizer-owned sandbox-canary source.

Mutable team candidate lanes are deliberately not global Phase-0 infrastructure. Team strategies,
candidate configs, risk policies, challenger directories, and their local tests may iterate during
the train laboratory. Every selected candidate tree is instead hashed before its accepted request,
journaled before execution, checked again after execution, and bound to its immutable run output.
The Phase-0 targeted suite still executes all ten team tests and the disclosed incumbent tests.
Every accepted request also binds a durable content-addressed candidate source archive. Candidate
archives are run evidence under `reports-top40-v3/`, not mutable team-lane state and not global
Phase-0 infrastructure; the archive implementation and its contract tests are Phase-0 frozen.

The first explicit Phase-0 target is a real synthetic sandbox canary. It uses the production V3
worker launch path and its actual Linux user, mount, network, and PID namespaces; mount helper;
read-only staged repository-local venv; Landlock ruleset; seccomp filter; and JSON-lines protocol.
The trusted parent supplies one synthetic BTC perpetual membership row, one closed bar, and one
strictly past funding settlement, then requires an exact deterministic target and clean shutdown.
It never opens the market snapshot, calls an evaluator, publishes a result, or consumes team lab
or journal budget. Missing kernel protections, a failed namespace or mount, or an external venv is
a hard Phase-0 failure, never a skip or an unsandboxed fallback.

The Phase 0 record must also bind the exact manifest, membership, contract-metadata,
exchange-information, pure-crypto policy, audit-module, audit-dependency, and deterministic audit
report hashes described in `PURE-CRYPTO-POLICY.md`.

Before freeze, the organizer must prove with targeted tests that:

- V3 paths cannot resolve into V2 state or reports;
- the real V3 sandbox completes its organizer-owned synthetic init/decision/shutdown canary;
- labs can access only their authorized development slice;
- validation-probe and formal-submission budgets are enforced;
- negative training or validation checkpoints cannot be locked;
- only core-eligible nominees can enter public qualification ranking;
- private and final-OOS data remain inaccessible to teams;
- base and doubled-cost executions are deterministic; and
- the pure-crypto audit fails closed on stablecoin and non-crypto exposure.

After freeze, a frozen infrastructure, evaluator, metric, schedule, seed, rubric, or policy change
requires a new prospective V3 amendment and fresh integration freeze. Team candidate changes are
new hash-bound material trials under the existing infrastructure authority; they do not mutate
the frozen bytes in place.
