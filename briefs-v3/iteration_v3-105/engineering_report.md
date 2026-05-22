# Engineering Report — iter-v3/105

## Headers

- Iteration: iter-v3/105
- Branch: iteration-v3/105
- Commit SHA (gate): 3ce01acf6f4009a7263ebef58968fe7b9a489b88
- Commit SHA (implementation + tests, HEAD): a819727b724ee3894643e01ca3d1baa7d45c27c8
- Hardware: 20-core CPU, 58 GiB RAM (WSL2/DESKTOP-H1H6T11)
- Wall-clock time: SETUP-ONLY — backtest not yet launched (multi-hour; split-dispatch per
  `feedback_split_engineer_dispatch.md`)

## Configuration Diff vs BASELINE_V3.md (/059 canonical)

| Parameter | Baseline (/059) | iter-v3/105 |
|---|---|---|
| `ITERATION_LABEL` | `"v3-059"` | `"v3-105"` |
| `label_mode` | `"triple_barrier"` | `"trend_scanning"` |
| `trend_scan_grid` | N/A (not present) | `(5, 8, 13, 21)` |
| `V3_MODELS` | `(BCH, LDO, TRX)` | `(BCH, LDO, TRX)` — unchanged |
| `OOS_CUTOFF_DATE` | `2025-03-24` | `2025-03-24` — SACRED, unchanged |
| `training_months` | `24` | `24` — SACRED, unchanged |
| Inner ensemble seeds | `[42, 123, 456, 789, 1001]` | unchanged |
| `n_trials` | `35` | `35` — unchanged |
| Run mode | EXPLORATION (3-seed) | EXPLORATION (3-seed) — unchanged |
| `EXPLORATION_ENSEMBLE_SIZE` | `3` | `3` — unchanged |
| `REQUIRED_GAP` | `66 = (21+1)×3` | `66 = (21+1)×3` — unchanged by design |
| Walk-forward embargo | `22 candles` | `22 candles` — unchanged by design |
| `feature_columns` | explicit, 14-feature list | explicit, same 14-feature list — unchanged |
| Triple-barrier EXECUTION exits | SL / TP / timeout at 21 candles | SL / TP / timeout at 21 candles — unchanged |

ONE clean variable: `label_mode` changed from `"triple_barrier"` to `"trend_scanning"`.
`trend_scan_grid=(5,8,13,21)` is the parameterization of the new mode (not a second
variable). The capped grid `max(grid)=21` equals the incumbent timeout — REQUIRED_GAP=66
and embargo=22 are numerically unchanged by design (per brief Section 3.1).

## Phase 5.5 Gate

OVERALL: PASS. Gate file `briefs-v3/iteration_v3-105/phase5p5_gate.md` committed at
`3ce01ac`. All 10 mandatory sections (0-9) verified PASS. One Phase-6 verification note
(not a BLOCK): the hard label-leakage test confirming `max(grid)=21 <= timeout_candles=21`
was mandated in the gate note and has been implemented as:
- A runtime preflight assertion in `run_baseline_v3.py` (`_verify_feature_columns`)
- A dedicated test `test_trend_scanning_max_grid_leakage_guard` in the test suite

## Implementation — the `label_mode="trend_scanning"` axis

Three source files and one runner modified; one new test file added.

### `src/crypto_trade/strategies/ml/labeling.py`

New private helper `_trend_scan_label(close_arr, sym_idx, pos, grid)`:
- Pre-gathers up to `max(grid)` forward close prices from the master array.
- For each horizon `h` in grid: builds `y=[entry_close, available[0..h-1]]`, `x=[0..h]`,
  computes closed-form OLS slope and t-statistic (`dof=n-2`, `t=slope/SE`).
- If only `entry_close` is available (bar near end of window), returns `label=+1, best_h=h, fwd_return_pct=0.0`.
- Selects the horizon with maximum `|t-stat|`. Returns `(label, best_h, fwd_return_pct)`.

`label_trades()` signature gains `trend_scan_grid: tuple[int, ...] = (5, 8, 13, 21)`.
When `label_mode == "trend_scanning"`: short-circuits the triple-barrier loop, calls
`_trend_scan_label`, writes label directly. All three `label_mode` values
(`"triple_barrier"`, `"fixed_horizon"`, `"trend_scanning"`) pass through the function;
default `"triple_barrier"` reproduces /059 bit-for-bit. The `trend_scan_grid` parameter
is completely inert when `label_mode != "trend_scanning"`.

### `src/crypto_trade/strategies/ml/lgbm.py`

`LightGbmStrategy.__init__` gains `trend_scan_grid: tuple[int, ...] = (5, 8, 13, 21)`,
stored as `self.trend_scan_grid = tuple(trend_scan_grid)`. Passed to `label_trades`
at `_train_for_month`. Default `(5, 8, 13, 21)` is inert for callers using
`label_mode="triple_barrier"` — no regression.

### `src/crypto_trade/strategies/ml/metalabeling.py`

`MetaLabelingStrategy.__init__` gains `trend_scan_grid: tuple[int, ...] = (5, 8, 13, 21)`,
forwarded to the M1 `LightGbmStrategy` constructor.

### `run_baseline_v3.py`

- `ITERATION_LABEL = "v3-105"` (from `"v3-102"`)
- `common_kwargs` in `_build_v3_model`: added `label_mode="trend_scanning"` and
  `trend_scan_grid=(5, 8, 13, 21)`.
- `_verify_feature_columns` preflight:
  - `expected_label_mode = "trend_scanning"` assertion (was `"triple_barrier"`).
  - New `expected_trend_scan_grid = (5, 8, 13, 21)` assertion.
  - HARD label-leakage gate: `assert max(trend_scan_grid) <= timeout_candles=21`.

## Test Suite

New file: `tests/strategies/ml/test_trend_scanning_label_mode.py`, 8 tests:

| Test | Purpose |
|---|---|
| `test_trend_scanning_labels_in_valid_set` | Labels in {-1, +1} for random price series |
| `test_trend_scanning_hard_causality` | MANDATORY: appending bars beyond max(grid) leaves all earlier labels bit-identical |
| `test_trend_scanning_monotone_up_labels_long` | Strictly increasing series → all +1 |
| `test_trend_scanning_monotone_down_labels_short` | Strictly decreasing series → all -1 |
| `test_triple_barrier_default_unchanged_by_trend_scan_parameter` | Triple-barrier byte-identical with grid passed (inert) |
| `test_trend_scanning_max_grid_leakage_guard` | `max(grid)=21 <= 21` hard assertion; also asserts `best_h in grid` |
| `test_lgbm_strategy_stores_trend_scan_grid` | Default `(5,8,13,21)` stored; custom grid stored as tuple |
| `test_trend_scanning_integration_smoke` | Full `compute_features(master)` + `label_trades` pipeline; both ±1 classes present on IS window |

All 8 pass. Result from previous session run: 8/8 in 0.87s.

Modified: `tests/strategies/ml/test_universe_reselection_v3.py` — `ITERATION_LABEL`
assertion updated `"v3-102"` → `"v3-105"`.

Full test suite: 289/292 passing. 3 pre-existing failures unrelated to iter-v3/105:
- `test_feature_count_15` (expects 15 features per iter-v3/102 spec — count is now 14)
- `test_feature_columns_pinned_for_new_symbols` (same pre-existing count mismatch)
- `test_iter090_runner_feature_count` (XS_BASE_FEATURES count constant)

None of the 3 failures are in the labeling, lgbm, metalabeling, or runner paths touched
by this iteration. No regression introduced by iter-v3/105.

## Pre-Flight Verification (setup-only; to be re-run before backtest)

- **Feature isolation:** `grep -r "from crypto_trade.features " src/crypto_trade/features_v3/`
  must return empty. (Verified clean in previous session; re-run before backtest launch.)
- **Symbol exclusion:** `V3_EXCLUDED_SYMBOLS` disjointness assertion in runner preflight.
  BCH/LDO/TRX are the canonical v3 universe.
- **Label-leakage gap:** `REQUIRED_GAP = (21 + 1) × 3 = 66`. Preflight asserts
  `max(trend_scan_grid)=21 <= timeout_candles=21`. Walk-forward embargo: 22 candles
  (`e149e9d` lookahead fix, inherited unchanged from /059). Trend-scanning mode does not
  touch CPCV, embargo, or walk-forward.
- **Lint:** `uv run ruff check .` and `uv run ruff format .` clean (6 E501 violations fixed
  during implementation; lint was verified clean in commit `a819727`).
- **Data freshness:** must re-verify within 16h before backtest launch. Re-fetch via
  `uv run crypto-trade fetch --interval 8h --symbols BCHUSDT,LDOUSDT,TRXUSDT` if stale.
  Regenerate v3 parquets before launch.

## Smoke Test Results (from implementation session)

Integration smoke (`test_trend_scanning_integration_smoke`): 2000-bar synthetic master,
`compute_features(master)` on 3 symbols, `label_trades` with `label_mode="trend_scanning"`,
IS window (24-month): 30 labeled bars — long=83.3% (+1), short=16.7% (-1). Both ±1 classes
present. Non-degeneracy confirmed.

Hard-causality test (`test_trend_scanning_hard_causality`): label assigned to a bar using
only bars `[t..t+max(grid)]`; appending additional bars beyond `max(grid)` left all 30
earlier labels bit-identical. PASS.

Backward-compat test (`test_triple_barrier_default_unchanged_by_trend_scan_parameter`):
`label_mode="triple_barrier"` with `trend_scan_grid=(5,8,13,21)` passed produces byte-identical
labels to `label_mode="triple_barrier"` without `trend_scan_grid`. PASS.

## Key Metrics Block

Not yet available — backtest has not been run (setup-only dispatch). Metrics will be
produced by the full EXPLORATION run and filed in `reports-v3/iteration_v3-105/`.

## Seed Concentration Audit

Not yet available — pending backtest run.

## Label Leakage Audit

- `REQUIRED_GAP = (21 + 1) × 3 = 66` — unchanged from /059 by design.
- Trend-scanning max horizon `max(grid) = 21` equals triple-barrier timeout = 21.
  No lookahead extension. HARD assertion in preflight: `max(grid) <= timeout_candles`.
- Walk-forward embargo: 22 candles per cell. `train_end_ms = test_start_ms - embargo_ms`
  at `walk_forward.py:113`. The `e149e9d` lookahead fix is intact and untouched.
- `trend_scan_grid` parameter is completely inert for the IS/OOS split, CPCV paths,
  and embargo computation.

## Gate Efficacy Table

The `label_mode` axis does not introduce or modify any live risk gate. The 7 inherited
risk primitives (vol-adjusted sizing, ADX gate, Hurst regime, z-score OOD, drawdown brake,
BTC contagion kill, liquidity floor) plus Primitive 10 (direction-asymmetric BCH LONG block,
committed `9b1293d`) are unchanged from the /059 baseline. Gate fire rates carry forward;
no new gate efficacy table is required for a labeling-geometry-only axis.

## Anomaly Notes

None during setup. Three pre-existing test failures are documented above and confirmed
pre-existing (verified before implementation by `git stash` isolation). No new anomaly
introduced by iter-v3/105.

## Launch Command (EXPLORATION)

```
uv run python run_baseline_v3.py --exploration --clean-oof
```

Estimated wall-clock: ~1.1h (3-seed EXPLORATION, 35 trials/cell, 3 symbols, identical
cell count to iter-v3/101 which ran 0.72h; trend-scanning OLS is O(H·N) per bar with
H=4 and N≤21, negligible overhead vs LightGBM training).

Outputs land at:
- `reports-v3/iteration_v3-105/in_sample/`
- `reports-v3/iteration_v3-105/out_of_sample/`
- `reports-v3/iteration_v3-105/comparison.csv`
- `reports-v3/iteration_v3-105/dsr.json`
- `reports-v3/iteration_v3-105/cpcv_paths.csv`
- `reports-v3/iteration_v3-105/adf_test.csv`
- `reports-v3/iteration_v3-105/ic_matrix.csv`

## Status

OVERALL=READY-FOR-CRITIC (post-backtest — pending backtest execution and metrics)
