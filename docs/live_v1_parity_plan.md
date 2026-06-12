# Live V1 Bundle-002 Parity Plan

Branch: `live/v1-bundle-parity`
Worktree: `/home/roberto/crypto-trade/.worktrees/live-v1-parity`
Based on: quant-research `d2a17bd3` (iter-v1/082 BUNDLE-002 merge commit, tag `v0.v1-082`)

---

## IMPORTANT: Live Engine Isolation

The main checkout `/home/roberto/crypto-trade` is running a **LIVE TESTNET ENGINE**
(`--track all` = legacy v1 / v2 / v3) on branch `quant-research`. Presence confirmed by
`/home/roberto/crypto-trade/logs/testnet_engine.log` and
`/home/roberto/crypto-trade/data/testnet.db`.

**DO NOT edit or commit into `/home/roberto/crypto-trade`** while the engine is running.
This worktree (`/home/roberto/crypto-trade/.worktrees/live-v1-parity`) is fully isolated:
it has its own `.venv`, its own empty `data/` directory, and its own git HEAD. The
cutover of the BUNDLE-002 specialists into the live engine is a **manual step deferred
to Phase 4** — after trade-level AND signal-level reconciliation are complete.

---

## Goal

Reproduce the BUNDLE-002 backtest (tag `v0.v1-082`) field-by-field in the live engine and
gate on BOTH:

1. **Trade-level reconciliation** — closed trades in a seeded live DB match
   `reports-v1/iteration_v1-082/{in_sample,out_of_sample}/trades.csv` within tolerance
   5e-4 on all numeric fields.
2. **Signal-level reconciliation** — per-candle get_signal() output (50 per-seed votes,
   _final_signed, _ensemble_std, _sp_confidence, R3 OOD distance, vt_scale, r2_scale,
   direction, weight, tp_pct, sl_pct) matches between the backtest path and the live
   engine path.

User decisions (locked, not revisited):
- Do not chase thread/float-sum determinism — trust the seeding.
- Reconcile against FRESHLY-REGENERATED fixed-code CSVs (the ~10h regen is Phase 2).
- Gate on BOTH trade-level AND signal-level parity.

---

## BUNDLE-002 Exact Configuration

Confirmed from `run_baseline_v1.py` dispatch branches + `src/crypto_trade/features_v1/__init__.py`.

| Specialist | Symbol | Seeds | ENSEMBLE_SIZE | n_trials | Features | ATR TP/SL | Risk |
|---|---|---|---|---|---|---|---|
| V1-DOT (/063) | DOTUSDT | 50 (42..91) | 1 per study | 30 | 48 PRUNED | 3.5/1.75 | R1+R2+R3 |
| V1-ETH (/064) | ETHUSDT | 50 (42..91) | 1 per study | 30 | 48 PRUNED | 2.9/1.45 | R3 only |
| V1-BTC (/065) | BTCUSDT | 50 (42..91) | 1 per study | 30 | 48 PRUNED | 2.9/1.45 | R3 only |
| V1-AAVE (/078) | AAVEUSDT | 50 (42..91) | 1 per study | 30 | 49 PRUNED+excess | 2.9/1.45 | R3 only |

Common: `specialist_mode=True`, `bounds_profile='v1_pruned'`, `max_depth=5 FIXED`,
`num_leaves=31 FIXED`, `n_startup_trials=10`, `n_estimators_max=500`,
`aggregator=mean-of-signed-weights`, `cooldown_candles=2`, `training_months=24`,
`OOS_CUTOFF_DATE=2025-03-24`, `ood_cutoff=0.70`, `V1_OOD_FEATURE_COLUMNS` (16 features),
`features_dir='data/features'`.

R1 (DOT only): `risk_consecutive_sl_limit=3`, `risk_consecutive_sl_cooldown_candles=27`.
R2 (DOT only): `risk_drawdown_scale_enabled=True`, trigger=7%, anchor=15%, floor=0.33.

---

## AAVE Feature: excess_ret_5d_vs_majors_z90

**Status: RESTORED IN CODE** (commit `550829f7`, Phase 1a).

This feature was added at iter-v1/078 (commit `21cdbf5e`) then reverted when quant-research
diverged. It is **absent** from the quant-research base — confirmed by the orchestrator before
this worktree was created. Phase 1a grafted the exact implementation from `21cdbf5e` onto the
current `cross_btc_v1.py` without wholesale reverting the file.

**Definition:**
- `ret_window_bars = 15` (15 bars = 5 days at 8h interval)
- `sym_ret_5d = close.pct_change(15)`
- `excess = sym_ret_5d - 0.5*btc_ret_5d - 0.5*eth_ret_5d`
- z-score over 90 bars (rolling std, ddof=1), clipped ±10, NaN warm-up filled 0.0
- Column name: `excess_ret_5d_vs_majors_z90`
- Code: `src/crypto_trade/features_v1/cross_btc_v1.py` —
  `compute_excess_ret_5d_vs_majors_z90()` + `_load_eth_aligned()` helper +
  universal dispatch in `add_cross_btc_v1_features` (writes column to ALL symbols' parquets
  harmlessly; non-AAVE symbols carry it but the PRUNED feature list ignores it).

**Constant placement:**
- `V1_FEATURE_COLUMNS_PRUNED` stays at 48 cols — other 3 specialists unaffected.
- `V1_ITER078_FEATURE_COLUMNS = tuple(V1_FEATURE_COLUMNS_PRUNED) + ('excess_ret_5d_vs_majors_z90',)`
  = 49 cols, AAVE specialist only.
- Both constants are in `src/crypto_trade/features_v1/__init__.py`.

**Verification:** 7 tests in `tests/test_excess_ret_5d_vs_majors_z90.py` (4 unit + 3
parquet-level, the parquet-level ones skip until Phase 2 regen).

---

## Live Engine Wiring

**Status: COMPLETE** (Phase 1b, commit `6f8619bb`).

`src/crypto_trade/live/models.py`:
- `BUNDLE_002_MODELS: tuple[ModelConfig, ...]` — 4 ModelConfigs for DOT/ETH/BTC/AAVE,
  constructed lazily via `_build_bundle_002_models()`.
- Each ModelConfig mirrors the exact fields from the runner dispatch: specialist_mode,
  seed_count, optuna_trials, n_startup_trials, n_estimators_max, bounds_profile, feature_columns,
  ood_enabled/features/cutoff, R1/R2 params, atr multipliers.

`src/crypto_trade/main.py`:
- Track map at line 931: `"v1-bundle": BUNDLE_002_MODELS`.
- Launch: `uv run crypto-trade live --testnet --track v1-bundle --amount 100 --leverage 1`
- The `"v1"` track retains `BASELINE_MODELS` (legacy v0.186 pattern) — NOT repurposed.

---

## Reconciliation Harnesses

**Status: SCAFFOLDED** (Phase 1c, commit `1bf00178`).

### Trade-level: `scripts/reconcile_full_oos.py`

Extended with `--track v1-bundle` mode (flag `--v1-bundle-trades <path>`) that:
- Reads live DB closed trades for `V1-{DOT,ETH,BTC,AAVE}` models.
- Reads `/082` IS+OOS CSVs from `reports-v1/iteration_v1-082/`.
- Compares field-by-field: `symbol`, `direction`, `open_time`, `close_time`, `entry_price`,
  `exit_price`, `pnl_pct`, `weighted_pnl_pct`, `weight_factor`, `exit_reason` with tol=5e-4.
- `end_of_data` → `timeout` exception allowed (data extent artifact).
- Reports: match rate, first N mismatches, per-symbol summary.

### Signal-level: `tests/live/test_backtest_parity_bundle002_signal.py`

Per-candle harness that, given an identical trained model + identical injected candle/state,
asserts bit/eps equality between backtest `get_signal()` and live runner signal for:
- 50 per-seed signed votes (exact list equality)
- `_final_signed` (rtol 5e-4)
- `_ensemble_std` (rtol 5e-4)
- `_sp_confidence` (rtol 5e-4)
- R3 `ood_distance` vs `ood_cutoff` (rtol 5e-4), pass/fail gate
- `vt_scale` (rtol 5e-4)
- `r2_scale` (rtol 5e-4) — DOT specialist only
- `Signal.direction` (exact)
- `Signal.weight` (exact)
- `Signal.tp_pct`, `Signal.sl_pct` (rtol 5e-4)

All tests are `xfail` until Phase 2 regen is complete. `PHASE3_PROBE_PLAN` is an empty
list placeholder — populated in Phase 3 from real `open_time_ms` values in `/082` trade CSVs.

---

## Phase Plan

### Phase 1 — Code Setup (NO regen) — COMPLETE on this branch

- Phase 1a: Restore `excess_ret_5d_vs_majors_z90` feature + `V1_ITER078_FEATURE_COLUMNS` (commit `550829f7`)
- Phase 1b: Wire `BUNDLE_002_MODELS` + `v1-bundle` track (commit `6f8619bb`)
- Phase 1c: Scaffold reconciliation harnesses (commit `1bf00178`)
- Phase 1d: Fix `BASELINE_V1.md` doc accuracy (50-seed correction, AAVE code reference) + write this plan doc (this commit)

### Phase 2 — Data Regen (~10h, NOT this workflow)

Regen commands (to be run by orchestrator — see Phase 2 Command Sequence below):

```bash
cd /home/roberto/crypto-trade/.worktrees/live-v1-parity
export PATH="$HOME/.local/bin:$PATH"

# Step 1: fetch fresh klines (BTC + ETH needed for cross-asset feature)
uv run crypto-trade fetch \
  --symbols BTCUSDT,ETHUSDT,DOTUSDT,ETHUSDT,BTCUSDT,AAVEUSDT \
  --intervals 8h

# Step 2: regenerate v1 feature parquets (all 4 specialist symbols + BTC + ETH for cross-asset)
uv run crypto-trade features \
  --symbols DOTUSDT,ETHUSDT,BTCUSDT,AAVEUSDT \
  --interval 8h --track v1 --format parquet --workers 4

# Step 3: run full BUNDLE-002 backtest (~10h; produces /082 reports)
uv run python run_baseline_v1.py --iter-v1-082
```

Wall-clock estimate: fetch ~5min, features ~10-20min, backtest ~8-10h (50 seeds × 30 trials × 4 specialists × ~24 months × 2 windows).

### Phase 3 — Signal-Level Parity Test

1. Populate `PHASE3_PROBE_PLAN` in `tests/live/test_backtest_parity_bundle002_signal.py`
   from the freshly-generated `/082` trade CSVs.
2. Run: `uv run pytest tests/live/test_backtest_parity_bundle002_signal.py -v -s`
3. All xfail tests flip to unconditional assertions.

### Phase 4 — Trade-Level Reconciliation + Live Cutover

1. Seed live DB from fresh `/082` trades CSVs.
2. Run reconciler: `uv run python scripts/reconcile_full_oos.py --track v1-bundle`
3. Gate: zero divergences outside `end_of_data` → `timeout` exception.
4. Manual cutover: stop legacy `--track all` engine, restart with `--track v1-bundle`
   (or `--track both` if v2/v3 are also desired).

---

## 50-Seed Confirmation

Confirmed by reading `run_baseline_v1.py` dispatch (lines 6847-6960 for /063, 6975-7127
for /065, 7140-7313 for /064, 7313+ for /078) and `src/crypto_trade/features_v1/__init__.py`
docstrings:

- `V1_SPECIALIST_SEED_COUNT = 50`
- `V1_SPECIALIST_OPTUNA_TRIALS = 30`
- `V1_SPECIALIST_SEEDS` = range(42, 92) [42..91 inclusive]
- `ENSEMBLE_SIZE = 1` per study (`specialist_mode=True` overrides ensemble aggregation)

This applies to ALL FOUR specialists: DOT (/063), ETH (/064), BTC (/065), AAVE (/078).
The BASELINE_V1.md table previously showed "5 inner seeds [42,123,456,789,1001]" and
"n_trials=18" for DOT/ETH/BTC — those were doc bugs from the pre-SPECIALIST methodology.
Fixed in Phase 1d.
