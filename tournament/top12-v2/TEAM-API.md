# Neutral team API

This document describes mechanics only. It contains no alpha idea or prior result.

Each candidate directory contains:

- `strategy.py`, defining `build_strategy()` and one `target_weights` method;
- `candidate.json`, the preregistration;
- `risk_policy.json`, declarative organizer-enforced controls; and
- `README.md`, a concise economic explanation and falsifier.

The runner constructs a clean strategy instance with `build_strategy()`. The strategy implements:

```python
def target_weights(self, context, *, seed: int) -> Mapping[str, float] | None:
    ...
```

`context.decision_time` is UTC. `context.bars` maps eligible symbols to past-only 8h frames with
`open_time`, OHLC, base and quote volume, trade count, and taker-buy volume fields.
`context.funding` contains settled funding rows strictly before the decision boundary.
`context.eligible_symbols` is the weekly Top-12 membership intersected with contracts that have a
next executable open. That open is not visible.

A mapping requests signed unlevered target weights. An empty mapping requests a flat book. `None`
keeps current quantities except for organizer-enforced exits and exposure reductions. Targets must
be finite and deterministic under the frozen seed. The central evaluator owns all fills, funding,
costs, participation, membership exits, and risk controls.

Candidates may use Python's standard library, NumPy, and pandas. They may not read files, inspect
the environment, use the network, spawn processes, manufacture PnL/fills, or mutate supplied data.
The sealed worker enforces these restrictions.

Only completed bars may inform a decision. A row with `open_time=t` is complete at `t+8h`.
Funding must be settled strictly before the boundary. Rebalances execute at the next executable
open after the decision.

`candidate.json` must declare:

- exact team and candidate IDs;
- the assigned mechanism string;
- parent or null;
- hypothesis and falsifier;
- formation and rebalance horizons;
- control profile;
- material parameters;
- research tags; and
- optional preregistered neighborhood ID and numeric coordinates.

Changing any candidate byte or material declaration creates a new candidate and consumes a new
accepted trial.

The exact candidate schema is:

```json
{
  "schema_version": 1,
  "team_id": "team-NN",
  "candidate_id": "unique-lowercase-id",
  "parent_candidate_id": null,
  "mechanism": "exact-assigned-mechanism",
  "hypothesis": "bounded single-line text",
  "falsifier": "bounded single-line text",
  "formation_horizon": "bounded single-line text",
  "rebalance_horizon": "bounded single-line text",
  "control_profile": "bounded single-line text",
  "neighborhood_id": null,
  "neighborhood_coordinates": {},
  "tags": ["baseline"],
  "material_parameters": {"example_numeric_or_structured_parameter": 1}
}
```

The exact risk-policy schema is:

```json
{
  "schema_version": 1,
  "policy_id": "unique-lowercase-policy-id",
  "same_boundary_reentry": false,
  "volatility_target": {
    "enabled": true,
    "lookback_days": 30,
    "annualized_target": 0.20,
    "minimum_scale": 0.20,
    "maximum_scale": 1.0
  },
  "drawdown_brakes": [
    {"drawdown": 0.10, "gross_scale": 0.75},
    {"drawdown": 0.15, "gross_scale": 0.50}
  ],
  "position_stop": {"enabled": false, "loss_fraction": 0.10, "cooldown_bars": 0},
  "time_stop": {"enabled": false, "maximum_holding_bars": 30, "cooldown_bars": 0},
  "turnover_limit": {"enabled": true, "maximum_one_way_turnover": 0.20},
  "side_scaling": {"long_scale": 1.0, "short_scale": 1.0}
}
```

All keys are mandatory. A disabled control still needs valid parameters. Risk policies may scale
or block organizer-evaluated targets but may never create leverage beyond the central caps.
