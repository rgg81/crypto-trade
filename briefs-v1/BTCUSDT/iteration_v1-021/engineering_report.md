# Engineering Report — iter-v1/021 (BTCUSDT) — Phase 6 SETUP (full backtest NOT yet run)

## Headers
- Iteration: iter-v1/021 — FUNDING-CONTRA-CROWD re-admission (single-axis vs the /020 MERGED stack)
- Symbol: BTCUSDT (single-symbol v1 track)
- Branch: iteration-v1/redesign-single-symbol
- Setup commit SHA: fbcf1358d891fbb019ac0149b7b327a509203382
- Type: SPECIALIST / EXPLORATION (per brief §6 cadence; K=5 screen first)
- Risk declaration: NORMAL-RISK (brief §2.5 — stateless RULE-layer entry filter on top of
  the UNCHANGED training objective, UNCHANGED direction, UNCHANGED conviction gate; it only
  decides whether an already-gate-skipped candle is un-skipped at the unchanged trend-state
  direction — never changes Optuna's training-objective domain, never flips direction).
- Status: SETUP-ONLY — src + test wired, lint-clean (my lines), look-ahead test passes,
  readmit-fires-and-thickens smoke confirmed. The full K=5 EXPLORATION backtest is launched
  by the orchestrator (detached), then this report's metric block is filled.

## What was wired (single axis vs iter-020)
iter-021 = the ENTIRE iter-020 MERGED stack + ONLY `enable_funding_contra_readmit=True`
(plus `funding_contra_col="funding_rate_zscore_30"`, `funding_contra_quantile=0.50`).
Everything else (19-col HYBRID `V1_BTC_ITER009_FEATURES`, `fixed_horizon` N=42 (14d),
let-winners-run exec `atr_tp=100.0`/`atr_sl=1.45`/14d timeout, R2 brake
trigger=2.07/anchor=8.28/floor=0.20, R3 OOD 0.70, R5 vol-target, stateless 200-SMA
trend-state DIRECTION override, q=0.40 trend-strength conviction gate) is BIT-IDENTICAL to
/020. R1 OFF. `funding_rate_zscore_30` is already in the 19-col HYBRID set — NO feature
change; RULE-layer only.

The re-admission attaches at the trend-strength gate-skip site. When the conviction gate
WOULD skip a weak-trend candle, re-admit it (do NOT skip) IFF funding opposes the trend:
```
f_z30   = funding_z30[t-1]                         # past-only `.shift(1)` over the parquet col
opposes = sign(f_z30) == -sign(_sp_direction)      # funding leans against the trend-state dir
crowded = |f_z30| >= f_thr                          # f_thr = past-only training-window q_f quantile
readmit = isfinite(f_z30) & isfinite(f_thr) & crowded & opposes
fire    = (conviction gate fires) OR readmit
```
`f_thr` is recomputed at each `_train_for_month` from the training-window rows ONLY
(open_time in `[train_start_ms, train_end_ms)`), mirroring the trend-strength threshold and
the R3 OOD training-window-stat pattern — fit on PAST rows, never recomputed on test rows.
The direction is NEVER changed — the re-admitted row fires at the unchanged trend-state
direction `_sp_direction`.

## Load-bearing `.shift(1)` (leak-free)
The parquet's `funding_rate_zscore_30[t]` numerator uses `rate[t]` (the funding rate that
settled at candle t's open). The QR's IS-only script reads
`f_z30 = df["funding_rate_zscore_30"].shift(1)` — an ADDITIONAL `.shift(1)` so bar t uses
`funding_z30[t-1]`. compute_features() reproduces this EXACTLY (the index applies the extra
`.shift(1)` at build time). The QR leak-probe confirmed this `.shift(1)` is LOAD-BEARING:
478/2382 = 20.07% of re-admission decisions FLIP without it.

## Insertion points (commit fbcf1358)
`src/crypto_trade/strategies/ml/lgbm.py`:
- `__init__` params (~L326): `enable_funding_contra_readmit=False`,
  `funding_contra_col="funding_rate_zscore_30"`, `funding_contra_quantile=0.50` (default off).
- Instance attrs (~L574): `_enable_funding_contra_readmit`, `_funding_contra_col`,
  `_funding_contra_quantile`, `_funding_contra_idx`, `_funding_contra_thr`.
- `compute_features()` (~L911): builds sorted `(open_time_ms, funding_z30[t-1])` index from
  the trend-state symbol parquet's `funding_contra_col` with an extra `.shift(1)` — EXACTLY
  the QR script's `f_z30`. FAIL-LOUD if the parquet or the column is missing.
- `_train_for_month()` specialist block (~L1920): per-month `f_thr` from training-window
  rows; `< 50` finite rows → `None` (no re-admission that month → conservative skip).
- `_compute_funding_contra(open_time)` (~L2512): exact-open_time-match lookup of
  `funding_z30[t-1]` at row t; `None` on warmup/NaN/missing.
- `get_signal()` specialist path (gate-skip site, ~L2939): at the `if … < thr` skip branch,
  check the re-admission condition BEFORE `return NO_SIGNAL`. Readmit → log
  `funding_contra_readmit` and fall through (fire at the unchanged direction). Else → the
  original `trend_strength_gate_skip` log + `return NO_SIGNAL`.

`run_baseline_v1.py`:
- `run_model()` signature (~L638) + `LightGbmStrategy(...)` construction (~L821): 3 params
  threaded (default False).
- CLI flags (~L2886): `--enable-funding-contra-readmit` / `--funding-contra-col` /
  `--funding-contra-quantile`.
- `_spec_*` defaults (~L3813) + `v1-021` keyed override branch (= /020 config + 3 readmit
  params; q_f=0.50) + CLI precedence hook + generic single-symbol dispatch threading (~L4719).
- Backtest-mode `decision_log.configure()` gate extended to also fire when the readmit is
  active → captures the `funding_contra_readmit` events for Phase 7 attribution.

Note on the legacy `v1-021` label collision: the runner has a PRE-EXISTING legacy
multi-symbol `v1-021` methodology-pivot branch (`set(symbols) == V1_ITER021_UNIVERSE`, 5
symbols). The redesigned single-symbol run passes 1 symbol → routes to the UNIVERSAL
SINGLE-SYMBOL ROUTING GUARD (which takes precedence over all `set(symbols) ==
V1_ITERNNN_UNIVERSE` branches); the legacy branch never fires (its 5-symbol guard is False).
My new keyed override is in the SEPARATE `_spec_*` config chain, disambiguated by the
single-symbol guard at dispatch. No collision.

## Look-ahead test result (MANDATORY)
`tests/test_funding_contra_readmit_lookahead.py` — 17 tests PASS. Protects:
1. The compute_features `(open_time, funding_z30[t-1])` index matches an independent manual
   past-only reference at every row.
2. `_compute_funding_contra(open_time)` equals the manually-lagged `funding_z30[t-1]`.
3. APPENDING future candles (open_time > decision) does NOT change a past row's value (THE
   look-ahead property).
4. Mutating the decision candle's OWN funding value does NOT change its signal (it is
   `.shift(1)`-lagged → uses funding[t-1]).
5. Mutating funding[t-1] DOES change it (confirms it is the live input — alignment correct).
6. Warmup (no t-1) / NaN funding → `None` → caller does NOT re-admit (conservative skip).
7. The per-month `f_thr` uses ONLY training-window rows (rows after the window mutated to
   extremes do not change it) → past-only, leak-free.
8. The full readmit boolean equals `isfinite & |f|>=thr & sign(f)==-sign(dir)`, matching the
   QR script's r2 mask EXACTLY (both directions checked).

Mandated suite — `uv run pytest tests/test_funding_contra_readmit_lookahead.py
tests/test_trend_state_lookahead.py tests/test_trend_strength_lookahead.py
tests/test_lookahead_embargo.py tests/test_backtest.py -q` → **129 passed**.

## Byte-identical-when-disabled proof
- Source diff is ADD-ONLY for `lgbm.py` and `run_baseline_v1.py` except the gate-skip block,
  which was restructured into an if/else (re-admit vs original skip) — the `else` branch is
  the ORIGINAL `trend_strength_gate_skip` log + `return NO_SIGNAL` verbatim. With
  `enable_funding_contra_readmit=False` the `if _fc_readmit:` is never reached (the inner
  guard requires `self._enable_funding_contra_readmit and self._funding_contra_thr is not
  None`), so the path is the original skip — bit-identical.
- `enable_funding_contra_readmit` defaults False in `LightGbmStrategy.__init__`, `run_model`,
  and `_spec_enable_funding_contra_readmit`. Both new code paths (compute_features index
  build, get_signal readmit) are wrapped in `if self._enable_funding_contra_readmit:` →
  strict no-op when disabled. `_funding_contra_idx` / `_funding_contra_thr` stay `None`.
- `test_disabled_by_default_no_index_built` asserts default construction leaves the index
  None and `_compute_funding_contra` returns None.
- **Empirical control**: the iter-020 control run (readmit OFF, identical K=2/n_trials=2)
  produced **0 `funding_contra_readmit` events** — the disabled path is dead.
- No v2/v3 source touched (`git diff --name-only` shows no `features_v2`/`features_v3`/
  `validation_v2`/`validation_v3`/`run_baseline_v2`/`run_baseline_v3`). v2/v3 construct
  `LightGbmStrategy` without the flag → unchanged.
- `grep -rn funding_contra src/crypto_trade/features_v2/ src/crypto_trade/features_v3/` → none.
- The committed iter-020 baseline reports tree (`comparison.csv`) was restored to its
  session-start committed state after the control run; the MERGED /020 baseline stays
  reproducible (the control only touched untracked report files, which were removed).

## Smoke verification — readmit FIRES and THICKENS (K=2, n_trials=2)
Ran iter-021 (readmit ON) vs an iter-020 control (readmit OFF), identical K=2 / n_trials=2,
on the pinned BTCUSDT parquet (7073 rows; 6980 finite funding_z30[t-1] rows). Banner
confirmed `FUNDING-CONTRA READMIT ON (col=funding_rate_zscore_30 q_f=0.5; …; .shift(1))`,
index loaded, per-month `f_thr` ≈ 0.61 from training-window rows.

| run | IS trades | OOS trades | total |
|---|---:|---:|---:|
| iter-020 control (readmit OFF) | 76 | 37 | 113 |
| iter-021 (readmit ON)          | 105 | 51 | 156 |
| **increase**                   | **+38.2%** | **+37.8%** | **+38.1%** |

The readmit thickens the book ~+38% (re-admits gate-skipped weak-trend rows) — directionally
consistent with the brief's +23–31% IS-firing-candle estimate (the realized count grows more
because the let-run 14d book holds positions). `funding_contra_readmit` events: **372**;
`trend_strength_gate_skip` events: 913. Control: **0 readmit events** (disabled path dead).

Correctness invariant — 2 logged re-admission examples (every example funding-OPPOSES-trend):
```
ot=2022-02-05 00:00  dir_sign=-1  funding_z30=+1.6890  thr=0.6065  opposes=True crowded=True
ot=2022-02-07 00:00  dir_sign=-1  funding_z30=+1.1487  thr=0.6065  opposes=True crowded=True
```
Both: SHORT trend (dir=-1) + POSITIVE funding (crowded longs paying carry against the
downtrend) → funding OPPOSES the trend, |funding_z30| ≥ thr → re-admitted at the UNCHANGED
short direction. Exactly the brief §0.2 mechanism (crowded-long squeeze fuels the
continuation DOWN; the trend-state short is the high-quality side). These timestamps match
the iter-018 example skips (2022-02-05/07) — weak-trend rows the gate skipped are now
re-admitted because funding opposes.
(The K=2 smoke report dirs were throwaway — removed; the iter-020 committed reports were
restored from git. The real K=5 run produces the merge artifacts.)

## Risk note — live `_tick` parity
Default `enable_funding_contra_readmit=False` keeps the live engine `_tick` path
byte-identical for v2/v3 and /002–/020. When enabled (iter-021 cell only), the readmit reads
the SAME `(open_time, funding_z30[t-1])` past-only index in backtest and live (no
exchange/clock state), and the SAME `_sp_direction` the trend-state DIRECTION override
already set — so backtest and live compute an identical re-admission decision. The per-month
`f_thr` is rebuilt from the training window at each month-train (the existing lazy-retrain
hook), matching the backtest's `_train_for_month`.

## Anomaly notes
- `[FATAL] engineering_report.md NOT FOUND` at the END of a smoke run is the expected
  end-of-pipeline deliverable guard (the run produced trades + reports first, exit 0). Not a
  backtest error; this report satisfies it for the real run.
- Pre-existing E501 lint warnings at run_baseline_v1.py:4180/4222/4232/4338-4340/4461-4505
  are in the v1-013/018/019/020 legacy branches (confirmed present in the committed file
  BEFORE my changes; none appear as `+` additions in my diff vs the parent `b9304860`); not
  touched (out-of-scope for this single-axis change). All MY added lines are lint-clean
  (`ruff check` on the new test file = "All checks passed!"; the 4 E501s I introduced were
  fixed; `ruff format --check` = "3 files already formatted").

## Exact full EXPLORATION (K=5) command — for the detached launch
```
PYTHONUNBUFFERED=1 uv run python run_baseline_v1.py \
  --exploration --iteration 21 --symbols BTCUSDT --n-trials 18 \
  > reports-v1/BTCUSDT/iteration_v1-021/run.log 2>&1
```
- `--exploration` resolves `bagging_k = V1_EXPLORATION_BAGGING_K = 5`. ENSEMBLE_SIZE=1,
  outer seeds=1.
- `--iteration 21` keys the `v1-021` override branch (= /020 config + the 3 readmit params;
  prints `[iter-v1/021] OVERRIDE ACTIVE … FUNDING-CONTRA READMIT ON`).
- `--n-trials 18` = the v1 SPECIALIST default (per cycle-7 budget). Reports land under
  `reports-v1/BTCUSDT/iteration_v1-021/{in_sample,out_of_sample}/`; the decision_log (with
  the `funding_contra_readmit` + `trend_strength_gate_skip` events) at
  `reports-v1/BTCUSDT/iteration_v1-021/decision_log.jsonl`.

PRIMARY RISK to verify on the real run (brief §3 / §4 / §5): the OOS trade-rate floor. The
let-run 14d book holds ~42 candles, so the INDEPENDENT OOS trade count is well below the
firing-row estimate. v1 specialist floor is ≥50 OOS trades; the brief projects ~47 at q_f=0.50
(just under). If the K=5 run comes in < 50 OOS, the brief's PRE-REGISTERED fallback is q_f=0.30
(`--funding-contra-quantile 0.30`, est. ~50 projected; IS-stable: combined full +0.81, readmit
full +0.22). Also verify the brief §5 falsifiers: both-positive (IS>0 AND OOS>0), IS ≥ +0.30,
OOS-concentration improved (no ≤2 OOS trades/month > ~40% of OOS net), and combined recent IS
sub-period positive.

## Status
OVERALL=SETUP-COMPLETE — awaiting detached K=5 backtest. (Metric block / seed-concentration /
gate-efficacy tables to be filled post-run before READY-FOR-CRITIC.)
