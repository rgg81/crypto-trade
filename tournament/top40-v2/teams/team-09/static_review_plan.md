# Team09 independent static-review plan

This is a prospective checklist, not a completed review or authorization.

An independent reviewer must inspect the exact proposed source bytes before family/trial
registration and return explicit GO/NO-GO. The reviewer must not use private or OOS data and must
not substitute performance judgment for contract review.

## Required review

1. Confirm the package is confined to `tournament/top40-v2/teams/team-09`, ledgers are empty, and
   the bootstrap says `A7_A6_ACTIVE_PROSPECTIVE_UNREGISTERED`.
2. Confirm every future command is pinned to the active A7 entrypoint, that its exact delegated A5
   score surface and A6 pure-crypto bindings match `a7_execution_authority.json` and
   `a5_score_lineage.json`, and no ineligible asset classification can enter team code.
3. Match every `StrategyConfig` field and value to `frozen_config.json` and the complete trial
   template. Check every declared family range and neighbor is feasible under `validate()`.
4. Trace each feature to past-only context data. Check exact eight-hour price adjacency, latest
   close freshness, strictly past funding timestamps, bounded funding lookback, funding freshness,
   under-history exclusion, and absence of imputation or future compression.
5. Verify cross-sectional ranking and tie behavior are deterministic and input-order invariant.
   Verify the seed is exact and `build_strategy()` performs no I/O.
6. Verify both sleeves are required, have equal gross, satisfy 10% per-symbol/100% gross/25% net
   evaluator limits, and request explicit flat when breadth is insufficient.
7. Inspect funding sign economics: a positive funding row charges a carried long and benefits a
   carried short in the central evaluator. Confirm the strategy interprets high relative funding
   as a short crowd and low relative funding as a long crowd without claiming its own cashflows.
8. Check no date-to-target table, private/OOS reference, fitted opaque state, evaluator state,
   filesystem/network/subprocess path, or hidden dependency exists.
9. Enumerate the entire executable Team09 tree at the candidate source commit. Require an acyclic
   manifest that equals the complete executable dependency set; hash every file and reject
   unlisted executable helpers.
   Verify the exact score manifest, direct one-positional `strategy.score_boundary` call, capture
   boundary, same-object return, and use of the captured dict for filtering, ordering, side
   selection, and weights before caps/risk. Complete the semantic-review template only from exact
   reviewed bytes.
10. Validate all six risk-policy JSON files against the frozen organizer parser/schema. Confirm
    next-open execution, ordinary costs, capacity sharing, and same-boundary reentry are organizer
    responsibilities. Confirm each policy run produces paired base/doubled-cost panels and counts
    as one material configuration.
    Before the first registration, require root `risk_policy.json` to be byte-identical to
    `risk_policies/00-none.json`. Run that core first and require positive ordinary/doubled return
    and Sharpe, at least four positive folds, positive bull/bear/chop returns, positive
    long-bull/short-bear/combined-chop attribution, and active sleeves before any control. Controls
    cannot rescue failure. For a later policy, copy its immutable template byte-for-byte to root
    before commit, registration, and run, then recompute all bindings.
11. Review tests for future-data fail-closed behavior, exact gap handling, stale/under-history
    symbols, funding economics, input-order invariance, deterministic reruns, exposure limits,
    config/template completeness, and risk-policy validity.
12. Confirm the walk-forward and neighborhood files are prospective plans only. They are not
    qualification evidence until exact model/parameter/return hashes and central evidence exist.
    Enforce `neighbor_staging_plan.json` so all identities are frozen before any result read and no
    result hash can enter its own registration lineage.
13. Confirm the hard disposition: no qualifier freeze or submission unless every development gate
    passes; otherwise continue, pivot within budget, or DNF.
14. Replace family/trial timestamp placeholders only with actual lifecycle event times and replace
    every zero-hash sentinel before schema validation and registration.

Any material source correction after review requires a new exact-byte review. A static GO would
authorize only organizer registration through the then-active lifecycle, not an evaluator run,
qualification claim, private ticket, or OOS reveal.
