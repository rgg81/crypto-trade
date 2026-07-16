# Team 06 synthetic test plan — persistence pivot

The root `test_strategy.py` is prospective source and must be run serially by the organizer. The
author did not execute it. Its checks cover causal input handling, relative-rank persistence
polarity, deterministic broad zero-net construction, the 96-hour schedule, pure-crypto membership,
and the direct A5 score boundary.

1. **Exact history:** each scored coin needs one finite positive close at every one of 97 exact
   completed 8-hour opens. Duplicate, missing, future-only, nonpositive, malformed, or noncanonical
   histories fail that coin closed; fewer than 24 complete eligible coins fails the decision.
2. **Persistence polarity:** a path moving from negative prior rank to positive recent rank must
   have positive shift and positive raw score. A steady positive recent/prior level must still
   contribute positively with zero shift, proving the model is not merely the failed score's sign
   relabeled.
3. **96-hour schedule:** epoch-aligned decisions divisible by twelve 8-hour bars construct; the
   eleven intervening aligned bars hold; off-grid, naive, or pre-epoch timestamps fail flat.
4. **Pure-crypto point-in-time membership:** only `eligible_symbols` are scored or targeted. Extra
   bar frames never expand the organizer-certified Amendment 0006 universe.
5. **Common-factor invariance:** multiply every coin by the same arbitrary positive price path and
   require identical captured ranks and targets.
6. **Causality:** future rows, next-open fields, funding, auxiliary values, volume, and unrelated
   columns cannot change a target.
7. **Construction:** require deterministic sorted targets, at least eight names per side, exact
   zero net, no more than 0.40 gross, and no more than 0.025 absolute coin exposure.
8. **Base versus doubled costs:** the material runner must emit 1x and 2x cost views from one target
   and fill path; doubled cost is not a second candidate or trial.
9. **A5 boundary:** each scheduled construction captures exactly one finite built-in score
   dictionary—or one empty dictionary on scheduled failure—after final ranking and before
   selection, sizing, caps, or risk. Returned values must drive construction.
10. **Identity and policy:** reject the wrong seed, unknown candidate identity, or any hidden
    override. Root `risk_policy.json` must remain the exact disabled no-control policy.
11. **Frozen folds and label:** use only A5 F1–F6, the epoch-anchored 96-hour schedule, executable
    opens at `t` and `t+96h`, and frozen endpoint purge. Reproduce pooled and per-fold Pearson,
    pair counts, unavailable-label counts, and scheduled coverage without fitting or imputation.
12. **Registration identity:** the new family must precede final source fingerprinting; all three
    new A5 controls and the A7 family/candidate rebind must be immutable ancestors of the exact
    trial opt-in. Historical parent controls, results, and ledgers remain unchanged.

Any discrepancy is a contract failure, not a tuning or control opportunity.
