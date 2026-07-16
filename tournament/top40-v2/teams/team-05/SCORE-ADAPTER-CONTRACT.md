# Preconstruction score and adapter contract

Version: `team05-crtr-v1`

## Score producer

`preconstruction_scores(context, parameters=...)` is a pure boundary function. Its only market
inputs are `context.decision_time`, past-closed `close` series in `context.bars`, and the exact
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
There is no randomness and no fitted state. The evaluator-provided seed is validated but cannot
alter a score.

## Portfolio adapter

`scores_to_target_weights(scores, parameters=...)` is a separate pure function. It may read only
the score records and frozen parameters. It applies, in order:

1. finite/schema and minimum-universe guards;
2. minimum score-span guard;
3. fixed sleeve count and stable score/symbol ordering;
4. soft absolute-trend side preference with deterministic ranked fallback;
5. continuous broad-direction net tilt;
6. fixed equal/strength blend; and
7. per-symbol caps with unfilled sleeve budget left unused.

It returns a sorted finite mapping of signed unlevered target weights or `{}` to request flat. It
never returns `None`; only the strategy schedule returns `None` on a non-rebalance boundary. The
adapter does not infer or simulate fills. The central evaluator remains responsible for next-open
execution, funding, costs, participation, delistings, positions, and the frozen risk policy.

## Frozen invariants

- Same causal context and parameter object produces byte-order-equivalent targets across fresh
  strategy instances and all non-negative integer seeds.
- Appending, deleting, or corrupting rows strictly after the decision cannot affect scores.
- Altering `open`, funding, auxiliary fields, or ineligible symbols cannot affect scores.
- Gross request is no more than `target_gross`; absolute net request is no more than
  `maximum_abs_net_tilt`; every absolute symbol request is no more than
  `maximum_symbol_weight`.
- Both sleeves are present whenever the adapter emits a nonempty target.
- Any invalid score record fails closed to `{}` rather than being silently imputed.
