# iter-v3/005 — Seed audit + synthetic 10-seed Pareto

## Two deliverables

This Phase-5 script produces IS-only numerical evidence for two concerns:

1. **Seed-dimension variance audit on iter-v3/003's parquet.** Tests
   iter-v3/004's brief Section 2.1 claim that "every group of 5 rows
   for the same (sym, month, trial, fold, candle) tuple has nunique == 1".
2. **Synthetic 10-seed Pareto consumer-side demo on a small parquet subset.**
   Demonstrates the iter-v3/004 per-cell PBO consumer pipeline run across
   10 outer seeds, with a seed-controlled path-permutation knob, on a
   1-symbol × 3-month subset.

## (a) Seed-dimension variance audit

Empirical breakdown of `nunique(oof_return)` per natural-key group
`(symbol, train_month, trial_id, fold_idx, candle_open_time_ms)`:

| nunique | n_groups | frac |
|---:|---:|---:|
| 1 | 3,692,727 | 0.2345 |
| 2 | 9,220,769 | 0.5855 |
| 3 | 2,834,004 | 0.1800 |

| Aggregate | Value |
|---|---:|
| Total natural-key groups | 15,747,500 |
| Total raw rows | 78,688,992 |
| Mean rows-per-group | 4.9969 |
| Degenerate (nunique==1) | 3,692,727 (23.45%) |
| Variable (nunique>1) | 12,054,773 (76.55%) |

**Variable-group oof_return std distribution** (for the 12,054,773 groups
with `nunique > 1`):

| Stat | Value |
|---|---:|
| mean | 3.8784 |
| median | 3.1342 |
| min | 0.0001 |
| max | 62.2865 |

## Interpretation — iter-v3/004 brief Section 2.1 claim REFINED

iter-v3/004's brief stated "every group of 5 rows for the same (sym, month,
trial, fold, candle) tuple has `nunique(oof_return) == 1`". That claim is
**partially incorrect on the empirical evidence**:

- **23.45% of natural-key groups** are degenerate (`nunique == 1`).
- **76.55% of natural-key groups** are variable (`nunique > 1`),
  with mean variable-group std = 3.8784.

The seed dimension is NOT structurally degenerate. Most natural-key groups DO
carry per-seed signal — the 5 ensemble rows differ. The iter-v3/004
"`nunique == 1`" framing was an over-generalization driven by the writer's
silent five-fold append pattern (no `seed` column persisted), not by the
underlying OOF behavior.

This refinement matters for iter-v3/005 sub-fix #5: the producer-vs-drop
recommendation must consider that ~76% of the parquet's seed dimension
already carries information; the question is whether to surface that
information in the schema (add a `seed` column at write time) OR to honestly
acknowledge that the consumer pipeline (which dedups-by-natural-key) discards
~80% of the data anyway and the schema is misleading.

## (b) Synthetic 10-seed Pareto demo (consumer-side)

Subset: 1 symbol (BCHUSDT) × 3 IS months × 5 trials per cell.

For each of 10 outer seeds in {42, 123, 456, 789, 1001, 7, 13, 17, 23, 37},
the per-cell PBO pipeline runs on the subset with a per-seed RNG-controlled
path-permutation knob. The path-permutation should leave aggregate metrics
stable IF the methodology is robust.

| seed | mean_pbo | median_pbo | median_n_eff | informative_cells |
|---:|---:|---:|---:|---:|
| 42 | 0.0000 | 0.0000 | 24 | 3/3 |
| 123 | 0.0001 | 0.0000 | 24 | 3/3 |
| 456 | 0.0001 | 0.0000 | 24 | 3/3 |
| 789 | 0.0657 | 0.0000 | 24 | 3/3 |
| 1001 | 0.0192 | 0.0000 | 24 | 3/3 |
| 7 | 0.0025 | 0.0000 | 24 | 3/3 |
| 13 | 0.0001 | 0.0000 | 24 | 3/3 |
| 17 | 0.0000 | 0.0000 | 24 | 3/3 |
| 23 | 0.0084 | 0.0000 | 24 | 3/3 |
| 37 | 0.0047 | 0.0000 | 24 | 3/3 |

| Cross-seed summary | Value |
|---|---:|
| mean_pbo: mean across seeds | 0.0101 |
| mean_pbo: std across seeds | 0.0205 |
| mean_pbo: range | [0.0000, 0.0657] |
| n_eff: mean across seeds | 24.0000 |
| n_eff: std across seeds | 0.0000 |

| Pareto-non-domination | Value |
|---|---:|
| n_total_seeds | 10 |
| n_non_dominated | 2 |
| non_dominated_seeds | [42, 17] |

## Implication for iter-v3/005

The demo confirms the per-cell consumer pipeline can produce a meaningful
10-row Pareto table at low cost. The cross-seed std on `mean_pbo` is
0.0205 — small enough to suggest the pipeline is stable across the
benign path-permutation knob, but the actual iter-v3/005 10-seed run
(which varies the OUTER seed driving model training, not just consumer
post-processing) will show larger variance because each outer seed produces
different LightGBM ensemble realizations.

The Phase-5 prediction for iter-v3/005's true 10-seed run is therefore:
- **mean monthly Sharpe across 10 seeds**: prediction ≥ +0.5 (single-seed=42
  was +1.0955 for OOS monthly Sharpe; cross-seed mean may be lower due to
  variance).
- **≥ 7/10 profitable seeds**: prediction TRUE.
- **per-seed PBO std**: prediction in [0.05, 0.20] (above the consumer-side
  permutation std of 0.0205 but below the brief's structural-instability
  falsifier of 0.20).

## Sub-fix #5 framing

If iter-v3/005's `tests/strategies/ml/test_ensemble_seed_propagation.py`:
- **PASSes on iter-v3/003's parquet** (because ~76% of groups DO have
  `nunique > 1`): the test's threshold ("at least 50% of groups have
  `nunique > 1`") is met by the existing data. The seed dimension is
  REAL but UNLABELED — recommend adding a `seed` column to the writer
  schema (iter-v3/006 producer fix), preserving information that already
  exists.
- **FAILs on iter-v3/003's parquet** (if the test counts ALL groups or
  applies a different threshold): the seed dimension is structurally
  degenerate — recommend dropping it from the schema (iter-v3/006 schema
  simplification).

The Phase-5 IS-only audit suggests the FIRST scenario is more likely:
the test threshold "≥ 50% of groups have `nunique > 1`" matches the
76.55% empirical fraction. iter-v3/005's job is to land the test,
run it on the existing parquet, and document the actual outcome — leaving
the producer-vs-drop decision for iter-v3/006.
