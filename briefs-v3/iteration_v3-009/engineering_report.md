# Engineering Report — iter-v3/009

## Headers

| Field | Value |
|---|---|
| Iteration | iter-v3/009 |
| Type | EXPLORATION (cadence catalog row #2) |
| Branch | iteration-v3/009 |
| Code SHA at backtest | `43b3ed8` |
| Analysis SHA | `565e0ec` (top-13 validation script, committed before brief) |
| Brief SHA | `96ec4d5` |
| Phase 5.5 Gate | PASS (`7b72845`) |
| Hardware | WSL2 / Linux 6.6.87.2 |
| Wall-clock | 660s = 0.18h (11 min) — target < 30 min, hard cap 2h |
| Run date | 2026-05-06 |

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

## Runner Invocation

```
uv run python run_baseline_v3.py --exploration --seeds 1 --n-trials 10
```

`--exploration` flag active: ENSEMBLE_SIZE=1 (seed=42), n_trials=10, colsample_bytree=1.0, output dir = `reports-v3/iteration_v3-009/`.

## Configuration Diff vs iter-v3/007 Baseline

| Parameter | iter-v3/007 | iter-v3/009 |
|---|---|---|
| `ITERATION_LABEL` | `"v3-007"` | `"v3-009"` |
| `V3_FEATURE_COLUMNS` length | 14 | **13** (`vwap_dev_50` dropped) |
| Seeds | 1 (exploration) | 1 (exploration) |
| n_trials | 10 | 10 |
| colsample_bytree | 1.0 | 1.0 |
| Symbols | BCH, MKR, LDO, TRX | BCH, MKR, LDO, TRX |
| OOS_CUTOFF_DATE | 2025-03-24 | 2025-03-24 (UNCHANGED) |
| training_months | 24 | 24 (UNCHANGED) |

Only change vs iter-v3/007: one feature dropped (`vwap_dev_50`, iter-v3/007 IS rank 2).
Only change vs iter-v3/008: `ITERATION_LABEL` cosmetic update (all other code inherited).

## Headline Metrics Table

| Metric | iter-v3/007 IS | iter-v3/009 IS | iter-v3/007 OOS | iter-v3/009 OOS | OOS/IS ratio |
|---|---:|---:|---:|---:|---:|
| Monthly Sharpe | +0.2241 | **+0.0802** | +0.0622 | **+1.1223** | 13.99 |
| Daily Sharpe | — | +0.1815 | — | +2.4761 | 13.64 |
| Max Drawdown (%) | — | 76.49 | — | 37.90 | 0.496 |
| Profit Factor | — | 1.0246 | — | 1.3535 | 1.321 |
| Win Rate (%) | — | 37.08 | — | 45.98 | 1.240 |
| N Trades | — | 267 | — | 87 | 0.326 |
| Total PnL | — | 12.73 | — | 53.22 | 4.180 |
| Monthly Calmar | — | 0.1664 | — | 1.4043 | 8.437 |
| DSR | — | 0.0000 | — | — | — |
| PBO (per-cell mean) | — | 0.1145 | — | — | — |
| PSR | — | 1.0000 | — | — | — |
| n_trials | — | 40 | — | — | — |
| n_eff | — | 7 | — | — | — |

Delta vs iter-v3/007: IS monthly Sharpe Δ = **-0.144** (dropped from +0.2241 to +0.0802); OOS monthly Sharpe Δ = **+1.060** (rose from +0.0622 to +1.1223).

## Per-Symbol Breakdown

### In-Sample

| Symbol | Trades | Win Rate (%) | Net PnL (%) | % of Total PnL |
|---|---:|---:|---:|---:|
| LDOUSDT | 23 | 39.1 | +14.02 | -21.88 |
| TRXUSDT | 89 | 38.2 | -14.53 | 22.67 |
| BCHUSDT | 84 | 42.9 | -19.31 | 30.14 |
| MKRUSDT | 71 | 33.8 | -44.26 | 69.07 |

Note: IS total PnL = +12.73 from comparison.csv; the per_symbol table shows negative net_pnl_pct for 3/4 symbols, with the portfolio positive due to weighting. IS is barely positive overall (IS monthly Sharpe +0.0802), with LDOUSDT the only per-symbol positive contributor in net_pnl_pct.

### Out-of-Sample

| Symbol | Trades | Win Rate (%) | Net PnL (%) | % of Total PnL | Concentration |
|---|---:|---:|---:|---:|---:|
| LDOUSDT | 12 | 75.0 | +85.51 | 104.87 | 132.97% |
| TRXUSDT | 25 | 44.0 | +5.97 | 7.32 | 1.87% |
| BCHUSDT | 37 | 43.2 | +3.16 | 3.88 | -1.75% |
| MKRUSDT | 13 | 30.8 | -13.09 | -16.06 | -33.09% |

OOS total PnL = +53.22. LDOUSDT drives 104.87% of OOS PnL with 12 trades and 75% win rate. OOS max concentration (from pareto_front.csv): 98.61% in seed=42 (single-seed exploration run).

## Feature Importance — iter-v3/009 IS vs iter-v3/007 IS

| iter-v3/009 Rank | Feature | iter-v3/009 Imp | iter-v3/007 Rank | iter-v3/007 Imp |
|---:|---|---:|---:|---:|
| 1 | ema_spread_atr_20 | 420 | 4 | 318 |
| 2 | ret_skew_200 | 342 | 1 | 408 |
| 3 | range_realized_vol_50 | 333 | 3 | 321 |
| 4 | vwap_dev_20 | 317 | 10 | 201 |
| 5 | ret_skew_50 | 289 | 13 | 168 |
| 6 | max_dd_window_50 | 280 | 6 | 242 |
| 7 | btc_ret_14d | 274 | 11 | 195 |
| 8 | sym_vs_btc_ret_7d | 259 | 14 | 159 |
| 9 | hurst_100 | 257 | 8 | 236 |
| 10 | ret_autocorr_lag1_50 | 255 | 5 | 292 |
| 11 | ret_kurt_50 | 235 | 9 | 219 |
| 12 | ret_kurt_200 | 198 | 7 | 237 |
| 13 | hurst_diff_100_50 | 109 | 12 | 172 |

Notable rank shifts: `ema_spread_atr_20` rose from rank 4 to rank 1; `vwap_dev_20` rose from rank 10 to rank 4; `ret_skew_200` dropped from rank 1 to rank 2. This confirms Prediction P3 from Section 7 of the brief (importance ranks may shift with the different feature set). The dropped `vwap_dev_50` had IS rank 2 in iter-v3/007 (importance=462).

## PBO / CPCV / DSR Audit

| Statistic | Value | Source |
|---|---:|---|
| Per-cell mean PBO | 0.1145 | dsr.json |
| Median PBO | 0.0000 | run.log |
| frac_positive_paths | 0.600 (27/45) | dsr.json |
| CPCV path Sharpe Q25 | -0.5366 | dsr.json |
| CPCV path Sharpe Q50 | +0.1175 | dsr.json |
| CPCV path Sharpe Q75 | +1.0278 | dsr.json |
| DSR | 0.0000 | dsr.json |
| PSR | 1.0000 | dsr.json |
| n_eff (per-cell median) | 7 | dsr.json |
| n_trials total | 40 | dsr.json (10 trials × 4 symbols) |
| min_trl_months | 66.75 | dsr.json |

DSR=0.0 and PSR=1.0 are informational only for EXPLORATION (not gates per Section 8 criteria).
173/173 per-cell PBO cells were informative (rank > 1).

## Label Leakage Audit

From run.log pre-flight output:

```
Label-leakage gap: (timeout_candles=21+1) * n_symbols=4 = 88  [matches REQUIRED_GAP=88]  PASS
CV gap: 22 rows (= 184h at 8h interval — the within-model purge)
```

Gap = 88 = (21 + 1) × 4 satisfies the López de Prado purge requirement. The inner CV gap of 22 rows (184h) was verified in the run.log for every symbol's fold boundaries.

## Gate Efficacy Table

All 7 risk primitives applied across full run. Stats below are from run.log (full run including IS + OOS candles):

| Gate | BCHUSDT | MKRUSDT | LDOUSDT | TRXUSDT |
|---|---|---|---|---|
| Signals seen | 2851 | 2773 | 1062 | 2552 |
| Killed by z-score OOD | 405 | 884 | 261 | 454 |
| Killed by Hurst | 171 | 159 | 85 | 162 |
| Killed by ADX | 694 | 560 | 260 | 676 |
| Killed by low-vol | 597 | 517 | 204 | 355 |
| Kill rate | 65.5% | 76.5% | 76.3% | 64.5% |
| Vol-scaled signals | 984 | 653 | 252 | 905 |
| Mean vol scale | 0.709 | 0.754 | 0.746 | 0.723 |

BTC trend filter (gate 7): killed 22/354 signals (6.21%) across all symbols.

Combined kill rates are within the 69–78% target range for MKRUSDT and LDOUSDT. BCHUSDT and TRXUSDT land at 64–66%, slightly below the lower bound — consistent with iter-v3/007 values (gate parameters unchanged).

## ADF Stationarity Audit

ADF tested per (symbol, feature, retraining month). Results:

- Total rows: 2769
- Stationary (p < 0.05): 2278 (82.3%)
- Non-stationary: 491 (17.7%)

One missing entry logged: `LDOUSDT/cusum_reset_count_200 not found in ADF output` (this feature is not in V3_FEATURE_COLUMNS; it appears to be a legacy feature in the parquet not tested — not an error).

## IC Matrix Summary (13×13 IS)

Max off-diagonal |IC| in 13-feature matrix: 0.6602 (`max_dd_window_50` × `range_realized_vol_50`, negative rho). This is the same value verified in the analysis script at SHA `565e0ec`. Zero pairs above the |IC| ≥ 0.7 threshold (confirms the iter-v3/008 IC-redundancy drop hypothesis at runtime).

Highest cross-family ICs retained:
- `ema_spread_atr_20` × `btc_ret_14d`: 0.508
- `ema_spread_atr_20` × `vwap_dev_20`: 0.547
- `ema_spread_atr_20` × `sym_vs_btc_ret_7d`: 0.507

## Section 3.6 Reconciliation Verifiers

| # | Verifier | Result |
|---|---|---|
| 1 | `len(V3_FEATURE_COLUMNS) == 13` | PASS — run.log: `V3_FEATURE_COLUMNS: 13 columns  PASS` |
| 2 | `'vwap_dev_50' not in V3_FEATURE_COLUMNS` | PASS — 13-feature importance CSV has no `vwap_dev_50` row |
| 3 | `ITERATION_LABEL = "v3-009"` | PASS — SHA `43b3ed8` sets label; run.log banner confirms `iter-v3-009` |
| 4 | `comparison.csv` exists | PASS — file present with 14 headline rows + per-symbol section |
| 5 | IS monthly Sharpe > 0 | PASS — IS = +0.0802 > 0 (central EXPLORATION test passes) |
| 6 | 35/35 adversarial tests pass | PASS — `uv run pytest tests/strategies/ml/` → `35 passed in 90.27s` |
| 7 | Wall-clock < 120 min (target < 30 min) | PASS — 11 min (0.18h) |
| 8 | Active models: 4/4 | PASS — run.log: `Active models: 4/4 (--symbols=None)` |
| 9 | `--exploration` flag active | PASS — run.log: `Seeds: 1  Optuna trials/model: 10` + `CPCV: N=10, k=2, 45 paths` |
| 10 | `pareto_front.csv` has >= 1 row | PASS — 1 row (seed=42) |

All 10 verifiers PASS.

## Section 8 EXPLORATION Criteria Evaluation

| # | Criterion | Threshold | Status |
|---|---|---|---|
| 1 | TYPE=EXPLORATION declared in §0.5 | TRUE | PASS |
| 2 | Single-axis variation only (features) | TRUE | PASS — only change vs iter-v3/007 is 1 dropped feature; no label/symbol/gate changes |
| 3 | Wall-clock < 2h (target < 30 min) | TRUE | PASS — 11 min |
| 4 | `--exploration --seeds 1 --n-trials 10` used | TRUE | PASS — confirmed in runner invocation and run.log |
| 5 | 35/35 adversarial tests pass | TRUE | PASS — verified post-backtest |
| 6 | `len(V3_FEATURE_COLUMNS) == 13` at runtime | TRUE | PASS — run.log pre-flight confirms |
| 7 | `comparison.csv` produced | TRUE | PASS — all required rows present |
| 8 | Critic OVERALL = EXPLORATION-PROMISING or EXPLORATION-NEGATIVE (not BLOCK) | enum | PENDING (Phase 7.5) |
| 9 | NO 5-seed or CONFIRMATION-style runs | TRUE (vacuous) | PASS — seeds=1 |
| 10 | Catalog updated post-Phase-8 | TRUE | PENDING (post-Phase-8 mechanic) |

Criteria 1-7, 9 all PASS. Criteria 8 and 10 are pending Phase 7.5 and Phase 8 respectively. No process-level BLOCK conditions triggered.

**IS monthly Sharpe vs Section 4 falsifiers:**
- Falsifier 1 threshold: IS Sharpe < +0.10 → EXPLORATION-NEGATIVE. Actual IS = +0.0802 — this is **below +0.10**, which activates Falsifier 1.
- Falsifier 2 threshold: IS Sharpe > +0.40 — not triggered.
- Predicted band [+0.18, +0.28] per Section 4.2 — actual IS = +0.0802 is **below the predicted band**.

The IS result falls below Falsifier 1's +0.10 threshold, which per the brief means: `vwap_dev_50` was actually contributing independent signal. The EXPLORATION axis verdict (PROMISING vs NEGATIVE) is for the Critic to determine in Phase 7.5.

## Track Isolation Audit

From run.log pre-flight:

```
Track isolation (features_v3 does not import v1/v2): PASS
```

No v1 or v2 symbols in the v3 universe. `set({BCH, MKR, LDO, TRX}) ∩ V3_EXCLUDED_SYMBOLS = ∅` verified at runtime.

## Seed Concentration Audit (Single-Seed Exploration)

| Seed | OOS Monthly Sharpe | OOS Max DD (%) | N Trades | Max Concentration (%) |
|---:|---:|---:|---:|---:|
| 42 | +1.1223 | 37.90 | 87 | 98.61 |

Single-seed exploration run per cadence discipline. Concentration 98.61% driven by LDOUSDT (104.87% of OOS PnL, 12 trades). This is expected for an EXPLORATION iteration and is informational only (not a gate per Section 8 criteria).

## Anomaly Notes

**Anomaly 1 — IS drop, OOS rise (primary anomaly):**

IS monthly Sharpe dropped from +0.2241 (iter-v3/007, top-14) to +0.0802 (iter-v3/009, top-13), a delta of -0.144. Simultaneously, OOS monthly Sharpe rose from +0.0622 to +1.1223, a delta of +1.060. Raw values:

- IS: Sharpe=+0.0802, 267 trades, WR=37.08%, PF=1.0246, MaxDD=76.49%
- OOS: Sharpe=+1.1223, 87 trades, WR=45.98%, PF=1.3535, MaxDD=37.90%
- OOS/IS Sharpe ratio: 13.99

The IS/OOS ratio of ~14x is anomalously high. The IS result (barely above zero at +0.0802) falls below Falsifier 1's threshold of +0.10. The OOS result (+1.1223) is the highest OOS monthly Sharpe seen in the v3 track to date. No code changes were made to the backtest logic, risk gates, labeling, or data pipeline between iter-v3/007 and iter-v3/009. The only change is one feature dropped (`vwap_dev_50`). This divergence is documented as a raw observation; interpretation is reserved for the Critic (Phase 7.5).

**Anomaly 2 — Feature importance rank shift:**

`ema_spread_atr_20` rose from IS rank 4 (iter-v3/007) to IS rank 1 (iter-v3/009). `vwap_dev_20` rose from rank 10 to rank 4. Both features have high IC with the dropped `vwap_dev_50` (0.547 and 0.875 respectively in iter-v3/007's matrix), consistent with the hypothesis that `vwap_dev_50`'s IS importance was borrowing from these features rather than measuring independent signal. The redistribution of importance is factual — interpretation is for the Critic.

**Anomaly 3 — LDOUSDT OOS dominance:**

LDOUSDT accounts for 104.87% of OOS PnL (12 trades, 75% win rate). This is the same concentration dynamic seen in iter-v3/007 (BCH 84.44% OOS concentration), but with a different dominant symbol. OOS concentration at 98.61% in pareto_front.csv.

**Anomaly 4 — statsmodels divide-by-zero warning:**

run.log contains `RuntimeWarning: divide by zero encountered in log` from statsmodels `linear_model.py:955`. This warning appeared in prior iterations and is benign (occurs in OLS log-likelihood computation during ADF testing on near-constant series). It does not affect any reported metrics.

**Anomaly 5 — ADF missing entry for LDOUSDT/cusum_reset_count_200:**

run.log notes: `WARNING: LDOUSDT/cusum_reset_count_200 not found in ADF output`. This feature is not in `V3_FEATURE_COLUMNS` (the 13-feature list). It is a non-model feature present in the parquet that the ADF loop attempted to find but could not match. No impact on reported ADF rows or model outputs.

## Status

OVERALL: READY-FOR-CRITIC
