# iter-v3/003 — IS-Only Numerical Evidence Synthesis

**Date**: 2026-05-04
**Author**: QR (autopilot)
**Source**: `analysis/iteration_v3-003/pbo_strategy_axis_demo.py` (committed before brief)
**Inputs read**: `reports-v3/iteration_v3-002/cpcv_paths.csv` (45 paths, 1 column, IS-window
candle sequence, REQUIRED_GAP=88).  No OOS data accessed.

## What this script demonstrates

The corrected `pbo_from_cpcv` algorithm (validation_v3.py:165-340 on `iteration-v3/002`
branch) is **structurally correct** but **structurally inert** when called on iter-v3/002's
S=1 path matrix.  Run it on the actual iter-v3/002 input → returns `pbo=None`, which is the
documented "test could not run" outcome rather than an informative number.  The fix is
**upstream**: `LightGbmStrategy._train_for_month` must persist per-Optuna-trial
out-of-fold returns so the runner can build a (45, 50) matrix instead of a (45, 1) column.

## Results — `pbo_strategy_axis.csv`

PBO at S in {1, 5, 25, 50, 100} for three regimes.  Base path Sharpes are iter-v3/002's
exact 45 values.  Mean = +0.257, std = 1.188, 60% positive (mean recovers an anti-edge
signature, but with high variance — same evidence the iter-v3/001 diary surfaced):

| Regime | S | PBO | Verdict |
|---|---:|---:|---|
| iter-v3/002 actual (no replication) | 1 | NaN | "test could not run" — CURRENT iter-v3/002 STATE |
| iter-v3/002 actual REPLICATED S times | 5 | 0.7808 | replica-degenerate (every strategy identical → IS-best is never anti-correlated with OOS) |
| iter-v3/002 actual REPLICATED S times | 50 | 0.7808 | same — saturates, replication adds no information |
| Near-overfit synthetic | 5 | 1.0000 | correctly identifies overfit (strategy 0 anti-correlated by construction) |
| Near-overfit synthetic | 50 | 1.0000 | same |
| Near-clean IID, σ from base | 5 | 0.163 | small S → small-sample optimism |
| Near-clean IID, σ from base | 25 | 0.560 | regression-to-mean baseline (matches LdP expected ~0.5+ε) |
| Near-clean IID, σ from base | 50 | 0.795 | high — IID at this σ is hard to beat OOS-half median |
| Near-clean IID, σ from base | 100 | 0.677 | converges below 0.8 |

### Reading the table

Three points worth highlighting:

1. **The iter-v3/002 actual S=1 case (top row) reproduces precisely the current state.**
   PBO=NaN.  This is what `reports-v3/iteration_v3-002/dsr.json` and
   `reports-v3/iteration_v3-002/comparison.csv` report.  The Critic flagged this as
   the methodology-killer FAIL on Check 3.

2. **Replicating the same column S times produces a trivially-overfit-looking matrix
   (PBO=0.78).** This is what would happen if iter-v3/003's Engineer "shipped" by tiling
   the iter-v3/002 column 50 times — it would technically produce S=50 input but the
   PBO would be uninformative because every "strategy" is the same path.  This is the
   easy mistake to avoid in Phase 6.  The persistence_schema.csv (column-by-column
   prescription) prevents this by requiring DISTINCT trial_ids with INDEPENDENT
   out-of-fold returns.

3. **The near-overfit and near-clean cases bracket what iter-v3/003 should produce.**
   When the lgbm.py modification lands and a real (45, 50) matrix exists, PBO will land
   somewhere in [0, 1) — not NaN, not pegged at 0 by a tiling artifact.  Where it lands
   IS the methodology-validated answer.  The iteration's Phase 4 prediction (Section 4)
   commits to "any value in [0, 1] is acceptable; NaN is not" — which is the falsifier.

## What `LightGbmStrategy._train_for_month` must change

The CURRENT structure (verified on `iteration-v3/002` branch via `git show`):

```python
# src/crypto_trade/strategies/ml/lgbm.py:_train_for_month, lines 437-457:
for i, seed in enumerate(seeds):
    ...
    model, selected_cols, confidence_threshold = optimize_and_train(
        feat_train, train_labels, available_feat_cols,
        long_pnls, short_pnls,
        self.n_trials,        # ← 50 trials per month, per ensemble seed
        self.cv_splits,       # ← 5 folds per trial
        seed, self.verbose,
        sample_weights=train_weights,
        open_times=train_open_times,
        train_end_ms=split.train_end_ms,
        ternary=ternary,
        cv_gap=cv_gap,
    )
    self._models.append(model)
    self._confidence_thresholds.append(confidence_threshold)
```

`optimize_and_train` (optimization.py:270-386) wraps Optuna's `study.optimize(...)` with
`_objective` (optimization.py:140-267).  The objective ALREADY iterates through
`TimeSeriesSplit(n_splits=cv_splits, gap=cv_gap)` and computes per-fold predictions —
the OOF returns are in scope at line 254-258 of `_objective`:

```python
y_proba = model.predict_proba(feat_val)
sharpe = compute_sharpe_with_threshold(
    y_proba, long_pnls[val_idx], short_pnls[val_idx],
    confidence_threshold, ternary=ternary,
)
sharpes.append(sharpe)
```

The iter-v3/003 modification adds **one persistence side-effect** to the objective: for
each (trial, fold), append the per-candle OOF return + (trial_id, symbol, train_month,
fold_idx, candle_open_time_ms) to a buffer.  After `study.optimize()` returns, the buffer
is flushed to a parquet file at `reports-v3/iteration_v3-003/trial_oof_returns.parquet`.

## Persistence schema (prescribed)

See `persistence_schema.csv` for the full column dictionary.  Quick summary:

| Column | dtype | Load-bearing for |
|---|---|---|
| trial_id | int32 | indexes the strategy axis of the path matrix (S = #unique trial_ids) |
| symbol | string | aggregation across symbols when building the candle timeline |
| train_month | string YYYY-MM | ensures cross-month trials are not co-mingled in PBO |
| fold_idx | int8 | lets the runner verify per-fold OOF coverage is complete |
| candle_open_time_ms | int64 | joins to CPCV path test_idx via candle position |
| oof_return | float64 | THE input value to the path matrix M[path, trial] |

**Volume budget**: 50 trials × 5 folds × ~20 test_candles per fold × 4 symbols ×
~25 walk-forward months ≈ 500,000 rows ≈ 24 MB on disk.  Negligible compared with the
2.16h backtest wall-clock from iter-v3/002.

**Path matrix construction**:

```python
# Pseudocode for _compute_cpcv_paths (after iter-v3/003 modification)
trial_oof = pd.read_parquet(report_dir / "trial_oof_returns.parquet")
n_trials = trial_oof["trial_id"].nunique()
combined = trial_oof.groupby(["trial_id", "candle_open_time_ms"])["oof_return"].sum()
splits = combinatorial_purged_cv(n_samples=n_candles, ...)
mat = np.zeros((len(splits), n_trials))
for path_id, (_, test_idx) in enumerate(splits):
    test_candles = candle_timeline[test_idx]
    for trial in range(n_trials):
        path_returns = combined.loc[trial].reindex(test_candles).fillna(0).to_numpy()
        mat[path_id, trial] = mu/sigma sharpe of path_returns
```

The path matrix shape becomes (45, 50) for the canonical config — exactly the input
type the CSCV expects.

## Falsifier (re-stated for clarity)

If iter-v3/003's Engineer ships the lgbm.py modification correctly, the path matrix
will be shape (45, 50) and `pbo_from_cpcv` will return a number in [0, 1].  This number
is the methodology-validated PBO.  Any of the following outcomes invalidate iter-v3/003:

- PBO is NaN (S=1 again — the modification didn't ship).
- PBO is exactly 0.0 (replica-degenerate — the modification tiled, didn't persist
  per-trial OOF).
- The parquet has fewer than `n_optuna_trials × n_cv_folds × ~20 candles per fold`
  rows (the persistence loop dropped data).
- The parquet has rows for trial_id values outside `[0, n_trials × n_models × n_months)`
  (id collision across months/symbols).

## What this iteration does NOT change

- Universe (BCH, MKR, LDO, TRX) — unchanged from iter-v3/001 / iter-v3/002.
- Features (V3_FEATURE_COLUMNS, 34 columns) — unchanged.
- Labeling (triple-barrier with NATR scaling, 21-candle timeout) — unchanged.
- Risk gates (v2's 5-gate set + BTC trend filter) — unchanged.
- Model headline metrics (IS Sharpe, OOS Sharpe, trades, concentration) WILL match
  iter-v3/002 EXACTLY. The model itself is not modified — only its trial-OOF logging is.

## Single-fix discipline

iter-v3/002 had FIVE methodology fixes promised; only THREE landed correctly (PBO
algorithm in validation_v3.py, embargo assertion, ADF granularity).  Two were
half-shipped because the runner-side and validation_v3-side fixes did not extend to
`LightGbmStrategy._train_for_month`.  iter-v3/003's discipline is to ship ONLY the
remaining two related sub-fixes: per-trial OOF persistence (sub-fix B of iter-v3/002
fix #2) and consequently the corrected n_eff_trials (iter-v3/002 fix #5 with real
per-trial returns instead of zero-padded surrogates).

The discipline is **explicitly mandated** by Critic Recommendation #1 and #3 from
iter-v3/002's review: each Section 3.5 fix must decompose into atomic sub-fixes, and
each sub-fix's reconciliation row must reference a verifiable file artifact (not a
prose description).
