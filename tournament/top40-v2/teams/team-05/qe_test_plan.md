# QE verification plan

The two synthetic test modules were not executed during clean-room authoring or the active-authority
rebind. This statement does not supersede any separately recorded organizer validation. They cover
score causality, deterministic construction, conservative exposure, explicit flat/hold semantics,
membership, neighbor overrides, declarative risk scaling, stop triggers, cooldowns, and
same-boundary reentry blocking.

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
12. Verify active A7 entrypoint SHA-256
    `8a4ada10176d2606df3f358fc188e21b45153ad9a7270f36908736f03322a3a9`, A7 integration-freeze
    commit `c8b917ca49306d5200a4e08848e73ff6f5a18bf3`/SHA-256
    `6f77a146e7b414eabd20c5cc9321a95493bb98116dde07ef79d9eb009b6a6f51`, A5 integration-freeze
    commit `d2b95f610722aab65b4e67466b34efeaa3554101`/SHA-256
    `b3b2b96245a479ccfff95b5cd5b5cd0aef3b2d0aac0fc9faf5367d3e6772958c`, and the delegated A6
    integration/report authority before any result-bearing command. Require A8 freeze commit
    `f6003ae687d5a6bf665abb001715b01ea8b10abb`/SHA-256
    `08bf194c9ade1f66bf38012210ad8604df61ca467cdad00bd3957aa679ea9bdd` for infra-r1.
13. Recompute the complete executable set from the final Team05 historical tree. Require the
    executable-source commit to precede the independent semantic-review commit, then the score
    manifest commit, then the infra-r1 registration commit; require exact executable bytes at all
    three downstream boundaries.
    The prospective root set is `candidate_variant.py`, `frozen_config.json`, `risk_policy.json`,
    `strategy.py`, `test_risk_policy_contract.py`, and `test_strategy.py`.
14. Validate the materialized score manifest against the active A5 schema: exact 72-hour schedule
    from `2020-01-01T00:00:00Z`, exact 72-hour executable-open label, fold-end purge, 12 minimum
    pairs, and globally pooled Pearson. Confirm the diagnostic is non-material, does not charge a
    team trial, and is not an automatic gate.
15. At the supplied eligibility boundary and every archived replay boundary, require the exact A6
    certified universe and zero non-crypto leaks. Stablecoins, equities/TradFi, indexes, metals,
    commodities, and every other non-crypto contract must remain absent even when Binance lists a
    perpetual.
16. For every material candidate, verify the committed `candidate_variant.py` ID, overrides, and
    risk-template declaration match its preregistered cell and that zero-argument
    `strategy.build_strategy()` exposes exactly those parameters. Verify the declared template was
    materialized byte-for-byte at root `risk_policy.json`; reject any assumption that the lifecycle
    selects a side-path policy.
17. Preserve and verify the already registered one-row family projection before computing the
    replacement core's final source-bundle fingerprint; do not register or pivot the family.
    Recompute the fingerprint only after the family projection and all three fresh infra-r1 A5
    artifacts exist, then bind that exact value in the later replacement registration.
