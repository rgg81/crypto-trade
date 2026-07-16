# Top-40 V2 Amendment 0007 — frozen-worker A5 protocol preload

Status: **IMPLEMENTATION DRAFT — INDEPENDENT REVIEW, FREEZE, AND INTEGRATION REQUIRED**

## Incident and scope

An ordinary `run-window development` reached the exact frozen strategy worker but failed while
loading an A5-opted-in candidate with:

```text
ModuleNotFoundError: crypto_trade.tournament.score_adapter_protocol_v5
```

The strategy worker starts from the repository's editable package, then bind-stages the virtual
environment, masks the complete repository parent, and removes repository paths from `sys.path`.
The frozen worker imports the core decision protocol before that mask, but it does not import the
later A5 score-adapter protocol. Candidate loading occurs after the mask, so the reviewed public A5
module is neither readable nor already present in `sys.modules`. The A5 score-diagnostic worker
does not have this defect because its organizer-owned generic adapter imports the same protocol
before applying the frozen mask and sandbox.

Amendment 0007 repairs only this runtime availability boundary. It changes no candidate, score,
target, evaluator, cost, risk, snapshot, universe, qualification, budget, journal, or result rule.
It does not edit the Phase-0 runner or worker and does not authorize a retry of any failed trial.

## Superset dispatch

The non-active candidate entrypoint is
`scripts/top40_v2_tournament_runtime_preload_v7.py`. Every argument vector delegates through the
exact active Amendment 0005 integration dispatcher using the same immutable list snapshot that it
used for scope classification. A7 never calls Amendment 0006 or Amendment
0004 directly. Consequently:

- A5 status, reservation, and declared-score diagnostic commands retain their private capability,
  integration guard, registration boundary, and exact implementation.
- Every other command still traverses A5's exact A6 delegate.
- A6 still verifies the exact pure-crypto report before and after delegation.
- A4 remains the sole compatibility authority for `run-window development`; private/finalist
  execution remains unavailable.

For a canonical four-token `run-window development TEAM_ID CANDIDATE_ID` argument vector naming
Team04 through Team10 and a bounded canonical candidate identifier, A7
temporarily replaces only the in-memory `runner_v2._strategy_worker_command` binding. Malformed
development argv and Teams01–03 delegate unchanged. The replacement first invokes the captured
exact frozen command builder, requires the root entrypoint to be exactly `strategy.py`, requires
exactly one launch on success, and requires one unambiguous
`-m crypto_trade.tournament._strategy_worker_v2` operand, and replaces only that operand with
`crypto_trade.tournament._strategy_worker_preload_v7`. Every namespace flag, executable, path,
environment, protocol, timeout, and resource setting remains the frozen builder's output.

The patch is held under A4's captured shared reentrant patch lock. A7 rejects a preexisting patch,
checks its installed identity, delegates through captured A5 `run`, observes the binding, and
restores the exact original in an unconditional `finally` path after success, ordinary exception,
`KeyboardInterrupt`, or `SystemExit`. A delegate that changes the binding is terminal even though
the original is restored. Restoration and post-authority failures take precedence and are chained
from the delegated failure. Non-development commands never receive the patch.

The public dispatcher also requires the private identity held by its reviewed `main` path. Before
and after every delegation it validates the future implementation review, amendment freeze,
integration draft, integration review, and integration freeze as canonical, uniquely first-added
files in strict commit order. The active freeze must bind the exact current entrypoint, dispatcher,
worker wrapper, delegated A5 integration, historical A5 entrypoint, and a prospective organizer
journal count/head whose prefix extends A5's activation. Until that complete chain exists, the
candidate entrypoint fails closed and cannot install the worker-command patch.

The guard also invokes A5's exact active-integration loader, requires its uniquely first-added
integration-freeze commit and bytes to equal the delegated A5 authority, and requires that commit
to strictly precede A7's implementation. It verifies the live A7 module path and captured
dispatcher, guard, authorization, delegate, lock, command-builder, replacement class, and command
constants before and after every operation. The implementation and integration reviewer
identifiers must be distinct.

## Worker preload boundary

`_strategy_worker_preload_v7` imports the exact frozen A5 protocol and exact Phase-0 worker before
calling the worker's captured `main()`. Before the repository mask it verifies exact paths,
single-link regular-file sizes and hashes, protocol constants, module-registry identities, the
public hook identity, and frozen worker-main identity. It then delegates all parsing, mount setup,
path remapping, resource limits, Landlock, seccomp, audit policy, strategy loading, incremental
history, decisions, and wire protocol to the unchanged worker.

The preload adds no path to `sys.path`, copies no organizer file into the candidate bundle, opens no
post-mask filesystem allowance, passes no additional data, and does not replace the identity hook.
The already-loaded module satisfies the candidate's reviewed direct import without filesystem
access. Module and callable identities are rechecked when the frozen worker returns. An intentional
candidate mutation therefore makes the child exit uncleanly before parent evaluation.

These exact immutable parents are required:

| Authority | Bytes | SHA-256 |
| --- | ---: | --- |
| Phase-0 `runner_v2.py` | 86,317 | `d4fc1c381f9e69c0dbdd5b7c6e5d273e43b39c5df16a082a99af1b4ef7310ec2` |
| Phase-0 `_strategy_worker_v2.py` | 46,620 | `fff67076592e337adb721b72c4c77326c3e40e396ba57217c387a8b5f58f2b5d` |
| Phase-0 freeze | 5,301 | `cc7484d0be2fe6b64b34b6f4c7ce76647af750b02c3df065c4b81e10f1396259` |
| Amendment integrity helpers | 34,451 | `e3a4f60aa955ebcf461026527da5b6b28b87e9e7ec057dd2e10a1e884612a8ab` |
| A2 shared-patch module | 10,828 | `fc70dbdb752c58857c5ed60a96e497324e93b9d5dc7e6afa0692bd3e02ad21aa` |
| A4 runner module | 12,114 | `03006ea1ce391ef3c8da6244acb89aab19f7e63d1e0a617e2743894a575fd6cd` |
| A4 freeze | 1,865 | `bfb9e82c0b9a0950ead9b94ae61fe9f6c091462b106e46bd51113894b6eb9465` |
| A5 protocol | 1,037 | `8f8f5db3be3069cce7c7c0605fb15b31c4f28af7c2e0f2e24d79d861a65ae4ff` |
| A5 active entrypoint | 263 | `0dc9228f3b9c6fe41b2655055f766fc92f323a289a050e6bdf4e48a30b0105f4` |
| A5 integration module | 3,080 | `c9e0b0be288edebf86f8c7d441b4093843ae3d64f0cbac42dbadf21625f786f8` |
| A5 freeze | 5,477 | `0f112dc0e6452e29d691f46d42b8c19ea46482bda0b813143664acf056954c5f` |
| A5 integration freeze | 2,286 | `b3b2b96245a479ccfff95b5cd5b5cd0aef3b2d0aac0fc9faf5367d3e6772958c` |
| A6 integration freeze | 2,044 | `3e93bdfe031e2589888c3bbcaae583437bbd074fa9d86c6dc0a54187bc0f1e34` |

The delegated A6 authority continues to require the 73,777-byte pure-crypto audit report with SHA
`b9c55b40fef331861af068272159f45860870182a58c93652eff2a819b3d5d1b`, policy SHA
`2c7fb0ff593d06c323517e60df4b28ab9387a2df580b83f82f65ef71c91fc350`, and zero violations.

## Explicitly rejected repairs

- No `PYTHONPATH`, editable-install, environment, or virtual-environment mutation.
- No new readable repository or package path after masking.
- No copy of organizer protocol source into a team bundle.
- No candidate-side fallback, duplicate identity function, or import exception handler.
- No edit to the frozen worker or Phase-0 freeze.
- No use of the A5 score worker for ordinary target generation; its initialization and response
  protocol are intentionally different.

## Required validation

Validation must be serialized. It must establish:

1. the transformed command differs from the frozen command by exactly one module operand;
2. missing, duplicate, misplaced, prepatched, or delegate-mutated bindings fail closed;
3. the exact runner binding is restored after every `BaseException` path;
4. all non-development vectors, malformed development vectors, and Teams01–03 development
   vectors reach exact A5 unchanged and unpatched;
5. exact protocol bytes and identities are loaded before masking;
6. a temporary A5-importing strategy initializes and decides under the real production namespace
   and repository mask without running tournament lifecycle;
7. a non-A5 strategy returns identical weights under frozen and wrapped workers;
8. frozen filesystem, network, process, resource, Landlock, seccomp, history, and wire-protocol
   tests remain unchanged;
9. A5 declared-score capture/replay remains unchanged; and
10. the canonical A6 pure-crypto report is identical before and after delegation.

## Governance and activation

This implementation and candidate entrypoint are not active. Result-bearing commands must remain
paused until all of the following immutable first-add authorities exist in strict commit order:

1. implementation commit containing only the reviewed A7 scope;
2. independent implementation review commit;
3. amendment freeze commit binding exact implementation and review bytes;
4. integration-draft commit binding the new entrypoint and recording the A5 entrypoint as
   `superseded-unchanged`;
5. independent integration review commit; and
6. integration-freeze commit recording the current organizer-journal count and head.

The amendment freeze alone must report `frozen-pending-integration`. The A7 integration freeze is
the only activation authority for this command surface, but it creates no new candidate
eligibility boundary: A5's existing record-count 25 activation remains the declared-score
registration boundary. Still-unregistered packages must bind the eventual A7 integration freeze
before execution. The historical failed event remains immutable. Any exact-byte administrative
replacement requires separate explicit authority and cannot be inferred from this repair.
