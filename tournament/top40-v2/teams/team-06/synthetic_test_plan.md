# Team 06 pivot synthetic and organizer integration plan

`test_strategy.py` uses invented prices only. It covers exact past-close availability, future and
forbidden-field invariance, pure point-in-time membership, common-return-path invariance,
relative-rank acceleration polarity, deterministic broad zero-net construction, the 48-hour
schedule, fail-closed behavior, frozen identity, and direct A5 boundary placement. The pivot author
did not execute it.

The organizer must additionally run these cases serially:

1. **Next-open execution:** a scheduled target change must fill only at the next executable open,
   never at the decision close or any price read by the strategy.
2. **Pure-crypto point-in-time membership:** membership changes must use the Amendment 0006
   certified native-crypto universe; stablecoins, TradFi/equities, metals/commodities, and indexes
   must never enter the context.
3. **48-hour schedule:** epoch-aligned decisions divisible by six 8-hour bars construct; the five
   intervening aligned decisions hold; malformed or off-grid decisions fail flat.
4. **Exact history:** a missing or duplicate required close removes only that coin; fewer than 24
   complete coins produces a scheduled empty capture and flat target.
5. **Common-factor invariance:** multiply every coin by the same arbitrary positive price path and
   require byte-identical captured ranks and targets.
6. **Base versus doubled costs:** emit 1x and 2x fee/slippage views from the same material run and
   require identical pre-price-adjustment targets and fills; no duplicate trial exists.
7. **Long/short attribution:** reconcile combined PnL to central long sleeve, short sleeve,
   funding, fees, and slippage in bull, bear, chop, and stress cells.
8. **Disabled risk policy:** verify no volatility scaling, drawdown brake, turnover cap, position
   stop, time stop, or side scale changes the no-control reference.
9. **A5 boundary and clean replay:** at every manifest-scheduled decision, capture exactly one
   final finite built-in score dictionary—or one empty dictionary on valid scheduled failure—after
   transforms and before selection, sizing, caps, or risk. Returned values must drive construction,
   and two clean workers must reproduce byte-identical score and target artifacts.
10. **Frozen folds and label:** use only A5 F1–F6, the epoch-anchored 48-hour schedule, executable
    opens at `t` and `t+48h`, and frozen endpoint purge. Reproduce pooled and per-fold Pearson,
    pair counts, unavailable-label counts, and scheduled coverage without fitting or imputation.
11. **Registration identity:** the new family must precede final source fingerprinting; all three
    new A5 controls must be immutable ancestors of the exact trial opt-in; the historical parent
    A5 files and ledgers must remain unchanged.

Any discrepancy is a contract failure, not a tuning or control opportunity.
