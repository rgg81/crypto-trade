# Team 06 synthetic and organizer integration test plan

`test_strategy.py` contains invented-data unit tests for canonical RangeIndex `open_time` bars,
`open_time + 8h` future truncation, deterministic construction, membership, two-sided exposure,
the direct public score boundary and candidate-byte invariance, and separation from open, funding,
cost, and auxiliary fields. It is authored but has not been executed in this handoff.

The following cases require the neutral organizer evaluator and must be run by the organizer, not
implemented inside Team 06:

1. **Next-open execution:** a 00:00 decision changes the target; prove no fill occurs at the
   decision close and every strategy/risk fill is priced from the next executable open.
2. **Point-in-time membership:** remove an owned symbol and add a new member at a weekly boundary;
   prove the common exit occurs and the strategy never receives an ineligible next-open price.
3. **Funding order/sign/timestamp:** carry equal long/short positions across positive and negative
   funding timestamps; prove funding is charged to carried quantities before mark/risk/rebalance
   using the authoritative sign convention.
4. **Base versus doubled costs:** emit 1x and 2x fee/slippage views from each one material run;
   prove targets/fills before price adjustment are identical and no duplicate trial exists.
5. **Long/short attribution:** reconcile combined PnL exactly to central long sleeve, short sleeve,
   funding, fees, and slippage ledgers in bull/bear/chop/stress cells.
6. **Risk action order and capacity:** simultaneously trigger funding, mark, volatility scale,
   drawdown brake, strategy rebalance, and participation pressure; prove the frozen seven-step
   ordering and shared capacity.
7. **Same-boundary reentry:** trigger a central stop/cooldown fixture even though stops are disabled
   in the final Team 06 policy; with `same_boundary_reentry=false`, prove a strategy request cannot
   reopen the symbol at that boundary.
8. **A5 capture and clean-process reproducibility:** prove `strategy.score_boundary` is called once
   post-transform/pre-selection on finite built-in scores, returned values drive construction, and
   all frozen candidate bytes are identical before/after capture; then require two clean workers
   to emit identical target, fill, evidence, and artifact hashes.
9. **Fold stitching:** organizer-derive six equal chronological slices, prove lengths differ by at
   most one with no overlap/gap, score each observation once, and reproduce the stitched artifact.
10. **Neighbor identity:** after combined full-gate pass only, prove each neighbor artifact is
    byte-distinct, changes exactly one declared axis, uses combined policy, and has its own hash.

Any discrepancy is a failed contract test, not a tuning opportunity.
