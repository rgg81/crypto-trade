# Phase 6.0 Critic Pre-Flight — iter-v1/038

OVERALL: PASS

## Pre-Flight Checks

### Check A — Brief Look-Ahead Audit: PASS
Ceiling threshold computation in `src/crypto_trade/risk/vol_ceiling.py:compute_per_symbol_vol_ceiling` filters `close_time < OOS_CUTOFF_MS` (line 130) BEFORE percentile estimation. `compute_rv_30d_ann_at_bar` slices `closes_arr[:idx+1]` (line 73-74). Runner pre-computes thresholds at `run_baseline_v1.py:2337-2370` once-per-run with IS-only filtering downstream. Test 3 (`test_v1_038_compute_per_symbol_vol_ceiling_oos_exclusion`) demonstrates OOS bars do NOT affect threshold. Past-only confirmed at both feature and threshold layers.

### Check B — Dispatch defect + Mini-Check J: PASS
- `"v1-038"` present in catch-all exclusion tuple at `run_baseline_v1.py:4048`.
- `iteration_label == "v1-038"` elif at line 3932 fires BEFORE catch-all at 4034.
- Pre-flight asserts at 3941-3960 cover mode, pct range [70,80], scale==0.5, and universe.

### Check C — Wiring sanity: PASS
Flag → arg → kwargs → strategy → trade-time gate fully threaded: CLI flags at `run_baseline_v1.py:1999-2024`; resolution at 2257-2264; `vol_ceiling_enabled=vol_ceiling_mode_arg=="per_symbol"` at 2328; thresholds wired into `_r5_kwargs["vol_ceiling_thresholds"]` at 2370; `backtest.py:419-421/588-590` accepts in `run()` + `BacktestConfig`; trade-time gate at `backtest.py:521-534` multiplies `vt_scale *= config.vol_ceiling_scale` when `_vc_rv > _vc_thr`; IS/OOS counters partitioned at OOS_CUTOFF_MS; aggregation + comparison.csv reporting at runner 4896-5010.

### Check D — Configuration sanity: PASS
Brief Section 5: n_trials=18, ENSEMBLE_SIZE=3, seeds=1, universe=V1_BASELINE_UNIVERSE (5 cohorts), V1_FEATURE_COLUMNS_PRUNED (43 cols) UNCHANGED. Dispatch banner at line 3961-3970 verifies all five.

### Check E — Test suite: tests-not-yet-run-orchestrator-will-run
13 tests in `tests/test_iteration_v1_038.py` cover: CLI parsing, p75 numpy reference, OOS exclusion, above/below/NaN ceiling, past-only rv, banner, mode/pct asserts, catchall membership, threshold logging, walk_forward embargo regression. Logic inspection clean.

### Check F — Anti-pattern A1-A14: PASS
A1 (`train_end_ms = test_start_ms` no-subtract): 0 matches. `walk_forward.py:113` carries `- embargo_ms`. A2 (forward-window std): 0. A3 (fit_transform combined): 0. A12 (psr/dsr granularity): N/A (no new report-layer math). A13 (write-before-read): N/A.

### Mini-Check K — Strategy attribute symmetry: PASS
`vol_ceiling_enabled`, `vol_ceiling_scale`, `vol_ceiling_thresholds` consistent across CLI args, BacktestConfig (backtest.py:419-421, 588-590), runner threading (line 2328-2330, 2370), and gate evaluation (backtest.py:521-534).

### Mini-Check L — Wall-clock plausibility: PASS
Anchored /034 ~50min at IDENTICAL config (5 cohorts, n_trials=18, ENS=3, single-seed, 43 feats). Sizing-layer post-prediction gate = zero training-time impact; rv-lookup build is one O(N) scan per symbol at run start (~5s). Modal ~53min; conservative 45-75min.

## Approved Launch Invocation

```bash
PYTHONUNBUFFERED=1 uv run python run_baseline_v1.py \
  --pruned-features --iteration 38 --exploration \
  --n-trials 18 --ensemble-size 3 --seeds 1 \
  --vol-ceiling-mode per_symbol --vol-ceiling-pct 75 --vol-ceiling-scale 0.5 \
  > logs/iter_v1_038_backtest.log 2>&1
```

Phase 6 backtest launch AUTHORIZED.
