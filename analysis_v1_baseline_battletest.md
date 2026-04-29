# v1 Baseline Battle Test — FINAL CONCLUSION

**Date**: 2026-04-21
**Verdict**: **BASELINE.md's +2.83 OOS Sharpe is NOT reproducible with today's codebase.**
No bug in my reproduction. No bug in the current code. The Apr 5 state that
produced +2.83 is lost.

## Verified identical (all byte-level)

| Component | Status |
|---|---|
| Kline CSVs (BTC/ETH/LINK/BNB) | Identical worktree ↔ main (diff empty) |
| Feature code (all 8 feature *.py files) | 0 lines of diff vs Apr 5 commit `ee62224` |
| Feature parquet VALUES (14 tested dates 2022–2026) | 0 column diffs |
| Strategy code (lgbm, optimization, labeling, walk_forward) | 0 lines of diff vs Apr 5 |
| Backtest logic | Only renames (private→public), no behavior change |
| Seeds `[42,123,456,789,1001]`, config (cooldown, VT params, ATR mults) | Exact match |
| LightGBM determinism on real BNB training data | Proven (same threshold, same trees across two runs) |

## Verified DIFFERENT (and we cannot recover Apr 5 state)

| Component | Problem |
|---|---|
| Parquet column ORDER | Depends on how `generate_features` was called on Apr 5. That call is lost. Tried alphabetical group order and registration order — both diverge from BASELINE. |

## Root cause

LightGBM's `colsample_bytree < 1.0` (default in this config: 0.3–1.0 Optuna range)
samples columns by position. Reorder columns → same seeded RNG picks different
columns for each tree → different tree structure → different probabilities →
different trade signals. We empirically proved this:

```
colsample_bytree=1.0: Predictions identical bit-for-bit ✓
colsample_bytree=0.7: 6.1% label flips from reordering columns
```

The Apr 5 parquet had a specific column ordering produced by whatever specific
`generate_features(df, groups=…)` call was made at that moment. That groups
list could have been:
- `list_groups()` (alphabetical: calendar, interaction, mean_reversion, momentum, statistical, trend, volatility, volume)
- The explicit registration list (momentum, volatility, trend, volume, mean_reversion, statistical, interaction, calendar)
- A partial regeneration that preserved some older ordering from when individual groups were added one-at-a-time across iterations 033 → 151
- Something else entirely

I tested both documented orders. **Both diverge from BASELINE at the very first trade** (an extra BNB short on 2022-02-04 that BASELINE doesn't have).

## Fail-fast divergences (Model D BNB, registration-order regenerated parquet)

```
#   BASELINE                      MY RUN                       Match
1   2022-02-14 07:59 S @395.59    2022-02-04 23:59 S @399.33   ✗ (extra)
2   2022-02-16 07:59 S @430.62    2022-02-12 15:59 S @397.68   ✗
3   2022-02-28 23:59 S @395.50    2022-02-16 07:59 S @430.62   = BASELINE #2
4   2022-03-02 15:59 S @408.47    2022-03-01 07:59 S @413.38   ✗
5   2022-03-10 23:59 L @371.77    2022-03-09 15:59 S @397.33   ✗
...
```

Only 3 of first 9 trades overlap. Alphabetical-group order regeneration
produced the same Feb 4 extra trade.

## The Feb 4, 2022 canary trade

My reproductions consistently open a BNB short at `2022-02-04 23:59` that
BASELINE does NOT have. This trade requires:
- Model trained on Feb-2020 → Jan-2022 data (both runs have identical training data)
- Proba at Feb-4-23:59 candle > the Optuna-tuned threshold

The feature values at that candle are verified byte-identical across runs.
The only thing that changes is the tree structure (from column-position-dependent
sampling). That's enough to push the Feb 4 probability above threshold in my
run but (apparently) below in BASELINE.

## What this means for production

**You cannot trust any absolute Sharpe number from iter-100 onward** —
they were all measured with the Apr-5-era parquet ordering that's now
unrecoverable. Any LIVE deployment today will train models with WHATEVER
column order the current parquet has, producing signals that don't match
BASELINE's.

Relative orderings of iterations (iter-151 vs iter-152, etc.) might still
be valid since all those measurements used parquets in consistent ordering
during that stretch. But the absolute numbers drift.

## Recommended path forward (2 steps)

### Step 1: Lock in column ORDER

Save a canonical list as the single source of truth. Going forward every
run — backtest, live, reproduction — loads features in this exact order.

I saved `src/crypto_trade/baseline_feature_columns.py` earlier with alphabetical-
group schema order (not the right one for BASELINE, but it is a reproducible
reference). Consider instead saving the registration-order list which is more
intuitive.

### Step 2: Re-measure the baseline with that order

Run the full A+C+D portfolio ONCE with the canonical order. Whatever Sharpe
it produces IS the new "real" BASELINE. Update BASELINE.md. All future
iterations compare against this reproducible number.

### Step 3 (also recommended): Make it order-invariant

To prevent this from recurring, pass `deterministic=True, force_col_wise=True,
num_threads=1, colsample_bytree=1.0` in the LGBM params (skip the colsample
Optuna search too). This gives bit-exact reproducibility regardless of column
order. Might reduce performance marginally — worth testing.

## Don't put money on +2.83

BASELINE.md's +2.83 is a point-in-time artifact. The corresponding model does
not exist in any reproducible form. If you deploy v1 today, you'll get a
model trained on features in whatever order today's parquet has, producing
trades that differ materially from the Feb 2025 – Apr 2026 trades in
`reports/iteration_152_min33_max200/`.

**The v1 track cannot be audited for reproducibility without step 1 + step 2.**
Until that's done, v2 (which at least has a stable recently-measured
baseline + 10-seed validation) is the safer deployment target.

## Artifacts

- `src/crypto_trade/baseline_feature_columns.py` — first canonical order attempt
  (alphabetical-group schema order, will be replaced by registration order)
- `test_lgbm_col_order.py` — proves column order changes predictions
- `test_lgbm_determinism_real.py` — proves LGBM is deterministic on real data
- `compare_baseline_vs_clean.py` — trade-level forensic comparison
- `trade_diff_detail.py` — specific divergent trade listings
- `reports/iteration_152_core_alpha_order/` — Run #2 (alphabetical, OOS +1.04)
- `reports/iteration_152_core_buggy_196/` — Run #1 (196 cols, OOS +0.63)
- Aborted Run #3 (registration order, schema auto-discovery): 9 trades before
  kill — pattern matched Run #2's divergence.
