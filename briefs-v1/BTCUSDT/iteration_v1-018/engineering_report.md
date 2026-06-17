# Engineering Report — iter-v1/018 (BTCUSDT) — Phase 6 SETUP (gate wiring; full backtest NOT yet run)

## Headers
- Iteration: iter-v1/018 — TREND-STRENGTH CONVICTION entry gate (single-axis vs /016)
- Symbol: BTCUSDT (single-symbol v1 track)
- Branch: iteration-v1/redesign-single-symbol
- Setup commit SHA: dd2db88cc08f675ca6dfa1ce5262aa0ccbf0d5ec
- Type: SPECIALIST / EXPLORATION (per brief §7 cadence)
- Risk declaration: NORMAL-RISK (brief §2.5 — stateless RULE-layer entry filter; the
  Optuna training-objective domain and the direction rule are UNCHANGED)
- Status: SETUP-ONLY — src + test wired, lint-clean, look-ahead test passes,
  gate-fires smoke confirmed. The full K=5 EXPLORATION backtest is launched by the
  orchestrator (detached), then this report's metric block is filled.

## What was wired (single axis vs iter-016)
iter-018 = the ENTIRE iter-016 stack + ONLY `enable_trend_strength_gate=True`.
Everything else (19-col HYBRID `V1_BTC_ITER009_FEATURES`, `fixed_horizon` N=42 (14d),
let-winners-run exec `atr_tp=100.0`/`atr_sl=1.45`/14d timeout, R2 brake
trigger=2.07/anchor=8.28/floor=0.20, R3 OOD 0.70, R5 vol-target, stateless 200-SMA
trend-state DIRECTION override) is BIT-IDENTICAL to /016. R1 OFF.

The gate, applied AFTER the abstention gates + trend-state direction override decide a
trade fires:
```
trend_strength(t) = |close[t-1] - SMA200(close)[t-1]| / ATR14[t-1]      # past-only
fire(t)           = trend_strength(t) >= q_thr                          # else ABSTAIN
q_thr             = quantile(|dist_atr| over the TRAINING window, q=0.50)
```
`q_thr` is recomputed at each `_train_for_month` from the training-window rows ONLY
(open_time in `[train_start_ms, train_end_ms)`), mirroring the R3 OOD
training-window-stat pattern — fit on PAST rows, never recomputed on test rows.

## Insertion points (commit dd2db88c)
`src/crypto_trade/strategies/ml/lgbm.py`:
- `__init__` params (~L323): `enable_trend_strength_gate=False`,
  `trend_strength_atr_window=14`, `trend_strength_quantile=0.50` (default False).
- Instance attrs (~L545): `_enable_trend_strength_gate`, `_trend_strength_atr_window`,
  `_trend_strength_quantile`, `_trend_strength_idx`, `_trend_strength_thr`.
- `compute_features()` (~L816): builds sorted `(open_time_ms, |dist_atr|)` index from the
  trend-state symbol parquet's close/high/low with `.shift(1)` SMA200 + `.shift(1)` ATR14
  (simple rolling-mean true range, NOT Wilder) — EXACTLY the QR script's `absd`. FAIL-LOUD
  if the parquet is missing.
- `_train_for_month()` specialist block (~L1816): per-month `q_thr` from training-window
  rows; `< 50` finite rows → `None` (gate inert that month → conservative fire).
- `_compute_trend_strength(open_time)` (~L2356): exact-open_time-match lookup of `|dist_atr|`
  at row t; `None` on warmup/NaN/missing.
- `get_signal()` specialist path (~L2797): gate AFTER the trend-state override; below
  threshold → `NO_SIGNAL` + `trend_strength_gate_skip` decision-log event. `None` strength
  or `None` thr → fire.

`run_baseline_v1.py`:
- `run_model()` signature (~L635) + `LightGbmStrategy(...)` construction (~L811): 3 params
  threaded (default False).
- CLI flags (~L2836): `--enable-trend-strength-gate` / `--trend-strength-atr-window` /
  `--trend-strength-quantile`.
- `_spec_*` defaults (~L3763) + `v1-018` keyed override branch (= /016 config + 3 gate
  params) + CLI precedence hook + generic single-symbol dispatch threading (~L4448).
- Backtest-mode `decision_log.configure()` in the generic specialist dispatch (~L4433),
  gated to RULE-layer gates active → captures the skip events for Phase 7 attribution.

`tests/test_trend_strength_lookahead.py`: NEW (11 tests).

## Look-ahead test result (MANDATORY)
`tests/test_trend_strength_lookahead.py` — 11 tests PASS. Protects:
1. The compute_features `(open_time, |dist_atr|)` index matches an independent manual
   past-only reference at every row.
2. `_compute_trend_strength(open_time)` equals the manually-sliced past-only `|dist_atr|`.
3. APPENDING future candles (open_time > decision) does NOT change a past row's value.
4. Mutating the decision candle's OWN close/high/low does NOT change its strength
   (every primitive is `.shift(1)`-lagged).
5. Mutating `close[t-1]` DOES change it (confirms it is the live input — the alignment is
   correct, no double-lag with the direction override).
6. Warmup (SMA/ATR undefined) → `None` → caller does NOT gate (conservative fire).
7. The per-month threshold uses ONLY training-window rows (rows after the window mutated
   to extremes do not change `q_thr`) → past-only, leak-free.

Mandated suite — `uv run pytest tests/test_trend_strength_lookahead.py
tests/test_trend_state_lookahead.py tests/test_lookahead_embargo.py tests/test_backtest.py -q`
→ **116 passed**.

## Byte-identical-when-disabled proof
- Source diff is ADD-ONLY for `lgbm.py` and `run_baseline_v1.py` (no deletions; 372
  insertions total). No existing line changed.
- `enable_trend_strength_gate` defaults False in `LightGbmStrategy.__init__`, `run_model`,
  and `_spec_enable_trend_strength_gate`. Both new code paths (compute_features index build,
  get_signal gate) are wrapped in `if self._enable_trend_strength_gate:` → strict no-op
  when disabled. `_trend_strength_idx` / `_trend_strength_thr` stay `None`.
- `test_disabled_by_default_no_index_built` asserts default construction leaves the index
  None and `_compute_trend_strength` returns None.
- No v2/v3 source touched (`git diff --name-only` shows no `features_v2`/`features_v3`/
  `validation_v2`/`validation_v3`/`run_baseline_v2`/`run_baseline_v3`). v2/v3 construct
  `LightGbmStrategy` without the flag → unchanged.
- `grep -rn trend_strength src/crypto_trade/features_v2/ src/crypto_trade/features_v3/` → none.

## Smoke verification — gate FIRES and reduces trades (K=2, n_trials=2)
Ran iter-018 (gate ON) vs an iter-016 control (gate OFF), identical K=2 / n_trials=2, on the
pinned BTCUSDT parquet (7073 rows; 1346 OOS rows == the QR script's `OOS_CANDLES_APPROX`).
Banner confirmed `TREND-STRENGTH GATE ON (atr_window=14 quantile=0.5; past-only median)`,
index loaded (6873 finite |dist_atr| rows), per-month q_thr ≈ 5.16–5.62 from training-window
rows.

| run | IS trades | OOS trades |
|---|---:|---:|
| iter-016 control (gate OFF) | 125 | 58 |
| iter-018 (gate ON)          | 64  | 35 |
| **reduction**               | **-48.8%** | **-39.7%** |

The gate removes ~half of IS candles — consistent with a q=0.50 (median) conviction
threshold skipping the weak-trend half. `trend_strength_gate_skip` events: **1531**.
Correctness invariant: **0 of 1531 skips violate `trend_strength < q_thr`** — every skipped
candle was below its month's past-only threshold.

Example skips (decision_log):
```
ot=2022-02-05 00:00  strength=2.8851 < thr=5.3153  dir_pre_gate=-1  skipped:weak_trend_chop
ot=2022-02-07 00:00  strength=1.7938 < thr=5.3153  dir_pre_gate=-1  skipped:weak_trend_chop
ot=2022-02-07 08:00  strength=1.4247 < thr=5.3153  dir_pre_gate=-1  skipped:weak_trend_chop
```
(The K=2 smoke report dirs were throwaway; the iter-016 committed report was restored and
the iter-018 K=2 dir removed. The real K=5 run produces the merge artifacts.)

Note on threshold magnitude: q_thr (~5.2–5.6) is the EXPANDING training-window median of
|dist_atr|, which is higher than the QR script's per-sub-period median — this is the correct
leak-free per-month past-only behavior the brief §7.3 specified (mirror R3 OOD
training-window-stat), not a discrepancy. The trade-count reduction confirms the median
split fires as designed.

## Risk note — live `_tick` parity
Default `enable_trend_strength_gate=False` keeps the live engine `_tick` path
byte-identical for v2/v3 and /002–/017. When enabled (iter-018 cell only), the gate reads
the SAME `(open_time, |dist_atr|)` past-only index in backtest and live (no exchange/clock
state), and uses the SAME `close[t-1]` the trend-state DIRECTION override already reads —
so backtest and live compute an identical skip decision. The per-month `q_thr` is rebuilt
from the training window at each month-train (the existing lazy-retrain hook), matching the
backtest's `_train_for_month`.

## Anomaly notes
- `[FATAL] engineering_report.md NOT FOUND` at the END of the smoke run is the expected
  end-of-pipeline deliverable guard (the run produced trades + reports first, exit 0). Not
  a backtest error; this report satisfies it for the real run.
- Pre-existing E501 lint warnings at run_baseline_v1.py:4129/4171/4181/4287-4289 are in the
  v1-013/016/017 branches (confirmed present in the committed file BEFORE my changes); not
  touched (out-of-scope for this single-axis change). All MY added lines are lint-clean.

## Exact full EXPLORATION (K=5) command — for the detached launch
```
PYTHONUNBUFFERED=1 uv run python run_baseline_v1.py \
  --exploration --iteration 18 --symbols BTCUSDT --n-trials 18 \
  > reports-v1/BTCUSDT/iteration_v1-018/run.log 2>&1
```
- `--exploration` resolves `bagging_k = V1_EXPLORATION_BAGGING_K = 5` (raised 3→5 on
  2026-06-16; brief §7 "K=3 screen" predates the constant bump — the runner is
  authoritative). ENSEMBLE_SIZE=1, outer seeds=1.
- `--iteration 18` keys the `v1-018` override branch (= /016 config + the 3 gate params;
  prints `[iter-v1/018] OVERRIDE ACTIVE … TREND-STRENGTH GATE ON`).
- `--n-trials 18` = the v1 SPECIALIST default (per cycle-7 budget). If the QR wants the
  BASELINE_V1-anchored budget instead, use `--n-trials 50` (runner default). Reports land
  under `reports-v1/BTCUSDT/iteration_v1-018/{in_sample,out_of_sample}/`; the decision_log
  (with the gate-skip events) at `reports-v1/BTCUSDT/iteration_v1-018/decision_log.jsonl`.

PRIMARY RISK to verify on the real run (brief §4): the let-run 14d book holds ~42 candles,
so the INDEPENDENT OOS trade count is well below the ~571 firing-row estimate. v1 specialist
floor is ≥50 OOS trades. If the K=5 run comes in < 50 OOS, the brief's pre-registered
fallback is q=0.40 (est. firing 676) or q=0.30 (800) — both still IS-stable.

## Status
OVERALL=SETUP-COMPLETE — awaiting detached K=5 backtest. (Metric block / seed-concentration
/ gate-efficacy tables to be filled post-run before READY-FOR-CRITIC.)
