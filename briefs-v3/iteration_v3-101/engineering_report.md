# Engineering Report — iter-v3/101

## Headers

- Iteration: iter-v3/101
- Branch: iteration-v3/101
- Commit SHA (post-implementation HEAD): a86eea4c06fb3d6aa4b5d6954288dd4e03effe12
- Setup commit (feat): 87925c358d338e1d0468468e47678c8961cbd13d
- Fix commit (stale-runner): d1ea7d581951f077a88f7ccf348bca4935e69aa9
- Hardware: 20-core CPU, 58 GiB RAM (WSL2)
- Wall-clock time: ~0.72h (3-seed EXPLORATION mode, 35 trials/cell, 3 symbols)

## Configuration Diff vs BASELINE_V3.md (/059 canonical)

| Parameter | Baseline (/059) | iter-v3/101 |
|---|---|---|
| `ITERATION_LABEL` | `"v3-059"` | `"v3-101"` |
| `weight_mode` | `"magnitude"` (implicit) | `"rank_normalized"` |
| `V3_MODELS` | `(BCH, LDO, TRX)` | `(BCH, LDO, TRX)` — unchanged |
| `OOS_CUTOFF_DATE` | `2025-03-24` | `2025-03-24` — SACRED, unchanged |
| `training_months` | `24` | `24` — SACRED, unchanged |
| Inner ensemble seeds | `[42, 123, 456, 789, 1001]` | unchanged |
| `n_trials` | `35` | `35` — unchanged |
| Run mode | EXPLORATION (3-seed) | EXPLORATION (3-seed) — unchanged |
| `EXPLORATION_ENSEMBLE_SIZE` | `3` | `3` — unchanged |
| `feature_columns` | explicit, 14-feature list | explicit, same 14-feature list — unchanged |

Legitimate post-/059 evolution inherited but not axis-changes: `--exploration` flag,
`dsr_relative_b4` DSR methodology field, `_write_confidence_distribution`,
`conviction_derate` (dead/uncalled code).

## Phase 5.5 Gate

OVERALL: PASS. Gate file `briefs-v3/iteration_v3-101/phase5p5_gate.md` committed at
`5532da4`. All 10 mandatory sections (0-10) verified; single-variable axis confirmed
(weight_mode only); default `"magnitude"` reproduces /059 bit-for-bit; `V3_EXCLUDED_SYMBOLS`
unchanged; sacred constants unchanged.

## Implementation — the `weight_mode` axis

Three files touched in setup commit `87925c3`:

1. `src/crypto_trade/strategies/ml/labeling.py` — added `weight_mode: str = "magnitude"`
   parameter to `label_trades()`. Default branch: linear rescale `|net PnL|` to `[1, 10]`
   via `w / w.max() * 9 + 1.0` (byte-identical to /059). Rank branch: `pd.Series(weights).rank(pct=True) * 9.0 + 1.0`. Invalid mode raises `ValueError`.

2. `src/crypto_trade/strategies/ml/lgbm.py` — threaded `weight_mode` through
   `LightGbmStrategy.__init__` and the `label_trades` call in `_train_for_month`.
   Default stored as `"magnitude"` (no-regression guarantee for callers that do not pass
   the parameter).

3. `run_baseline_v3.py` — `ITERATION_LABEL="v3-101"`, `weight_mode="rank_normalized"` added
   to `common_kwargs`.

Tests (`tests/strategies/ml/test_weight_mode.py`, 7 tests, all pass):
- `test_magnitude_mode_byte_identical` — /059 no-regression guarantee
- `test_rank_normalized_output_range` — weights in `(1, 10]`
- `test_rank_normalized_monotone` — Spearman rho == 1.0 with magnitude weights
- `test_invalid_weight_mode_raises` — `ValueError` on unknown mode
- `test_lgbm_stores_weight_mode_default` — default == `"magnitude"`
- `test_lgbm_stores_weight_mode_rank` — stores `"rank_normalized"` when set
- `test_common_kwargs_carry_rank_normalized` — HARD Phase-6 preflight gate (per
  iter-v3/093 lesson); asserts `ITERATION_LABEL="v3-101"` and
  `weight_mode="rank_normalized"` in `run_baseline_v3.py` `common_kwargs`

## Stale-Runner Defect Found and Fixed (commit `d1ea7d5`)

`git diff v0.v3-059 HEAD` on `run_baseline_v3.py` revealed `V3_MODELS` was stale at
`(LDOUSDT, GALAUSDT, ADAUSDT)` — leftover from iter-v3/097 setup commit `e6ed662` (that
iteration filed NEGATIVE/NO-MERGE and never reverted the universe change). Running
iter-v3/101 with the stale universe would have produced uninterpretable results against
the brief's EDA tables and falsifiers (all anchored on BCH/LDO/TRX).

Items restored to /059 canonical in `d1ea7d5`:
- `V3_MODELS` tuple: `(LDO, GALA, ADA)` → `(BCH, LDO, TRX)`
- Pre-flight probe symbols: `ADAUSDT` → `TRXUSDT` (ADX check), `GALAUSDT` → `BCHUSDT`
  (drawdown-brake check), `ADAUSDT` → `LDOUSDT` (vol_scale_floor check)
- `REQUIRED_GAP` comment: restored /059 wording (was /088-era stale)
- Disjointness print/error messages: `LDO/GALA/ADA` refs → `BCH/LDO/TRX`
- Config-accretion check error/pass messages: /097 universe refs → /101 canonical
- Two test files updated to assert `BCH/LDO/TRX` and `ITERATION_LABEL="v3-101"`:
  `tests/features_v3/test_fracdiff_d05_universal.py`,
  `tests/strategies/ml/test_universe_reselection_v3.py`

## Pre-Flight Verification

- **Data freshness:** BCH and TRX 8h klines were 18.8h stale (exceeding the 16h guard).
  Re-fetched via `uv run crypto-trade fetch --interval 8h --symbols BCHUSDT,LDOUSDT,TRXUSDT`
  and v3 features regenerated for all 3 symbols before backtest launch. Documented in
  commit `d1ea7d5` message.
- **Feature isolation:** `grep -r "from crypto_trade.features " src/crypto_trade/features_v3/`
  returned empty — no v1 feature leakage.
- **Symbol exclusion:** `V3_EXCLUDED_SYMBOLS` disjointness assertion runs in preflight
  (`run_baseline_v3.py`). `BCH/LDO/TRX` are the canonical v3 universe; BTC/ETH/etc.
  remain excluded.
- **Label-leakage gap:** `REQUIRED_GAP = (timeout_candles + 1) × n_symbols = (21 + 1) × 3 = 66`.
  Verified by `_verify_label_leakage_gap` (recomputes `(21+1)×3` and asserts equality,
  runs unconditionally in preflight). Walk-forward embargo intact: `walk_forward.py:113`
  `train_end_ms = test_start_ms - embargo_ms`, 22-candle embargo per cell (the `e149e9d`
  lookahead fix, inherited unchanged from /059).
- **Lint:** `uv run ruff check .` clean.
- **Tests:** `uv run pytest` → 1062 passed, 1 failed (`test_recent_candle_has_features` —
  pre-existing environmental failure: BTCUSDT is a v3-excluded symbol whose feature parquet
  lags its klines because the excluded-coins deferred data fetch was not run; not a /101
  regression, not in the backtest path).

## Key Metrics Block

Source: `reports-v3/iteration_v3-101/comparison.csv` and `dsr.json`.

| Metric | In-Sample | Out-of-Sample | Ratio |
|---|---|---|---|
| `monthly_sharpe` | 0.8571 | 0.5190 | 0.6055 |
| `daily_sharpe` | 1.8577 | 1.1703 | 0.6300 |
| `max_drawdown` | 27.45 | 40.77 | 1.4851 |
| `profit_factor` | 1.3007 | 1.1672 | 0.8974 |
| `win_rate` | 31.25% | 40.59% | 1.2990 |
| `n_trades` | 176 | 101 | 0.5739 |
| `total_pnl` | 56.13 | 18.43 | 0.3283 |
| `monthly_calmar` | 2.0446 | 0.4520 | 0.2211 |
| `weighted_pnl_total` | 56.13 | 18.43 | 0.3283 |
| `dsr` | 0.0000 | — | — |
| `pbo` | 0.0968 | — | — |
| `psr` | 1.0000 | — | — |
| `n_trials` | 315 | — | — |
| `n_effective_trials` | 18 | — | — |

DSR/PSR supplementary fields from `dsr.json`:
- `dsr_relative`: 0.019014
- `dsr_relative_b4`: 0.999796
- `frac_positive_paths`: 0.6444 (gate threshold 0.55 — PASS)
- `cpcv_path_sharpe_q75`: 0.8378
- `n_daily_obs_oos`: 94
- `min_trl_months`: 19.56

Note: DSR=0.0 is the EXPLORATION-mode structural artifact. Per
`feedback_v3_dsr_mode_artifact.md`, at `n_trials=315` the E[max_SR] denominator drives DSR
to zero in short-window EXPLORATION runs. Informational only; not a CONFIRMATION-mode gate.

## Per-Symbol Attribution (OOS)

Source: `reports-v3/iteration_v3-101/comparison.csv` per-symbol section.

| Symbol | OOS wpnl | OOS trades | OOS win_rate | concentration_pct |
|---|---|---|---|---|
| BCHUSDT | +10.58 | 37 | 37.8% | +57.43% |
| LDOUSDT | -10.41 | 12 | 33.3% | -56.49% |
| TRXUSDT | +18.25 | 52 | 44.2% | +99.05% |

OOS IS per-symbol (from `in_sample/per_symbol.csv`):
- BCHUSDT: 76 trades, 44.7% WR, +78.68 net PnL pct
- LDOUSDT: 11 trades, 45.5% WR, +14.91 net PnL pct
- TRXUSDT: 89 trades, 27.0% WR, -47.91 net PnL pct

Note: `weight_factor=0.0000` rows exist in OOS trades.csv (rows 77, 78, 81, 82, 83 and
others) — these are intentional BTC-trend-kill-zeroed trades. Consistent with
`weighted_pnl_total` in `comparison.csv` and zero rows in `daily_pnl.csv`. Not a defect.

## Seed Concentration Audit

3-seed EXPLORATION mode (`EXPLORATION_ENSEMBLE_SIZE=3`, outer seeds from `ENSEMBLE_SEEDS`
prefix: 191664963, 1662057957, 1405681631). Single averaged-ensemble roster produced;
`pareto_front.csv` correctly absent (unified-ensemble architecture per BASELINE_V3.md
Phase-B-3 note replaced the per-seed Pareto front at /059). `frac_positive_paths=0.6444`
from 45 CPCV return-proxy paths — gate PASS at threshold 0.55.
`ensemble_summary.json` records the exact three seed integers.

## Label Leakage Audit

- `REQUIRED_GAP = (21 + 1) × 3 = 66` candles; recomputed at `_verify_label_leakage_gap`
  and asserted equal; runs unconditionally in preflight.
- Walk-forward embargo: `compute_embargo_candles(10080, 480) = 22` candles per cell
  (`10080 // 480 + 1`); `train_end_ms = test_start_ms - embargo_ms` at
  `walk_forward.py:113`. The `e149e9d` lookahead fix is intact; `weight_mode` does not
  touch CPCV, embargo, or walk-forward. No serial-dependence leakage path.
- `n_effective_trials=18` (PCA rank for ≥95% variance on 315 trial returns) — no
  artificial inflation.

## Gate Efficacy

The `weight_mode` axis does not introduce or modify any live risk gate. The 7 inherited
risk primitives (vol-adjusted sizing, ADX gate, Hurst regime, z-score OOD, drawdown brake,
BTC contagion kill, liquidity floor) are unchanged from /059. Gate fire rates and per-gate
OOS PnL attribution carry forward from the /059 baseline; no new gate efficacy table is
required for a training-objective-only axis.

Primitive 10 (direction-asymmetric kill switch, BCH LONG block) is present in the runner
(committed `9b1293d` on this branch) — fire rate unchanged from its /047 introduction.

## Trade-Row Spot Check

Three rows re-verified against raw entry/exit/fee math (from Critic review audit):
- OOS row 2: BCH short, entry 303.870000, exit 282.100779, weight 0.3300;
  `pnl_pct=(303.87−282.100779)/303.87×100=7.1640` ✓, `net=7.0640` ✓, `weighted=2.3311` ✓
- OOS row 5: TRX short, entry 0.253000, exit 0.243110, weight 0.40;
  `pnl_pct=3.9091` ✓, `net=3.8091` ✓, `weighted=1.5237` ✓
- IS row 2: BCH long, entry 300.910000, exit 287.394447, weight 0.41;
  `pnl_pct=−4.4916` ✓, `net=−4.5916` ✓, `weighted=−1.8825` ✓

No off-by-one, no sign errors. `n_trials=35×3×3=315` matches `dsr.json`. ✓

## Anomaly Notes

- `test_recent_candle_has_features` failure is pre-existing (BTCUSDT excluded from v3 universe;
  its feature parquet lags klines due to deferred excluded-coins fetch). Not a /101 regression.
- Stale `V3_MODELS` (`LDO/GALA/ADA`) from iter-v3/097 was the only material defect found; fixed
  in `d1ea7d5` before the backtest launched. No backtest was run on the stale universe.
- `dsr_relative=0.019014` (low, near-zero): this is the EXPLORATION-mode artifact described
  in `feedback_v3_dsr_mode_artifact.md`. `dsr_relative_b4=0.999796` is the Bayesian-prior
  stabilized estimate and is the operative number for EXPLORATION classification.

## Status

OVERALL=READY-FOR-CRITIC
