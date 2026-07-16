# Organizer static review — Team 05 initial CRTR draft

Disposition: **NO-GO for registration or execution; mechanism concept retained for remediation.**

## Sound elements

- The family is performance-blind, deterministic, two-sided, and economically falsifiable.
- Exposure is conservative and the fixed neighborhood is one-axis and nonselectable.
- The package records causal lineage, long/bull and short/bear roles, hard development gates, and
  explicit no-control/single-control/combined risk policies.
- No material trial or performance view has been consumed.

## Blocking corrections

1. `strategy.py` and its tests treat each bar frame's index as the timestamp. The real tournament
   worker supplies canonical bar columns, including `open_time`, on a non-time index. The strategy
   must consume that schema and admit a bar only after `open_time + 8h <= decision_time`.
2. Synthetic tests must use the real column schema. Their future-append/corrupt/truncate checks
   must distinguish bar open time from close availability.
3. The runtime seed should fail closed unless it equals the registered canonical seed `20260801`.
4. The prospective organizer score diagnostic requires the exact A5 identity hook at the
   post-transform/pre-selection boundary, a first-added candidate manifest, a complete simple
   executable-open-to-open label/IC contract, and byte-level invariance tests. Registration remains
   blocked until Amendment 0005 is frozen.
5. The trial plan redundantly registers doubled-cost cells. The central evaluator already produces
   base and doubled-cost evidence for every risk policy in one material run. Collapse twelve
   risk/cost cells to six risk-policy cells.
6. Run the no-control core first. Risk controls may activate only after positive, broad core-alpha
   minima; they may not rescue a negative or one-regime mechanism. The fixed combined policy may be
   the canonical controlled candidate only after the core activation gate passes.
7. The top-level risk policy used by the initial trial must match that no-control sequence; preserve
   the combined policy as an immutable declared ablation until promotion.
8. The manually dated fold plan does not match the evaluator's six equal chronological slices.
   Bind exact evaluator-derived fold boundaries/model declarations before qualification evidence is
   recorded; do not claim retrained OOF evidence from incompatible dates.

After remediation, run lint, formatting, synthetic strategy tests, risk-contract tests, and each
policy validator serially. Do not register the family until every blocker is closed and all draft
hashes are recomputed.
