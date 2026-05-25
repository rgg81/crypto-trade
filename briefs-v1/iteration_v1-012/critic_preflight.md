# Phase 6.0 Critic Pre-Flight — iter-v1/012

OVERALL: PASS

## Pre-Flight Checks

### Check 1 (mini) — Brief Look-Ahead Audit: PASS

Brief Section 3.1 explicitly states "Only TWO changes vs /011's branch" with no feature additions, no labeling changes, no universe changes. Section 2.5 (NORMAL-RISK) confirms training rows, labels, weights, feature columns, loss function, R5 mechanism are BIT-IDENTICAL to /011 — only RNG initialization changes via `ensemble_seeds_offset` 0→3. F1-F7 falsifiers in Section 4 operate strictly on post-backtest metrics (OOS Sharpe Δ, IS Sharpe Δ, R5 fire rate, LTC IS roster overlap with /011) — all derivable from reports without inspecting future bars. No "uses tomorrow's", "30-day forward", or "rolling X including current bar" patterns observed.

### Check 13 (mini) — Anti-Pattern Static Scan: PASS

Catalog signatures checked across the full src/ tree:

- **A1** (`train_end_ms = test_start_ms` without subtraction): `grep -rn "train_end_ms\s*=\s*test_start_ms" src/` returns exactly 5 hits, ALL carrying `- embargo_ms` subtraction or documentation comments. `walk_forward.py:113` carries the load-bearing fix. ZERO unexplained matches.
- **A2** (forward-window σ_t): zero matches in labeling.py; σ_t for triple-barrier labels comes via `atr_values` array (computed past-only in feature pipeline), not from forward window inside `label_trades`.
- **A3** (scaler fit on combined train+test): zero matches in v1 path. LightGBM is scale-invariant.
- **A7** (OOF parquet append-without-clearing): `run_baseline_v1.py:940` carries `OOF_PARQUET_PATH.unlink(missing_ok=True)` before training starts.
- **A12** (DSR/PSR wrong-granularity): no src/ changes; reporting_v1.py reading path bit-identical to /011 (passed Phase 7.5).
- **A13** (report-file read before write): only parquet reads are upstream IS-only feature parquet loaders for ADF/IC reporting, NOT runner-internal write-then-read.

### Foundation Regression: PASS

Re-verified `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` (iter-v3/057 fix `e149e9d`). `compute_embargo_candles` is single source of truth used by both `walk_forward.generate_monthly_splits` and `lgbm.py:_train_for_month` for `cv_gap = embargo_candles * n_symbols`. `validation_v1.REQUIRED_GAP = (21 + 1) * 5 = 110` matches v1 baseline universe × (timeout_candles+1) formula. `tests/test_lookahead_embargo.py` contains all 4 mandated regression tests. QE's commits do not touch `walk_forward.py`, `labeling.py`, or `lgbm.py`.

### Cadence + Axis Sanity: PASS

`phase5p5_gate.md` OVERALL=PASS. Brief Section 0.6 declares NEW 8th family `methodology-substrate-test` with rotation status VALID. Prior 5 EXPLORATION families: [feature-family /007, methodology /008, feature-family /009, risk-primitive /010, risk-primitive /011] — no family at 3+/5 saturation. The taxonomy declaration is honest:
- NOT `risk-primitive` (R5 config bit-identical, not an R5 intervention)
- NOT `methodology` (/008 was measurement-layer / report-layer; /012 tests substrate-conditional Optuna basin draws)
- NOT `hyperparameter-region` (/005 shifted search bounds at fixed seed; /012 shifts seed window at fixed bounds)

Cadence position 7/10 EXPLORATIONs in cycle-2; CONFIRMATION earliest at /015. Wall-clock cap ≤2h declared.

**Offset propagation verified**: `_r5_kwargs` dict at `run_baseline_v1.py:960-966` includes `ensemble_seeds_offset=ensemble_seeds_offset`, passed via `**_r5_kwargs` to all 4 model calls (lines 979, 992, 1005, 1019) for the V1_BASELINE_UNIVERSE path, and to the pooled path (line 1038). `run_model` forwards via `_derive_ensemble_seeds(ensemble_size, offset=ensemble_seeds_offset)` at line 243. Banner print at lines 919-923 emits `ensemble_seeds: [789, 1001, 2002] (offset=3)`.

**Seed isolation verified**: every other dimension that could plausibly shift between /011 and /012 was checked: R5-BINARY-KILL config, R5 vol-target disabled, V1_FEATURE_COLUMNS_PRUNED, n_trials=35, training_months=24, OOS_CUTOFF_MS, ATR multipliers per model, R1/R2 apply flags per model — ALL inherited bit-identically from /011.

**F6 join script determinism**: `analysis/iteration_v1-012/f6_roster_overlap.py` is pure-stdlib. No randomness, no time-of-day dependence, no master-data-extent dependence (consumes only the iteration's own trades.csv files). Output rounded to 6 decimals, sorted deterministically.

**/011 F6 reference artifact**: `reports-v1/iteration_v1-011/f6_roster_overlap.csv` confirmed present and matches brief Section 2.1 table (IS PORTFOLIO baseline-overlap 25.44%, iter010-overlap 94.91%; LTC IS iter010-overlap 93.27%). Retroactive Critic Rec #2 fix from /011 closeout is in place.

### Falsifier Presence: PASS

Brief Section 4 carries seven explicit numerical falsifiers F1-F7 with quantitative pass bands. F7 (NEW for /012) carries three-cell substrate-test classification (`>70%` SUBSTRATE-LOCKED, `<30%` SEED-LOCKED, `[30%, 70%]` PARTIAL) with /011 LTC IS overlap with /010 = 93.27% as empirical anchor. Section 8.1 fully pre-registers verdict-class for all measurable F1×F3×F7 cells — zero discretion at verdict time. Section 6 codifies off-table outcomes (F1 OOS Δ > +1.10 numerical-instability tripwire, F2 R5 fire rate outside [10%, 60%] data-integrity tripwire) as BLOCK-PENDING-FIX triggers.

---

Phase 6.0 verdict: PASS. Phase 6 backtest may launch.
