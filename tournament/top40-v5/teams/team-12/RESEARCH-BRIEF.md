# Research phases

Market data is mounted. The network is gone -- you have no search, no fetch and no shell.

Your working loop is: form a hypothesis, write `outbox/candidate.py` and `outbox/RATIONALE.md`,
and receive back a standardised metric packet for the **visible** development window. Some days of
that window are sealed and you will never see them; they carry the generalization bar.

## The contract

`candidate.py` must define `build_strategy()` returning an object with:

    target_weights(context, *, seed) -> Mapping[str, float] | None

Return a mapping of symbol to signed unlevered weight, or `None` to hold current quantities. An
empty mapping requests a flat book. Only point-in-time members are tradable. The evaluator enforces
membership exits, delisting exits, participation limits and exposure caps regardless of what you
return.

## What is fixed

- Gross <= 1.0, |net| <= 0.25, per-symbol <= 0.10, participation <= 0.1% of prior-24h quote volume.
- Costs are charged at 1x, 2x and 3x, independently evaluated. A book that only survives at 1x is
  not a book.
- **You may not target volatility.** A common organizer-owned ex-ante risk unit scales every lane
  to the same ex-ante volatility, so the field is compared at equal risk.
- No network, no subprocess, no filesystem, no `eval`/`exec`, no RNG, and no state that persists
  across decisions other than what you fit from the past-only rows you are streamed.

## What ends a trial

Every material trial is journalled before market data opens, and a rejected candidate consumes its
slot. An **evaluator fault does not** -- if the organizer's code breaks, you are refunded.
