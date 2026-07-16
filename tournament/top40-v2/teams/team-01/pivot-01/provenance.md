# Provenance: `rctc-pivot-ref-001`

## Boundary

This package is a Team 01-only implementation of the bounded pivot authorized in
`../post_result_review_rdf_core_h14_k3_g05_r1.md`. The stopped parent's source, registration,
lineage, frozen configuration, policy, tests, and Team 01 post-result review were used only to
preserve unchanged terms and make the single state branch explicit. Public V2 policy and the
shared tournament command definitions were consulted for lifecycle shape. No private qualifier,
final OOS, evaluator output, or new performance result informed the implementation.

The completed parent candidate remains historical evidence. Its family, ledger records, hashes,
and post-result files were not edited. No other-team evidence informed any mechanism, threshold,
test, gate, or trial allocation in this package.

## Frozen lineage decision

The pivot keeps H14/K3/gamma0.5, funding lambda `0.35`, `q=0.25`, 24-symbol/six-per-side minima,
gross `0.80`, cap `0.09`, direction scale `0.20`, tilt delta `0.075`, the no-control policy, and
runtime seed `20260801`. The only economic branch is:

- bull/chop: path-efficient standardized BTC-residual continuation;
- bear: path-efficient standardized raw asset trend, with raw sample volatility for sizing.

Both state and tilt use the exact BTC 60-day log return ending at `t-1d`, with inclusive thresholds
`+0.10` and `-0.10`. Missing exact state anchors now request flat; no neutral warm-up fallback is
allowed. Every asset continues to require valid 30-day paired BTC beta coverage so state branches
do not silently change the eligible cross-section.

## Unexecuted evidence

The strategy and synthetic tests were edited but not imported or executed during package creation.
No strategy hash, source-bundle hash, exact synthetic target hash, pass count, duration, process
count, registration timestamp, family ledger record, trial ledger record, or canonical result is
claimed. All such fields are `null` or begin with `PENDING_` in the corresponding artifacts.

`../risk_policy.json` was intentionally left unchanged. Its previously recorded SHA-256 is useful
historical context but must be recomputed by the organizer before trial registration.

## Organizer handoff

The ordered, serialized commands are in `commands.json`. They are instructions only and have not
been run. Before lifecycle mutation, the organizer must:

1. inspect all Team 01-local diffs;
2. run the test command twice and record exact evidence;
3. replace the pending family timestamp and all trial-registration hash/timestamp placeholders;
4. run `pivot-team` before `register-trial`;
5. verify the registered input bytes equal the reviewed templates;
6. execute only the single no-control development reference, then apply the frozen falsifier.

Neighborhood, component, and risk commands are deliberately absent because the reference has not
passed its causal and role gates.
