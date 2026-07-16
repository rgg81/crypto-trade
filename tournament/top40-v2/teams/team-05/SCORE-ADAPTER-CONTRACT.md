# Preconstruction score and adapter contract

Version: `team05-crtr-v1`

## Score producer

`preconstruction_scores(context, parameters=...)` is a pure boundary function. Its only market
inputs are `context.decision_time`, `open_time` and past-closed `close` series in canonical
RangeIndex `context.bars` frames, and the exact
point-in-time `context.eligible_symbols`. It ignores mapping insertion order, `funding`, and
`auxiliary`. It has no access to open orders, future opens, holdings, entry basis, fills, PnL,
equity, or evaluator risk state.

The output is a symbol-keyed `PreconstructionScore` map. Each record contains the final finite
score, the three raw log returns, realized 8h volatility, and the same broad-market direction
value. Symbols with invalid lineage are omitted. The entire map is empty when fewer than 12 valid
symbols remain. Output keys are exactly valid eligible symbols; reserved metadata can never be a
key.

All transforms are boundary-local and deterministic: time filtering precedes cleaning, cleaning
never backfills, ranks use exact average ties, and all sort fallbacks use ascending symbol text.
There is no randomness and no fitted state. Runtime accepts only the canonical seed `20260801`;
every other value raises before a target is formed. A row is available only when
`open_time + 8h <= decision_time`; the RangeIndex has no timestamp meaning.

## Amendment 0005 score boundary

Immediately after the final score transform and before score-span checks or selection,
`candidate_score_values()` constructs a sorted built-in `dict[str, float]` containing only finite
scores and directly calls
`crypto_trade.tournament.score_adapter_protocol_v5.score_boundary`. Portfolio construction
validates and consumes the values returned by that hook. `candidate_score_payload_bytes()` defines
the canonical byte representation used by the prospective first-candidate score artifact.

The diagnostic label is the simple three-day return from the organizer-authoritative executable
entry open for the target produced at the score decision to the first executable open at or after
three calendar days.
The complete endpoint, missingness, tie, Spearman IC, aggregation, and byte contracts are frozen in
`candidate_score_contract.json`; organizer binding fields are in
`candidate_score_manifest.template.json`. Registration remains blocked until Amendment 0005 and
the v5 protocol module are frozen and hash-bound.

## Portfolio adapter

`scores_to_target_weights(scores, parameters=...)` is a separate pure function. It may read only
the score records and frozen parameters. It applies, in order:

1. finite/schema and minimum-universe guards;
2. the exact A5 score boundary, consuming its returned values;
3. minimum score-span guard;
4. fixed sleeve count and stable score/symbol ordering;
5. soft absolute-trend side preference with deterministic ranked fallback;
6. continuous broad-direction net tilt;
7. fixed equal/strength blend; and
8. per-symbol caps with unfilled sleeve budget left unused.

It returns a sorted finite mapping of signed unlevered target weights or `{}` to request flat. It
never returns `None`; only the strategy schedule returns `None` on a non-rebalance boundary. The
adapter does not infer or simulate fills. The central evaluator remains responsible for next-open
execution, funding, costs, participation, delistings, positions, and the frozen risk policy.

## Frozen invariants

- Same causal context and parameter object produces byte-equivalent scores and targets across
  fresh strategy instances when the exact canonical seed is supplied.
- Appending, deleting, or corrupting rows whose `open_time + 8h` is after the decision cannot
  affect scores.
- Altering `open`, funding, auxiliary fields, or ineligible symbols cannot affect scores.
- Gross request is no more than `target_gross`; absolute net request is no more than
  `maximum_abs_net_tilt`; every absolute symbol request is no more than
  `maximum_symbol_weight`.
- Both sleeves are present whenever the adapter emits a nonempty target.
- Any invalid score record fails closed to `{}` rather than being silently imputed.
