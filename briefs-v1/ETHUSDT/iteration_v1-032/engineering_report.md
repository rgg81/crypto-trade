# Engineering Report — iter-v1/032 (ETHUSDT) — SETUP-ONLY

## Headers
- Iteration: iter-v1/032 (EXPLORATION, single-symbol ETHUSDT)
- Track: v1 (refactored single-symbol)
- Branch: iteration-v1/redesign-single-symbol
- Parent commit SHA at setup: a7aad22781affe73b28eb3fbc1f19ef89b680de1
- Scope: SETUP-ONLY. NO backtest run (orchestrator launches it). NO git commit (orchestrator commits).
- Edge: NEW deterministic SHORT-HORIZON MEAN-REVERSION fade (replaces trend-state direction;
  16h N=2 hold; high-vol-conditioned z-fade). Reuses the iter-026/027 deterministic-direction
  + LightGBM-head (abstention/sizing only) architecture.

## Files changed (with line ranges)

### src/crypto_trade/strategies/ml/lgbm.py (+394 lines)
- L377-409 — NEW constructor params: `enable_reversion_dir=False`, `reversion_z_window=10`,
  `enable_reversion_trigger_gate=False`, `reversion_z_threshold=1.5`,
  `reversion_natr_quantile=0.40`, `reversion_natr_col="vol_natr_14"`. All default-off.
- L671-704 — `self.` attribute storage + index/threshold slots
  (`_reversion_close_idx`, `_reversion_natr_idx`, `_reversion_natr_thr` all init None).
- L943-983 — `compute_features()`: build the sorted (close_time, close) reversion close index
  from the `trend_state_symbol` parquet (STRUCTURALLY IDENTICAL to the /016 trend-state close
  index). FAIL-LOUD if parquet missing.
- L985-1043 — `compute_features()`: build the (open_time, natr[t-1]) vol-gate index from the
  parquet `vol_natr_14` column, `.shift(1)`-lagged (mirrors the /018 trend-strength gate index).
  FAIL-LOUD if parquet or natr column missing.
- L2196-2225 — `_train_for_month()` (specialist path): per-month PAST-ONLY natr q40 threshold
  `_reversion_natr_thr` over the training-window natr[t-1] rows (mirrors trend-strength/funding
  thresholds). < 50 finite training rows → thr None → gate ABSTAINS (CONSERVATIVE).
- L2735-2784 — `_reversion_price_z(open_time)`: past-only z = (close[t-1] − SMA10[t-1]) /
  std10[t-1], std ddof=1 (matches pandas `rolling(10).std()`); searchsorted past-only lookup
  identical to `_compute_trend_state`; None on warmup / degenerate std / NaN.
- L2786-2806 — `_compute_reversion_state(open_time)`: returns `-sign(price_z)` (fade) or None.
- L2808-2832 — `_compute_reversion_natr(open_time)`: past-only natr[t-1] via open_time-keyed
  searchsorted equality; None when undefined.
- L3301-3358 — `get_signal()` specialist path: REVERSION DIRECTION override (mirrors the /016
  trend-state override; keeps model weight/conf/TP/SL, replaces SIGN; logs
  `kind="reversion_state_override"`). Inert this iter only if warmup → keeps model sign.
- L3429-3483 — `get_signal()` specialist path: REVERSION TRIGGER + VOL-REGIME entry gate.
  ENTER iff `|price_z| >= 1.5` AND `natr[t-1] >= q40` with finite calibrated values; else
  ABSTAIN (return NO_SIGNAL). CONSERVATIVE = ABSTAIN (opposite of the trend-strength gate's
  conservative-fire). Logs `kind="reversion_trigger_gate_skip"` with the abstain reason.

### src/crypto_trade/strategies/ml/metalabeling.py (+17 lines) — symmetry, default-off
- L334-347 — NEW M1-forwarded reversion params (default off; iter-032 takes the generic
  run_model path so this M2 path is NOT exercised).
- L437-446 — forward the 6 reversion params into the inner LightGbmStrategy.

### run_baseline_v1.py (+149 lines)
- L680-685 — `run_model()` signature: 6 NEW reversion params (default off).
- L869-876 — `run_model()` LightGbmStrategy construction: thread the 6 reversion params.
- L953-959 — `run_meta_model()` signature: 6 NEW reversion params (default off, symmetry).
- L440-446 (metalabeling, above) reached via run_meta_model's MetaLabelingStrategy build.
- L3961-3973 — `_spec_*` defaults block: 6 NEW `_spec_reversion_*` vars (strict NO-OP for
  /002–/031 → byte-identical).
- L4968-5063 — NEW `elif iteration_label == "v1-032" and len(symbols)==1 and symbols[0]=="ETHUSDT":`
  keyed config branch (mirrors the v1-027 ETH branch style; single-symbol ETH guard). Sets
  the full iter-032 config (see below). Prints an `[iter-v1/032]` banner.
- L5205-5212 — decision_log persistence condition extended to fire on reversion enablement.
- L5372-5377 — run_meta_model dispatch: thread reversion `_spec_*` (symmetry; not exercised).
- L5457-5463 — generic run_model dispatch (the path iter-032 takes): thread reversion `_spec_*`.

### tests/test_reversion_state_lookahead.py (NEW, 18 tests)
Mirrors tests/test_trend_state_lookahead.py; the critical past-only safety gate.

## iter-032 config resolved by the v1-032 branch
- Label: `fixed_horizon`, `use_atr_labeling=False`, `label_timeout_minutes=960` (N=2 = 16h),
  `execution_timeout_minutes=960`.
- Execution: `atr_tp=100.0` (NON-BINDING → 16h timeout binds), `atr_sl=1.45`.
- Direction: `enable_reversion_dir=True`, `reversion_z_window=10`, `trend_state_symbol=ETHUSDT`.
  `enable_trend_state_dir=False`, `enable_trend_strength_gate=False` (mutually exclusive).
- Reversion gate: `enable_reversion_trigger_gate=True`, `reversion_z_threshold=1.5`,
  `reversion_natr_quantile=0.40`, `reversion_natr_col=vol_natr_14`.
- Features: 19-col `V1_BTC_ITER009_FEATURES` (asserted ==19; parquet-exists + col-presence
  checks like v1-027; extra check for close/close_time/open_time/vol_natr_14).
- Risk: R2 ETH-calibrated ON (`_spec_apply_r2=True`, trig 4.07 / anchor 16.27 / floor 0.20),
  R3=ON 0.70 (BASELINE_OOD_CUTOFF_PCT), R5 vt_target_vol=0.3, R1 OFF. M2 OFF (generic run_model).
- Routing: `--iteration 32` → `iteration_label="v1-032"`; the universal single-symbol guard
  (`(exploration|confirmation) and len(set(symbols))==1`) dispatches via `run_model`.

## Test results
- NEW: `tests/test_reversion_state_lookahead.py` — 18 passed (0.97s).
  - Direction matches `-sign(manual z)` (uptrend→-1, downtrend→+1, full path).
  - Appending future candles does NOT change dir/z (the binding look-ahead test).
  - Decision candle's own bar never used; close[t-1] is the live input (z=0 boundary flip).
  - Warmup (<10 closes) → None; exactly-W history not warmup; degenerate std==0 → None;
    NaN close → None; index None → None.
  - Default-off byte-identity: no reversion index built, all reversion methods return None.
  - Gate: natr index is `.shift(1)` past-only; appending future doesn't change natr[t-1];
    natr warmup → None; per-month q40 threshold uses ONLY training-window rows (mutating
    future rows doesn't change it).
- Regression: `tests/test_trend_state_lookahead.py tests/test_trend_strength_lookahead.py
  tests/test_agreement_scale_lookahead.py tests/test_metalabel_lookahead.py` — 42 passed.
- Combined re-run post-format: 60 passed.

## Default-off byte-identity proof
- All 6 new LightGbmStrategy params default False/inert; `_reversion_close_idx`,
  `_reversion_natr_idx`, `_reversion_natr_thr` init None and are built ONLY when the flags
  are True. No prior iteration (/002–/031, v2/v3) sets them → those paths are untouched.
- `test_default_off_byte_identity` asserts: `_enable_reversion_dir is False`,
  `_enable_reversion_trigger_gate is False`, all indices/threshold None, and all three
  reversion methods return None on a default-constructed strategy.
- run_baseline_v1.py: 43 E501 lint findings at HEAD AND 43 current (identical count) — all in
  PRE-EXISTING branch regions; ZERO new lint errors introduced. The v1-032 branch (L4968+) is
  fully under 100 cols.

## Lint + compile
- `ruff check` CLEAN on lgbm.py, metalabeling.py, tests/test_reversion_state_lookahead.py.
- run_baseline_v1.py: only pre-existing E501s (43, unchanged vs HEAD); no new findings.
- `ruff format` applied to lgbm.py + test file (whitespace/wrap only); both re-lint clean and
  all 60 look-ahead tests still pass.
- `python -m py_compile` OK on all four files.

## Construction smoke test
- LightGbmStrategy built with the exact iter-032 reversion params: flags wired correctly,
  trend-state OFF, indices None pre-compute_features.
- MetaLabelingStrategy accepts the 6 reversion kwargs (symmetry; default off).

## vol_natr_14 coverage check (gate calibratability)
- ETHUSDT parquet: 7073 rows; 7060 finite `vol_natr_14`; 7059 finite after `.shift(1)`
  (warmup = first 14 candles only). IS rows (open_time < OOS cutoff 1742774400000) = 5727.
  Each 24-month training window has thousands of finite natr[t-1] rows ≫ the ≥50 floor → the
  per-month q40 vol gate is calibrated every month.

## Wiring ambiguity notes (for QR/Critic)
1. **natr column choice.** The brief defines `natr[t-1] = ATR14[t-1]/close[t-1]`. The V1
   parquet exposes `vol_natr_14` (= ATR14/close), `vol_natr_7`, `vol_natr_21`. I used
   `vol_natr_14` (the ATR14 match) via `reversion_natr_col="vol_natr_14"`. The parquet column
   is per-candle (data through candle t's close); the gate index applies `.shift(1)` so row t
   reads natr[t-1] — past-only, consistent with the brief's `natr[t-1]`. (The execution-TP/SL
   path independently uses `atr_column=vol_natr_21`, the runner default — unchanged.)
2. **std window ddof.** The brief says `std10 = rolling(10).std`. Pandas `rolling.std()`
   default is sample std (ddof=1); I matched that (`np.std(window, ddof=1)`). The look-ahead
   test reference uses the same ddof=1.
3. **z=0 boundary.** `-sign(0)` is undefined; I follow the convention `price_z > 0 → -1 else +1`
   (fade-long on exact-zero), identical to the trend-state `close_prev > sma_prev` boundary.
4. **Two flags vs one.** Per brief §3 I implemented `enable_reversion_dir` (direction) and
   `enable_reversion_trigger_gate` (entry gate) as separate flags; the v1-032 branch turns BOTH
   on (the gate is ON when the direction is ON, per the brief). Direction-only runs are possible
   for diagnostics but are not this iteration's config.

## Launch command (orchestrator runs this — NOT run here)
```
PYTHONUNBUFFERED=1 uv run python run_baseline_v1.py --exploration --iteration 32 \
  --symbols ETHUSDT --n-trials 18 --slippage-bps 2 --no-engineering-report
```

## Status
OVERALL=SETUP-COMPLETE — tests green (18 new + 42 regression = 60), lint+compile clean on
edited files, default-off byte-identity proven. Ready for orchestrator to launch the backtest.
