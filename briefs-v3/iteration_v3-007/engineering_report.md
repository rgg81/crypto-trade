# Engineering Report — iter-v3/007

## Headers

- Iteration: iter-v3/007
- Branch: iteration-v3/007
- Commit SHA at backtest time: 849c4a6de564b731f8fcf5de315602bf35454ae4
- Code SHAs:
  - `92218ef` — feat(iter-v3/007): top-14 V3_FEATURE_COLUMNS subset + ITERATION_LABEL=v3-007
  - `849c4a6` — fix(iter-v3/007): risk_v3 always loads atr_pct_rank_200 from parquet (see below)
  - `a394314` — feat(iter-v3/007): top-N feature importance analysis (analysis script)
  - `bce50c8` — feat(iter-v3/007): --exploration mode (colsample=1.0, ENSEMBLE_SIZE=1, n_trials=10)
- Hardware: 12th Gen Intel Core i9-12900HK, 58 GiB RAM
- Wall-clock time: 0.13h = ~8 minutes

## Library Versions

| Package | Version |
|---|---|
| lightgbm | 4.6.0 |
| numpy | 2.2.6 |
| pandas | 3.0.0 |
| pyarrow | 23.0.1 |
| pytest | 9.0.2 |
| scikit-learn | 1.8.0 |
| scipy | 1.17.0 |
| statsmodels | 0.14.6 |

## Configuration Diff vs Baseline (iter-v3/006)

| Parameter | iter-v3/006 | iter-v3/007 |
|---|---|---|
| `V3_FEATURE_COLUMNS` | 34 features (V3_FEATURE_COLUMNS_FULL) | **14 features (V3_FEATURE_COLUMNS_TOP_N)** |
| `ITERATION_LABEL` | v3-006 | **v3-007** |
| `ENSEMBLE_SIZE` | 5 (--exploration sets 1) | 1 (via --exploration) |
| `n_trials` | 50 (--exploration sets 10) | 10 (via --exploration) |
| `colsample_bytree` | Optuna-sampled | **1.0 (hardcoded by --exploration)** |
| Symbols | BCH-only (via V3_MODELS override) | **Full universe: BCH+MKR+LDO+TRX** |
| Seeds | 1 | 1 |
| Labels | unchanged | unchanged |
| Risk gates | unchanged | unchanged |

## Key Metrics Block

| metric | in_sample | out_of_sample | ratio |
|---|---:|---:|---:|
| monthly_sharpe | **0.2241** | 0.0622 | 0.2774 |
| daily_sharpe | 0.5194 | 0.1774 | 0.3417 |
| max_drawdown | 83.85% | 48.76% | 0.5815 |
| profit_factor | 1.0692 | 1.0218 | 0.9557 |
| win_rate | 36.13% | 42.22% | 1.1686 |
| n_trades | 274 | 90 | 0.3285 |
| total_pnl | +38.49% | +3.61% | 0.0939 |
| monthly_calmar | 0.4590 | 0.0741 | 0.1614 |
| dsr | 0.0000 | — | — |
| pbo | 0.1419 | — | — |
| psr | 0.7932 | — | — |
| n_trials | 40 | — | — |
| n_effective_trials | 7 | — | — |

## Per-Symbol Section (comparison.csv)

| Symbol | weighted_pnl | n_trades | win_rate | concentration_pct |
|---|---:|---:|---:|---:|
| BCHUSDT | 3.03 | 36 | 44.4% | 83.95% |
| LDOUSDT | 16.46 | 18 | 44.4% | 455.55% |
| MKRUSDT | -14.03 | 12 | 33.3% | -388.34% |
| TRXUSDT | -1.85 | 24 | 41.7% | -51.15% |

Note: concentration_pct values exceed 100% or are negative because individual symbols have positive/negative PnL contributions that net to a small total. OOS total PnL = +3.61%, driven by LDOUSDT (+17.72%) offset by MKRUSDT (-6.49%).

## 14 Features Actually Used (Sanity Check Against Brief Section 3.3)

```
max_dd_window_50       (rank 1)
vwap_dev_50            (rank 2)
ema_spread_atr_20      (rank 3)
ret_kurt_50            (rank 4)
ret_skew_200           (rank 5)
range_realized_vol_50  (rank 6)
hurst_diff_100_50      (rank 7)
ret_kurt_200           (rank 8)
hurst_100              (rank 9)
btc_ret_14d            (rank 10)
ret_skew_50            (rank 11)
vwap_dev_20            (rank 12)
ret_autocorr_lag1_50   (rank 13)
sym_vs_btc_ret_7d      (rank 14)
```

All 14 features appear in in_sample/feature_importance.csv. Confirmed: every
feature contributed non-zero importance. No missing columns.

## IS Feature Importance (Top-5 by Importance Score)

| Feature | IS Importance |
|---|---:|
| ret_skew_200 | 408.0 |
| vwap_dev_50 | 384.0 |
| range_realized_vol_50 | 321.0 |
| ema_spread_atr_20 | 318.0 |
| ret_autocorr_lag1_50 | 292.0 |

## Seed Concentration Audit (1-seed EXPLORATION)

Single seed (outer=42). ENSEMBLE_SIZE=1 per --exploration flag.

- Seed 42: monthly_sharpe=0.0622 (OOS), max_drawdown=48.76%, calmar=0.0741,
  pbo=0.1419, n_trades=90, max_concentration_pct=84.44% (BCHUSDT in OOS)

Note: BCHUSDT 84.44% concentration in OOS exceeds the ≤30% threshold from
the full-ensemble criteria. Per Section 0.5 TYPE=EXPLORATION, concentration
is NOT a gate for this iteration — flagged for Critic review.

## Label Leakage Audit

Gap formula: (timeout_candles + 1) × n_symbols = (21 + 1) × 4 = 88.
REQUIRED_GAP = 88. Verified in pre-flight (`_verify_label_leakage_gap()`).

Pre-flight log line:
```
  Label-leakage gap: (timeout_candles=21+1) * n_symbols=4 = 88
  [matches REQUIRED_GAP=88]  PASS
```

## Gate Efficacy Table

Risk gates are unchanged from iter-v3/006. The critical infrastructure fix
(SHA 849c4a6) ensures `atr_pct_rank_200` is always loaded from parquet
independent of V3_FEATURE_COLUMNS content.

| Gate | Status | Note |
|---|---|---|
| Vol scaling (atr_pct_rank_200) | ON | Fixed: now loaded explicitly from parquet |
| ADX gate (>20) | ON | Computed from OHLC, not feature list |
| Hurst regime check | ON | hurst_100 in top-14, loaded normally |
| Z-score OOD (|z|>2.5) | ON | Computed on V3_FEATURE_COLUMNS (14 features) |
| Low-vol filter (atr_pct_rank_200 >= 0.33) | ON | Fixed: same as vol scaling |
| Hit-rate feedback | OFF | Disabled per iter-v2/045 lesson |
| BTC trend filter (±20%, 14d) | ON | Loaded from BTC klines independently |
| R1 / R2 / R3 | OFF | Not in v3 scope |

## Infrastructure Fix: risk_v3 Gate-Feature Dependency (SHA 849c4a6)

During the first backtest run (after sub-fix #1+#2 commit at SHA 92218ef),
the runner crashed with:
```
KeyError: 'atr_pct_rank_200'
```
at `risk_v3.py:85` in `_build_lookups()`.

Root cause: `RiskV3Wrapper._build_lookups()` builds its `needed` columns list
as `["open_time", "high", "low", "close", "hurst_100", *V3_FEATURE_COLUMNS]`.
With V3_FEATURE_COLUMNS = top-14 (which excludes `atr_pct_rank_200`), the
parquet read did not load `atr_pct_rank_200`, causing the KeyError at line 85
where the lookup table is built.

Fix: added `"atr_pct_rank_200"` explicitly to the `needed` list BEFORE the
`*V3_FEATURE_COLUMNS` unpacking, with a comment explaining it is a gate
primitive independent of the training feature list. Dict.fromkeys dedup
prevents double-loading if a future V3_FEATURE_COLUMNS reassignment includes it.

This fix is correct per brief Section 3.4: "atr_pct_rank_200 is DROPPED from
V3_FEATURE_COLUMNS_TOP_N but is still computed by the feature pipeline (it's
in the parquet) and the gate logic reads it directly." The brief anticipated
this dependency but did not identify the specific code path in risk_v3.py.

The fix is minimal (1 extra column in the needed list), does not change any
gate logic, and the parquet always contains `atr_pct_rank_200` as a full-34
feature pipeline output.

## Anomaly Notes (Trade Spot-Check)

Random spot-check of 10 OOS trades (seed=42 in Python's random.sample):

All 10 trades examined:
- exit_reason: valid (stop_loss, take_profit, timeout)
- weight_factor: in [0.35, 1.0] — consistent with vol-scaling gate
- net_pnl_pct: range [-8.37%, +10.30%] — consistent with 2.9x ATR TP, 1.45x SL
- no NaN fields observed

No anomalies found.

## Section 3.6 Reconciliation Table — All 10 Verifiers

| # | Verifier | Status |
|---|---|---|
| 1 | `len(V3_FEATURE_COLUMNS) == 14` | PASS |
| 2 | `grep "n != 14" run_baseline_v3.py` | PASS |
| 3 | `test -f reports-v3/iteration_v3-007/comparison.csv` | PASS |
| 4 | IS monthly_sharpe != 0 (= 0.2241) | PASS |
| 5 | IS monthly_sharpe > 0 (= 0.2241) | PASS |
| 6 | pareto_front.csv has >= 1 row (= 1) | PASS |
| 7 | 35/35 adversarial tests pass | PASS |
| 8 | Wall-clock < 60 min (= 8 min) | PASS |
| 9 | Active models 4/4 in run.log | PASS |
| 10 | exploration/Seeds:1 in run.log | PASS |

## Prediction Calibration (Pre-Registration Section 7 Check-in)

Pre-registered predictions vs observed:

- P1 (15%): top-N breaks at runner level — TRIGGERED (risk_v3 gate crash at
  first run; fixed at SHA 849c4a6). The prediction named "wrong column names,
  missing imports" — the actual failure was a gate-column dependency, a
  closely related category. P1 MATERIALIZED (partial).

- P2 (10%): --exploration hidden ENSEMBLE_SIZE=5 dependency — NOT triggered.
  Backtest ran cleanly at ENSEMBLE_SIZE=1 after the gate fix. P2 MISS.

- P3 (15%): wall-clock > 60 min — NOT triggered. 8 min actual vs 60-min cap.
  P3 MISS.

- P4 (30%): IS Sharpe stays in [-0.1, +0.4] — IS monthly Sharpe = 0.2241.
  This is within the P4 range [−0.1, +0.4]. P4 MATERIALIZED.

- P5 (70%): IS Sharpe in [+0.4, +0.7] — NOT materialized. IS monthly Sharpe =
  0.2241 is below +0.4. P5 MISS.

## Section 8 EXPLORATION Criteria Evaluation

Per the brief's pre-registered EXPLORATION-PROMISING criteria:

| # | Criterion | Result | Status |
|---|---|---|---|
| 1 | TYPE=EXPLORATION declared | TRUE | PASS |
| 2 | --exploration flag used | TRUE (Seeds:1, n_trials=10, colsample=1.0) | PASS |
| 3 | Wall-clock < 60 min | 8 min | PASS |
| 4 | 35/35 adversarial tests pass | 35/35 | PASS |
| 5 | V3_FEATURE_COLUMNS reduced to 14 | len=14 confirmed | PASS |
| 6 | pareto_front.csv has >= 1 row | 1 row | PASS |
| 7 | Critic OVERALL = EXPLORATION-PROMISING | Pending Critic | TBD |
| 8 | Methodology axes (Checks 1,2,4,5,6,8) no FAIL | Pending Critic | TBD |
| 9 | NO 5-seed or 10-seed runs | --seeds 1 confirmed | PASS |
| 10 | All 10 reconciliation verifiers exit 0 | All PASS | PASS |

Criteria 7 and 8 await Critic Phase 7.5. Process-level criteria 1-6, 9-10
all PASS.

IS monthly Sharpe = +0.2241 > 0 (signal exists). However, IS Sharpe is below
the +0.5 EXPLORATION-PROMISING guidance threshold from the brief. Whether the
Critic emits EXPLORATION-PROMISING or EXPLORATION-NEGATIVE depends on the
methodology axis review and interpretation of IS Sharpe = +0.22 vs the +0.5
guidance.

## Comparison vs iter-v3/003 (Full Universe Baseline)

| Metric | iter-v3/003 (IS, seed=42, n_trials=50, 34 features) | iter-v3/007 (IS, seed=42, n_trials=10, 14 features) |
|---|---:|---:|
| IS monthly_sharpe | -0.0746 | **+0.2241** |
| IS n_trades | ~(not recorded in brief) | 274 |

The top-14 subset improved IS Sharpe from -0.0746 (iter-v3/003, full universe,
34 features, n_trials=50) to +0.2241 (iter-v3/007, full universe, 14 features,
n_trials=10). Direction of improvement is consistent with the de-noising
hypothesis. The absolute level (+0.22) is below the +0.5 EXPLORATION-PROMISING
guidance from the brief.

Note: iter-v3/003 used n_trials=50 and ENSEMBLE_SIZE=5; iter-v3/007 used
n_trials=10 and ENSEMBLE_SIZE=1 (--exploration). The --exploration mode
introduces additional variance due to fewer Optuna trials.

## Status

OVERALL: READY-FOR-CRITIC
