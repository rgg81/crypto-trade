# Team07 QE and static review plan

No GO decision has been made. Before family or trial registration, an independent reviewer should:

1. verify every changed byte is inside Team07 and confirm the two organizer ledgers were not
   edited;
2. compare StrategyConfig with frozen_config.json and every material trial declaration;
3. inspect every feature timestamp and prove bars close by the boundary and funding is strictly
   earlier;
4. confirm no high/low intrabar value, current executable open, file, network, subprocess, PnL,
   position, private, or OOS datum can affect a target;
5. verify daily cadence, eligible-only finite targets, gross/net/name caps, and both sleeves;
6. run formatting/lint plus the focused strategy and risk-policy tests serially;
7. run the official clean sandbox twice and require identical target/artifact hashes;
8. validate family and trial inputs against the frozen schemas after replacing every sentinel;
9. register before any evaluator run through the active Amendment 0006 entrypoint; and
10. require canonical OOF, doubled-cost, regime, role, concentration, and neighbor evidence before
    QR acceptance.

Static review must separately verify organizer semantics: funding on carried positions, risk
decision at a known boundary, next-open reductions, ordinary costs and shared participation,
strategy gate after risk, and no same-boundary reopening. Team code does not implement those
steps.

