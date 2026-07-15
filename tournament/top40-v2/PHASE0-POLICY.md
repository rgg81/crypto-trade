# Top-40 V2 Phase-0 policy

This policy and `TOURNAMENT-CHARTER-TOP40-V2.md` are authoritative. Machine-readable values in
`config.toml` control whenever prose and configuration differ.

## Qualification, not forced ranking

Ten teams enter research. A team becomes a finalist only after passing the complete development
gate and its one-shot private qualifier. A negative or otherwise unqualified result is research
evidence, not a submission. There is no organizer fallback that advances the least-bad cell.

An unresolved team may keep researching within the common deadline and cumulative budget, make at
most two documented mechanism pivots, or withdraw as DNF. Closing qualification converts every
remaining unresolved team to deadline DNF. Thresholds are never lowered because too few teams
qualify.

## Data authorization boundaries

The visible development worker may receive only history needed through 2023-06-30. It must not
load, hash, serialize, log, or expose private-qualifier or final-OOS observations.

The private qualifier replays the strategy from the canonical start so stateful learning has its
real history, but scores only 2023-07-01 through 2024-06-30. Source, parameters, risk policy,
dependency lock, seed, and cumulative trial ledger freeze before its single ticket is consumed.
Before finalist-cohort lock, only pass/fail and failed gate names may leave the organizer-owned
sealed record; numerical private metrics remain sealed.

Final OOS is unavailable until every team is terminal and the exact qualified/DNF cohort is
first-added and committed. Every finalist then consumes one organizer reveal from the same frozen
bytes. Two clean-process internal replays must produce identical records and artifact hashes;
neither replay is a team research view.

## Research accounting

Every material model, feature, ensemble, portfolio, parameter-neighborhood, and risk-control
variant is registered before its result is read. Pivots do not reset trial, compute, or time
budgets. Each family records a mechanism, economic thesis, parameter ranges, selection rule,
falsifier, and parent family when applicable.

The cumulative limits are 80 material configurations, two mechanism pivots, 12 CPU hours, and 18
wall-clock hours per team. The private qualifier has one ticket. Final OOS has no research views.
The organizer hash-chain journal is authoritative; `experiments.jsonl` is a derived exact
projection. Registration precedes result, failed/interrupted work consumes its trial and resource
budget, and only a whole-record journal prefix may be repaired after interruption.

## Risk controls

The central evaluator owns executed positions, entry basis, equity, peak equity, drawdown, fills,
unfilled requests, and cooldown state. Risk actions are based only on state known at a decision
boundary. Close-confirmed stops and brakes execute at the next available transaction open, pay
ordinary fee and slippage, and share the bar's participation allowance. Intrabar stop fills are
forbidden with the 8h dataset.

Risk action order is fixed:

1. charge funding on the carried position;
2. value the carried book at the boundary mark;
3. evaluate frozen organizer-owned risk policies;
4. execute risk reductions at the next open subject to costs and capacity;
5. apply the risk gate to the strategy request;
6. execute the remaining strategy request;
7. enforce common exposure and delisting controls.

Unless explicitly enabled in the frozen policy, a stopped symbol cannot reopen at the same
boundary.

## Freeze and audit

V2 uses its own branch, source modules, orchestrator, state, journals, manifests, ballots, and
locks. The V1 tournament tree is read-only common history and is excluded from V2 team sandboxes.
V2 Phase 0 binds the exact shared snapshot bytes plus all V2 code and methodology. Any correction
after Phase 0 requires an explicit amendment process or a new tournament; silent rewrites are
forbidden.
