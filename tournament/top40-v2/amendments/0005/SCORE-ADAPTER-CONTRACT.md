# Amendment 0005 score-adapter contract

This contract applies only to a prospective Team04–Team10 candidate that opts in before its
material trial registration. It does not retrofit an existing candidate.

## Candidate integration

`strategy.py` must use a direct import:

```python
from crypto_trade.tournament.score_adapter_protocol_v5 import score_boundary
```

At every scheduled decision, call the hook exactly once with the full transformed score map:

```python
scores = score_boundary(scores)
```

The call is after all transformations that define score meaning and direction, but before any
name selection, long/short allocation, weighting, exposure cap, stop, break, or other risk
control. The supplied object must be a built-in `dict`; keys must be currently eligible built-in
strings and values must be finite built-in `int` or `float` values, never booleans. Do not mutate
that dictionary after the call. An unscheduled decision must not call the hook. A scheduled
decision producing nonempty targets must provide a nonempty score map.

In an ordinary run `score_boundary` returns the identical object. It is not a source of data,
state, parameters, or model behavior.

## Registration opt-in

The material trial's `parameters` object contains exactly this nested opt-in shape:

```json
{
  "_top40_v2_score_adapter": {
    "adapter_id": "top40-v2-preconstruction-score-boundary-v1",
    "manifest_sha256": "<lowercase SHA-256>",
    "schema_version": 1
  }
}
```

The manifest path is derived, not caller-selected:

`tournament/top40-v2/teams/<team>/score-adapters/<candidate>.json`

The manifest must be canonical pretty JSON, uniquely first-added, never modified, and present
with the same bytes in the registration commit. Its fixed fields are:

- `stage`: `development`
- `hook`: `strategy.score_boundary`
- `capture_boundary`: `post-transform-pre-selection-weight-cap-risk`
- `schedule_utc.anchor_timestamp_utc`: the first development decision
- `schedule_utc.interval_hours`: a multiple of 8 from 8 through 168
- `label.holding_horizon_hours`: a multiple of 8 from 8 through 168, including 48
- `label.return_definition`: `simple-executable-open-to-open`
- `label.executable_price_column`: `open`
- `label.score_direction`: `higher-score-higher-return`
- `label.statistic_id`: `globally-pooled-pearson-v1`
- `label.purge_cross_fold_endpoints`: `true`
- `label.minimum_pairs`: an integer from 2 through 1,000,000

`score_description` must explain the score economically and state why larger values imply larger
expected forward returns. The description is evidence, not executable configuration.

## Diagnostic semantics

The organizer runs two isolated replays of the exact preregistration source and seed. Every score
and target must reproduce exactly, and replayed targets must equal the archived completed
development targets. A label uses the exact executable open at time `t` and at
`t + holding_horizon_hours`:

`forward_return = open_end / open_start - 1`

Pairs with missing, non-finite, or non-positive opens are unavailable. A pair is purged when its
endpoint is at or beyond its start fold's exclusive end. Pearson is pooled across all retained
candidate-symbol pairs for the complete development window and separately for each fold; it is
undefined when the manifest minimum pair count or nonzero-variance condition is not met.

The numeric result is public development research evidence. It does not add, replace, or weaken
any tournament qualification gate.
