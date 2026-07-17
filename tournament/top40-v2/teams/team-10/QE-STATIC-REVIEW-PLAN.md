# Team 10 pivot-01 QE static review plan

This checklist is prospective, not evidence.

1. Bind every executable root byte and verify the initial ledgers/A5 artifacts remain unchanged.
2. Verify every `StrategyConfig` field matches frozen config, trial parameters, family ranges,
   ablations, and each one-axis neighbor.
3. Prove exact 8h adjacency, future/corrupt append invariance, and a single 00:00 UTC decision per
   24h schedule; off-schedule calls must return hold without score capture.
4. Confirm the cohort quarantine enforces the declared one-bar, tail, drawdown, range, volatility,
   volume, dislocation, breadth, and history thresholds before scoring.
5. Confirm the exact finite final expected-return dict calls imported `strategy.score_boundary` once
   after all transforms and before spread filtering, buffered selection, sizing, caps, or central
   risk. All downstream ranking must use the identity return.
6. Verify 0.20 gross, zero net, four names per side at 0.025, two-rank retention, and hold on unchanged
   sleeves. Funding, results, equity, positions, fills, and ticker heuristics are forbidden inputs.
7. Exercise crash/gap quarantine, missing/stale histories, under-history membership, input order,
   funding invariance, malformed past data, deterministic state, and A6-only eligibility.
8. Require root no-control bytes exactly. Confirm controls are forbidden for the terminal initial
   family and cannot rescue a failed pivot core.
9. Validate the 24h A5 schedule/label, minimum 240 pairs, six folds, positive pooled Pearson, at least
   four positive fold correlations, complete coverage, and independent semantic approval.
10. Confirm all 12 neighbors were fixed before results, will all be registered before any neighbor
    result, and cannot qualify the center until complete aggregation passes.
