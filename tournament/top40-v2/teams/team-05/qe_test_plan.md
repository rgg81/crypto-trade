# QE verification plan

The two synthetic test modules are intentionally not executed during clean-room authoring. They
cover score causality, deterministic construction, conservative exposure, explicit flat/hold
semantics, membership, neighbor overrides, declarative risk scaling, stop triggers, cooldowns,
and same-boundary reentry blocking.

## Team-local synthetic checks

- Canonical RangeIndex frames with `open_time` and `close`; exact admission at
  `open_time + 8h <= decision_time`.
- Future truncation, append, and corrupt-future invariance based on close availability rather than
  bar open time.
- `open`, high/low, quote volume, funding, and auxiliary corruption invariance because those are
  explicit non-features.
- Point-in-time membership exclusion and reserved-key exclusion.
- Mapping-order and fresh-instance reproducibility; exact rejection of every seed except
  `20260801`.
- Direct A5 hook input type/finite checks, proof that construction consumes returned values, and
  byte-level candidate-score invariance.
- Finite signed weights, long and short activity, gross/net/symbol caps.
- Fail-closed behavior for sparse, stale, malformed, or zero-volatility histories.
- `None` on unscheduled boundaries versus `{}` on a scheduled invalid boundary.
- Exact one-axis neighbor construction and unknown-parameter rejection.
- Frozen risk-policy parsing, conservative scale composition, threshold stops, cooldown ordering,
  same-boundary blocking, and zero-gross drawdown action without a manufactured fill.

## Organizer integration checks required before qualification

These are evaluator responsibilities and must not be simulated inside team strategy code:

1. A target formed from a boundary close can fill no earlier than the next executable transaction
   open; no intrabar stop fill is possible.
2. Funding is charged to the carried signed position at the configured timestamps before boundary
   risk and strategy actions; verify long/short funding signs independently.
3. Point-in-time weekly membership, delisting exits, symbol/gross/net limits, and 0.1%
   participation apply centrally even when the strategy returns `None`.
4. At base and doubled costs, fees and slippage apply to strategy and risk orders identically.
5. Central attribution contains long and short sleeves in bull/bear/chop/stress and confirms the
   required long-bull, short-bear, and combined-chop roles.
6. Risk ordering is funding → carried-book mark → frozen risk decision → next-open risk reduction
   → risk gate → strategy request → common exposure/delisting controls.
7. Stopped symbols cannot reopen at the same boundary, stop/cooldown state uses authoritative
   fills, and risk orders share the participation allowance.
8. Two clean-process canonical replays produce identical target records, fills, scores, and
   artifact hashes.
9. Derive six equal chronological folds centrally before materializing any fold declaration. Each
   is a distinct past-only replay; stitched daily returns cover the visible index once.
10. Every material risk-policy and neighbor cell has a prior journal registration and consumes the
    cumulative trial/compute ledger even on failure or interruption.
11. Confirm each policy evaluation emits base and doubled costs, the no-control core precedes all
    controls, and the combined full-gate pass precedes all neighbors.
