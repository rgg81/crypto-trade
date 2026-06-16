# Engineering Report — iter-v1/009 (BTCUSDT) — Phase 6 SETUP

Status: **SETUP COMPLETE — READY FOR FULL K=5 SCREEN** (full backtest run detached by orchestrator).

## Headers
- Iteration: iter-v1/009 (BTCUSDT, single-symbol v1 redesign track)
- Branch: `iteration-v1/redesign-single-symbol`
- Setup commit SHA: `1ccb13a3a1b324d476e16d4cd0512bf721b575f5`
- Hardware: 20 vCPU / 58 GB RAM
- Smoke wall-clock: 35s for the backtest (K=1, n_trials=2); full pipeline (backtest + methodology reporting) ~3 min
- Axis: LABEL-HORIZON (FE Phase 4 PRIMARY) — switch TRAINING label to `fixed_horizon` N=21 (7d)

---

## 1. Execution-consistency decision (the load-bearing QE task)

### 1.1 How the v1 specialist trade EXITS (trace)

The exit path is three engine layers, and `label_mode` touches only the FIRST:

1. **TRAINING label** (`LightGbmStrategy` → `labeling.label_trades`): determines the
   `{-1,0,+1}` class the model learns. In `triple_barrier` mode this is first-hit of the
   ATR TP/SL barriers within the timeout; in `fixed_horizon` mode it is `sign(N-candle
   forward return)` — barriers are NOT scanned (`labeling.py:426` guards the barrier loop
   behind `if not use_fixed_horizon:`). **`label_mode` changes ONLY this.**

2. **Signal emission** (`lgbm.py:2658-2666`, `_predict`): regardless of `label_mode`, the
   emitted `Signal.tp_pct` / `Signal.sl_pct` are computed as
   `tp_pct = NATR × atr_tp_multiplier`, `sl_pct = NATR × atr_sl_multiplier`. This is the
   EXECUTION barrier and is independent of how the model was trained.

3. **Backtest exit** (`backtest.py:create_order` 989-1000 + `check_order` 800-834):
   - `stop_loss_price` / `take_profit_price` derived from `Signal.sl_pct` / `tp_pct`
     (falling back to `BacktestConfig.stop_loss_pct=4%` / `take_profit_pct=8%` only if the
     Signal value is `None`).
   - `timeout_time = open_time + config.timeout_minutes × 60 000`.
   - `check_order` exits on: (1) timeout first, else (2) SL hit (`low ≤ SL`), else (3) TP
     hit (`high ≥ TP`).

**The mismatch this iteration had to resolve:** the FE Sharpe proxy assumes a trade captures
the full ~21-candle forward move ("let winners run"). But with the incumbent
`atr_tp_multiplier=2.9`, the execution TP sits at `NATR × 2.9 ≈ 6.7%` at the median NATR of
2.31% (`vol_natr_21`). A 6.7% TP is hit within a few candles, so a `fixed_horizon`-trained
model would TP early and NEVER realize the 21-candle thesis — the backtest would be a
mismatched, invalid test. **Leaving the 2.9-ATR TP in place voids the test.**

### 1.2 The mechanism chosen: TP made non-binding via a large ATR multiplier

**Decision: `atr_tp_multiplier = 100.0`, `atr_sl_multiplier = 1.45` (unchanged),
`execution_timeout_minutes = 10080` (21 candles = 7d, == the training-label horizon).**

- **Let winners run**: with `tp_pct = NATR × 100`, the TP price sits at ≥ **116.9%** even in
  the lowest monthly-median-NATR month (1.17%). The largest observed 21-candle BTC move over
  the full window is **47.4%** (p99 = 28.5%). The TP is therefore NON-BINDING across the
  entire IS+OOS window → the **7d EXECUTION timeout becomes the binding exit for winners**.
- **Cut losers**: `atr_sl_multiplier = 1.45` is retained → protective stop ≈ 3.3% at median
  NATR. The thesis is deliberately asymmetric: cut losers (SL kept), let winners run (TP
  disabled).
- **Horizon match**: `execution_timeout_minutes == label_timeout_minutes == 10080` (7d) — the
  EXECUTION horizon equals the TRAINING-label horizon, which is exactly the consistency the FE
  Sharpe proxy assumes.

**Why `100×` and not `None`:** setting `atr_tp_multiplier=None` makes the Signal emit
`tp_pct=None`, which `create_order` (`backtest.py:990`) then falls back to
`BacktestConfig.take_profit_pct=8.0%` — a *tighter* fixed TP, the opposite of intended. A
large ATR multiplier is the engine-native way to make the TP non-binding while keeping the
EXACT existing code path — **zero new flags in `backtest.py`, byte-identical for every other
iteration.**

Label-side cleanliness: `use_atr_labeling=False` is set, so the `fixed_horizon` label is purely
`sign(7d forward return)`; the `atr_tp/sl` multipliers never touch the label (`lgbm.py:698`
leaves `_label_atr_values=None`, and `fixed_horizon` ignores barriers regardless). The 100×
multiplier is thus an EXECUTION-only quantity.

---

## 2. Wiring (mirrors the `elif iteration_label == "v1-007":` template)

All changes in `run_baseline_v1.py` (commit `1ccb13a3`). Defaults preserve `/002`–`/007`
byte-identically.

1. **`run_model` new params** (default to current behavior):
   - `use_atr_labeling: bool = True` → threaded to `LightGbmStrategy(use_atr_labeling=...)`
     (was hardcoded `True`).
   - `label_timeout_minutes: int = 10080` → threaded to
     `LightGbmStrategy(label_timeout_minutes=...)` (was hardcoded `10080`).
   - `execution_timeout_minutes: int = 10080` → threaded to
     `BacktestConfig(timeout_minutes=...)` (was hardcoded `10080`). Kept separate from the
     label horizon so the two can be reasoned about independently (they coincide at 7d for /009).

2. **New `_spec_*` override defaults** (in the per-iteration override block, before the keyed
   branches): `_spec_label_mode="triple_barrier"`, `_spec_use_atr_labeling=True`,
   `_spec_label_timeout_minutes=10080`, `_spec_atr_tp=2.9`, `_spec_atr_sl=1.45`,
   `_spec_execution_timeout_minutes=10080`. These are consumed by the universal single-symbol
   routing guard, which previously hardcoded `atr_tp=2.9, atr_sl=1.45` and never passed
   `label_mode`. Now the guard threads all six through `run_model`.

3. **`V1_BTC_ITER009_FEATURES`** — the 19-col HYBRID short+regime set (FE recommended).

4. **`elif iteration_label == "v1-009":` branch** sets:
   `_spec_feature_columns=list(V1_BTC_ITER009_FEATURES)`, `_spec_apply_r2=False`,
   `_spec_label_mode="fixed_horizon"`, `_spec_use_atr_labeling=False`,
   `_spec_label_timeout_minutes=10080`, `_spec_atr_tp=100.0`, `_spec_atr_sl=1.45`,
   `_spec_execution_timeout_minutes=10080`, and prints the override banner.

---

## 3. Feature-column verification (QE task #4)

All 19 columns verified present in `data/features/BTCUSDT_8h_features.parquet`; all NaN% < 3%
(max 2.15% on `btc_funding_spread_30_90`). 16/19 are inside `V1_FEATURE_COLUMNS` (193); **3 are
OUTSIDE**: `ent_shannon_10`, `btc_funding_spread_30_90`, `funding_rate_zscore_30`.

- **Prune-subset discipline does NOT apply** here — this is a hybrid short+regime set, not a
  prune of the 193. The `/002`–`/007` strict-subset assertion is intentionally REPLACED by:
  - a parquet-presence assertion (each of the 19 must exist in the parquet schema), and
  - a funding-outside-193 assertion (both funding cols must be present in the set AND outside
    `V1_FEATURE_COLUMNS`).
- The two funding cols + entropy being outside the 193 is exactly why the
  `active_feature_columns` sync fix (already in the universal guard) is load-bearing — it
  re-points `_write_feature_importance` / `_run_methodology_reporting` (ADF/IC) to the ACTUAL
  19 trained columns, so importance for the funding/entropy features stays auditable (avoids
  the `/005` funding-invisibility bug).

---

## 4. Smoke verification — execution change took effect (QE task #5)

Smoke command (fast: K=1, n_trials=2; informational only — NOT a screen result):
```
PYTHONUNBUFFERED=1 uv run python run_baseline_v1.py \
  --exploration --iteration 9 --symbols BTCUSDT --n-trials 2 --bagging-k 1
```

Override banner (confirms features=19 + fixed_horizon + non-binding TP):
```
[iter-v1/009] OVERRIDE ACTIVE: features=19 (19-col HYBRID short+regime; 16⊆V1_FEATURE_COLUMNS
+ 3 outside: ent_shannon_10/btc_funding_spread_30_90/funding_rate_zscore_30)
| LABEL=fixed_horizon N=21(7d) use_atr_labeling=False
| EXEC atr_tp=100.0(TP NON-BINDING → 7d timeout binds, 'let winners run')
  atr_sl=1.45('cut losers') timeout=10080min(7d) | R2 OFF R1=OFF R3=ON(0.7) R5/vt=ON
```

The model trained and produced 216 trades (149 IS / 67 OOS). The decisive proof is the
**hold-duration + exit-mix shift** vs the incumbent triple-barrier 2.9-ATR execution (the
`/005`–`/007` BTC specialists, same execution barrier as the incumbent):

| run | window | n | mean hold (candles) | median | max | TP exits | SL | timeout |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **BEFORE** /005 | IS | 194 | 10.66 | 9.5 | 21 | **49** | 107 | 38 |
| **BEFORE** /006 | IS | 200 | 10.28 | 9.0 | 21 | **49** | 110 | 41 |
| **BEFORE** /007 | IS | 191 | 10.88 | 10.0 | 21 | **42** | 107 | 42 |
| **AFTER**  /009 | IS | 149 | **12.44** | **12.0** | 21 | **0** | 95 | 54 |
| **BEFORE** /005 | OOS | 83 | 10.28 | 9.0 | 21 | **24** | 46 | 13 |
| **BEFORE** /006 | OOS | 87 | 9.57 | 7.0 | 21 | **19** | 55 | 13 |
| **BEFORE** /007 | OOS | 84 | 9.50 | 7.5 | 21 | **22** | 50 | 12 |
| **AFTER**  /009 | OOS | 67 | **12.04** | **11.0** | 21 | **0** | 46 | 21 |

**Interpretation:** the single cleanest diagnostic is the **complete disappearance of
`take_profit` exits** — the incumbent had 42–49 early TP truncations per IS run (≈22–25% of
trades); /009 has **zero**. Winners now run to the 7d horizon (timeout share rose from ~21% to
36% IS / 31% OOS) or get stopped, never truncating at a TP barrier. Mean hold rose ~10.3–10.9c
→ 12.0–12.4c and the median moved ~9c → 11–12c — materially toward the 21-candle horizon. The
SL at 1.45-ATR still cuts losers (95 IS / 46 OOS). `max=21c` in both before and after is the
timeout cap; the load-bearing signal is the distribution shift + TP elimination. **The
execution-consistency change is confirmed working.**

(Smoke headline metrics at K=1/n_trials=2 are NOT meaningful — they are the placeholder
single-study draw, intentionally not a screen result.)

---

## 5. Exact full-run command for the K=5 screen

`--exploration` resolves to `V1_EXPLORATION_BAGGING_K = 5` (raised 3→5 on 2026-06-16), so a
plain EXPLORATION IS the K=5 screen. Re-fetch + regenerate features first (the worktree's
`data/` extends to 2026-06-15; if launching later, refresh to satisfy the 16h staleness guard):

```bash
# (1) refresh klines + v1 features for BTCUSDT (only if data > 16h stale)
uv run crypto-trade fetch --symbols BTCUSDT --intervals 8h
uv run crypto-trade features --symbols BTCUSDT --interval 8h --track v1 --format parquet --workers 4

# (2) full K=5 EXPLORATION screen (n_trials=18 = v1 SPECIALIST standard)
PYTHONUNBUFFERED=1 uv run python run_baseline_v1.py \
  --exploration --iteration 9 --symbols BTCUSDT --n-trials 18 \
  > reports-v1/BTCUSDT/iteration_v1-009/run.log 2>&1
```

Notes for the full run:
- The runner's `--n-trials` CLI default is 50; the v1 SPECIALIST standard is **18** (per
  `feedback_v1_trial_budget_standardization`), so pass `--n-trials 18` explicitly. (Use 50 only
  if you want to match the BASELINE_V1 anchor budget; the FE bounds region — `v1_pruned` — is
  designed to resist over-fitting at higher budgets, but 18 is the cadence-standard EXPLORATION
  budget.)
- The universal single-symbol guard uses `bounds_profile="v1_specialist"` (the established
  single-symbol convention); the FE report named `v1_pruned`. /009 does NOT change the bounds
  profile — flagged here for the QR/Critic to confirm against the brief if the brief pins a
  specific profile.
- This final run will produce `engineering_report.md` complaint at the gate (it now exists, so
  the gate passes); the FATAL seen in the smoke was only because the report had not been written
  yet at smoke time.

---

## 6. Anomaly notes
- Smoke produced `total_net_pnl` IS +1.97% / OOS −34.84% — these are the K=1/n_trials=2
  placeholder-study draw and carry NO information about the screen outcome. The screen is K=5
  bagging at n_trials=18.
- No NaN Sharpe, no zero-trade months in IS, no crashes. The 35s backtest + full methodology
  reporting (ADF/IC/DSR/basin diagnostics) all ran clean.

## Status
OVERALL=READY-FOR-FULL-SCREEN (SETUP ONLY — orchestrator runs the detached K=5 backtest;
post-run report addendum + Phase 7.5 Critic dispatch follow the screen).
