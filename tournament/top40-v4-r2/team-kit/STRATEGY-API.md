# Neutral strategy and broker API

## Candidate tree

Create each trial under `candidates/<candidate-id>/` with exactly these required UTF-8 files:

- `candidate.json` — preregistered mechanism, falsifier, horizons, controls, tags, and numeric
  neighborhood coordinates;
- `strategy.py` — a callable `build_strategy()` entrypoint;
- `risk_policy.json` — the declarative central-engine risk policy;
- `README.md` — causal timing, input lineage, parameter rationale, and prospective falsifier; and
- `cleanroom-attestation.json` — the exact candidate identity and clean-room declaration.

Candidate identifiers use lowercase letters, digits, dots, underscores, or hyphens and begin with
a letter or digit. `strategy.py` is the only permitted executable Python module; candidate-defined
helper modules or functions are not admitted. JSON/TOML/YAML configuration may document
the experiment and is archived, but it is never mounted in the strategy worker; every material
runtime parameter must be explicit in Python source and `candidate.json`. The complete tree is
capped at 10 MiB; each file is capped at 2 MiB.

## Entrypoint

`build_strategy()` returns one object implementing the frozen stateless causal subset:

```python
def target_weights(self, context, *, seed):
    ...
```

Return a finite `dict[str, float]`, `None`, or `{}`. A mapping requests an explicit rebalance;
`{}` requests a flat book; `None` holds quantities until the next decision while the central
engine may still enforce membership exits and risk reductions. Symbols must come from
`context.eligible_symbols`. Targets must satisfy gross `sum(abs(w)) <= 1.0`, absolute net
`abs(sum(w)) <= 0.25`, and `abs(w) <= 0.10` per symbol.

At each boundary, `context.decision_time` is timezone-aware UTC. `context.eligible_symbols` is the
point-in-time weekly Top-40 membership intersected with symbols having a hidden executable next
open. `context.bars` maps each eligible symbol to a read-only pandas frame of completed 8-hour bars
at or before the decision. Columns are `open_time`, `symbol`, `open`, `high`, `low`, `close`,
`volume`, `close_time`, `quote_volume`, `trade_count`, `taker_buy_volume`, and
`taker_buy_quote_volume`. Histories can be unequal or short.

`context.funding` is read-only and contains strictly past `funding_time`, `symbol`, `funding_rate`,
`mark_price`, and `settlement_time` rows for eligible symbols. `context.auxiliary` is empty. Do not
mutate context frames. The evaluator owns next-open fills, taker fees, slippage, participation,
funding, membership exits, and risk-policy actions. The fixed integer `seed` is the only randomness
authority, but this edition's stateless subset rejects RNG/random APIs; deterministic candidates
may accept the required `seed` argument without using it.

`target_weights` must be a pure decision function of its current arguments: it cannot access or
mutate `self` state or branch on the decision-time ordinal. Store no counters, caches, fitted state,
iterators, module/class mutation, or prior outputs, and do not delegate the decision to another
candidate-defined function or module. Formation windows may use the completed bar/funding frames supplied in the
current context. Rebalance variants must remain stateless—for example, use transparent properties
of completed observations rather than an invocation counter. The full syntactic limits are listed
in `RULES.md` and are enforced against the exact archived source before nomination.

## Asynchronous requests

For discovery, write exactly eight requests to `outbox/batch-1.json`; for refinement, write
exactly four new requests to `outbox/batch-2.json`:

```json
{
  "schema_version": 1,
  "operation": "is-batch",
  "requests": [
    {
      "candidate_id": "example-baseline",
      "entrypoint": "candidates/example-baseline/strategy.py",
      "purpose": "preregistered baseline"
    }
  ]
}
```

Use unique candidates and list requests in the intended acceptance order. The organizer replaces
the consumed request with a lane-local feedback packet containing each request hash, terminal
status, and successful standardized IS summary. Do not place claimed metrics in the request.

After at least eight accepted trials, write `outbox/decision.json` with either:

```json
{"schema_version":1,"operation":"nominate","candidate_id":"candidate-id","certificate_path":"work/research-certificate.json"}
```

or:

```json
{"schema_version":1,"operation":"retire","reason":"bounded evidence-based reason"}
```

The certificate uses the supplied template. Each of its seven evidence arrays contains unique
official request hashes whose candidate tags support the named cell; their union covers every
accepted trial. An exact sign inversion names the baseline as `parent_candidate_id`, uses identical
mechanism/horizon/control/risk metadata, and returns the negative of every baseline target while
preserving explicit-rebalance versus hold decisions. The organizer verifies the archived target
artifacts, not the tag.

`mechanism` is normally the stable family label established by the first accepted candidate.
Parented `control-ablation` and `role-check` candidates may describe the isolated control more
specifically without changing families. Any genuine family change requires `mechanism-pivot`, is
limited to one accepted pivot, and starts a new parent epoch. The pivot tag is invalid when the
family label did not change.
