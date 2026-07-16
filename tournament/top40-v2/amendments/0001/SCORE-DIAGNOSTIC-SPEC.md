# Top-40 V2 Amendment 0001 — organizer-private score diagnostic

Status: implementation specification; it has no effect until amendment 0001 is reviewed and
frozen. The original Phase-0 record and every file it froze remain unchanged and authoritative.

## Scope

This diagnostic supplies evidence required by the preregistered Team01
`t01-residual-drift-funding-v1` falsifier. It is an organizer audit, not a material configuration,
performance trial, new target, qualification attempt, or change to any team CPU/wall/trial budget.
It does not calculate tournament points or inspect private-qualifier/final-OOS data.

The reviewed adapter ID is `team01-rdf-select-signed-tails-v1`. No other team or family is accepted.

## Historical executable authority

For candidate `C`, the engine derives
`reports-top40-v2/team-01/registration-inputs/C.json`; callers cannot nominate another source path.
That file must have one unique first-add Git commit, no later modification, and exact bytes whose
canonical trial-registration line hashes to the organizer reservation's registration SHA-256.

The engine reconstructs the complete Team01 tree from that commit into a private temporary
directory using Git blobs. It rejects symlinks, submodules, non-regular modes, unsafe paths, and
duplicates. Before execution it recomputes and exactly matches the registered strategy, risk-policy,
and full source-bundle SHA-256 values and seed. Current Team01 worktree files are never substituted.

The completed trial-result authority fixes these additional inputs:

- frozen config path/SHA-256;
- frozen shared snapshot manifest path/SHA-256;
- completed development runner-record path/SHA-256;
- archived canonical `targets.parquet` path/SHA-256; and
- historical registration, strategy, risk, source-bundle, and canonical runtime seed bindings.

## Exact score semantics

The original historical strategy runs inside the frozen V2 Linux namespace, network, filesystem,
resource, audit-hook, Landlock, and seccomp controls. A separate additive worker reuses those frozen
controls.

The organizer adapter does not reproduce or approximate the signal formula. While the original
`target_weights()` call executes, it temporarily wraps that historical module's
`_select_signed_tails(scored, ...)`, records each exact `(symbol, score, residual_volatility)` tuple
passed into the selector, and delegates unchanged to the original selector. Thus the diagnostic
score is the complete combined cross-sectional score after Team01's residual-drift and funding
transforms and before signed-tail selection, inverse-volatility weighting, caps, and BTC sleeve
tilt.

The worker fails closed on an unexpected strategy class/module, changed selector, more than one
selector call, invalid/duplicate/ineligible/non-finite rows, non-positive residual volatility, or
nonempty targets without a captured score. BTC is never a scored asset. Scores may be emitted only
at Team01's scheduled `00:00 UTC` boundary.

## Two deterministic replays and target equivalence

The engine launches two clean worker processes sequentially. Both receive the same canonical
past-truncated contexts through the frozen `_WorkerStrategyProxy` and `generate_targets` APIs.

It requires:

1. replay target frames are bitwise identical;
2. replay score panels are bitwise identical;
3. replay 1 is bitwise identical to the hash-bound completed `targets.parquet`;
4. replay 2 is bitwise identical to that target artifact; and
5. every manifest-listed snapshot file has the same SHA-256 before and after both replays.

Target equality covers the exact UTC index, ordered columns, rebalance booleans, and float64 bit
patterns, including signed zero. No tolerance is used. Failure of any check produces no completed
diagnostic.

## Frozen outcome label

Only captured `00:00 UTC` score cross-sections in visible development are diagnostic observations.
For scored symbol `s` at decision `t`, the outcome is the simple transaction-open return

`open(s, t + 24 hours) / open(s, t) - 1`.

The open timestamped `t` is an outcome: it was hidden from Team01 when the just-closed history at
`t` formed the score. Both opens must exist and be finite and strictly positive. Missing endpoints
are omitted without imputation. Only symbols in the exact captured score cross-section are paired.

The six immutable, contiguous, end-exclusive folds are:

1. `[2020-02-03T00:00:00Z, 2020-09-01T00:00:00Z)`
2. `[2020-09-01T00:00:00Z, 2021-04-01T00:00:00Z)`
3. `[2021-04-01T00:00:00Z, 2021-11-01T00:00:00Z)`
4. `[2021-11-01T00:00:00Z, 2022-06-01T00:00:00Z)`
5. `[2022-06-01T00:00:00Z, 2023-01-01T00:00:00Z)`
6. `[2023-01-01T00:00:00Z, 2023-07-01T00:00:00Z)`

If `t + 24 hours >= fold_end`, the entire decision label is purged. No label crosses a fold.

## Frozen IC convention

For every remaining decision, compute one cross-sectional Spearman correlation between score and
forward return. Ranks are ascending, one-based float64 average ranks for exact ties. A date with
fewer than two pairs or a constant score/return rank vector is undefined and omitted; it is not
zero-filled.

- Pooled IC is the arithmetic mean of all finite daily cross-sectional ICs across the six folds.
- Each fold IC is the arithmetic mean of its finite daily ICs.
- An empty aggregate or fold is `null` and fails positivity.
- Positivity is strict `IC > 0`.
- The registered score gate passes only when pooled IC is positive and at least four of six fold
  ICs are positive, after replay and canonical-target integrity checks pass.

## Private evidence and public boundary

The lifecycle supplies the exact reserved owner-only Git-administrative output directory. The
engine creates exactly these mode-`0600` regular files below a mode-`0700` directory:

- `diagnostic-summary.json`
- `labeled-score-panel.parquet`
- `replay-1-scores.parquet`
- `replay-1-targets.parquet`
- `replay-2-scores.parquet`
- `replay-2-targets.parquet`

Symlinks, hardlinks, unexpected names, unsafe ownership/modes, size-limit violations, or hash
changes are rejected by the amendment integrity layer.

`diagnostic-summary.json` is canonical JSON with exactly:

- `schema_version`, `diagnostic_id`, `reservation_sha256`, and `status="completed"`;
- `replay`: target-replay equality, score-replay equality, and each replay's exact canonical-target
  equality; and
- `score_ic`: private pooled IC, exactly six private fold ICs in `[F1, ..., F6]` order, total
  daily-IC count, and exactly six fold daily-IC counts in the same order.

The lifecycle hashes all six files and derives boolean verdicts from this summary. Numeric ICs,
fold values, labels, scores, and counts never enter public state, CLI output, trial logs, or team
artifacts. The engine's lifecycle API returns only `status`, `failure_reason`,
`organizer_cpu_hours`, and `organizer_wall_clock_hours`.
