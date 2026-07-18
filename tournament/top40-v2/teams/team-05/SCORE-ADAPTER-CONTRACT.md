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
validates and consumes the values returned by that hook. `candidate_score_payload_bytes()` is a
team-local synthetic audit representation for byte-invariance checks; it is not an A5 artifact or
substitute for A5's captured replay evidence. The runtime dataclass annotations are not trusted as
validators: every record field must have its
declared exact runtime type and satisfy the finite/range rules before the hook. Any malformed
nonempty score map returns `{}` from `candidate_score_values()`, `b""` from
`candidate_score_payload_bytes()`, and `{}` from construction without coercion or an exception.

Amendment 0005 is active through
`scripts/top40_v2_tournament_score_diagnostics_v5.py` at SHA-256
`0dc9228f3b9c6fe41b2655055f766fc92f323a289a050e6bdf4e48a30b0105f4`. The controlling
integration-freeze commit is `d2b95f610722aab65b4e67466b34efeaa3554101`, and its file SHA-256
is `b3b2b96245a479ccfff95b5cd5b5cd0aef3b2d0aac0fc9faf5367d3e6772958c`.

Ordinary development execution now uses the active Amendment 0007 entrypoint
`scripts/top40_v2_tournament_runtime_preload_v7.py` at SHA-256
`8a4ada10176d2606df3f358fc188e21b45153ad9a7270f36908736f03322a3a9`. Its integration-freeze
commit is `c8b917ca49306d5200a4e08848e73ff6f5a18bf3` and its SHA-256 is
`6f77a146e7b414eabd20c5cc9321a95493bb98116dde07ef79d9eb009b6a6f51`. The one-shot
administrative eligibility for `team05-crtr-core-v2-infra-r1` is the frozen Amendment 0008 at
commit `f6003ae687d5a6bf665abb001715b01ea8b10abb`, SHA-256
`08bf194c9ade1f66bf38012210ad8604df61ca467cdad00bd3957aa679ea9bdd`. Neither authority changes
the score boundary, schedule, label, direction, or statistic below.

The declared diagnostic schedule is every 72 hours from `2020-01-01T00:00:00Z`, matching the
strategy schedule. Its label is the simple return between the organizer-authoritative executable
`open` at the score decision and the exact executable `open` 72 hours later. A decision is purged
when its endpoint touches or crosses the frozen fold end; an absent, nonfinite, or nonpositive
endpoint omits that symbol-label pair without substitution. The fixed statistic is globally pooled
Pearson correlation, repeated within each frozen fold, with 12 minimum pairs. It is non-material,
does not charge the trial budget, and is never an automatic qualification gate.

Only the first no-control core is declared to opt into this candidate-specific A5 diagnostic. The
unchanged score mechanism may be reused by later preregistered policy/neighbor trials, but they do
not inherit or reuse the core manifest identity.

The exact A5 score-manifest shape is in `candidate_score_manifest.template.json`. The complete
acyclic dependency declaration is in `executable_source_manifest.template.json`, and the fixed
independent attestation shape is in `semantic_coupling_review.template.json`. Those root templates
are not the canonical A5 artifacts. The organizer must materialize them respectively as:

1. `score-adapters/team05-crtr-core-v2-infra-r1.executable-source-manifest.json`;
2. `score-adapters/team05-crtr-core-v2-infra-r1.semantic-coupling-review.json`; and
3. `score-adapters/team05-crtr-core-v2-infra-r1.json`.

They must be canonical pretty JSON and immutable unique first-adds in that order, with the score
manifest preceding the replacement registration. All material hashes, byte sizes, reviewer
identity, and review timestamp remain prospective placeholders. The existing v2 files remain
immutable historical controls for the infrastructure-failed event and cannot stand in for any
replacement artifact. No current infra-r1 file is a semantic approval, registration, diagnostic
result, or performance claim.

The active entrypoint delegates ordinary tournament behavior through Amendment 0006. Therefore
the score and target universe is only the A6-certified point-in-time native crypto universe.
Stablecoins, equities/TradFi, indexes, metals, commodities, and other non-crypto perpetuals are
ineligible. Team05 may only consume `context.eligible_symbols` and may never re-expand it.

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
- Any invalid score record, including a wrong-typed dataclass field, fails closed to `{}` and
  empty artifact bytes rather than raising, coercing, serializing a valid-looking empty payload,
  or being silently imputed.
