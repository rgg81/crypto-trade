# Engineering Report — iter-v3/082

## Headers

- Iteration: iter-v3/082
- Branch: iteration-v3/082
- Commit chain:
  - EDA: `37d4da8` — `analysis/iteration_v3-082/funding_family_eda.py` + 6 result CSVs
  - Brief: `275d24a`
  - Brief SHA-backfill: `222308e`
  - Phase 5.5 gate (initial BLOCK): `3cd8012`
  - Setup: `87195d1` — funding-rate feature family + config-accretion pre-flight
  - Phase 5.5 re-gate (PASS): `034d7e6` — test_v3_feature_count updated 14→18
  - OOF atomic-write fix: `a7abba4` — infra-only, metric-neutral
  - HEAD at report time: `a7abba4`
- Hardware: WSL2 / Linux 6.6.114.1-microsoft-standard-WSL2, x86_64, 60 GB RAM
- Wall-clock time: 0.74h (within 2.0h EXPLORATION cap)
- Run mode: EXPLORATION (`--exploration` flag) — `ENSEMBLE_SIZE=3`, 3-seed outer-42 lineage subset
- Run command: `uv run python run_baseline_v3.py --exploration --n-trials 35`
- Optuna budget: 35 trials × 3 symbols × 3 seeds = 315 trials total

---

## Implementation Summary

### The Axis

iter-v3/082 is cycle-3 EXPLORATION #1 (Direction 1). The single primary change is expanding `V3_FEATURE_COLUMNS` from 14 to 18 by adding a 4-member funding-rate feature family implemented in `src/crypto_trade/features_v3/funding_v3.py`:

| Feature | Description |
|---|---|
| `funding_sign_persist_9` | Count of consecutive same-sign funding-rate candles (window 9) — measures sustained positioning crowding |
| `funding_momentum_3` | 3-candle rolling sum of funding rate — short-horizon momentum in leverage cost |
| `funding_accel_3` | 3-candle second difference of funding rate — rate-of-change of funding momentum; shock detector |
| `funding_price_divergence_6` | Normalized divergence between 6-candle cumulative funding sum and price return — detects divergence setup |

The closed single-z-score feature `funding_rate_zscore_30` (tested at /019/023/024, importance rank 14/14 on all three occasions) stays absent. No labeling, symbol, risk-gate, or model-architecture changes.

### Commit Descriptions

- **`87195d1`** (`feat`): Created `src/crypto_trade/features_v3/funding_v3.py` implementing the 4 feature functions. Added all 4 features to `V3_FEATURE_COLUMNS` (14→18). Added a config-accretion pre-flight check verifying 11 knobs equal the /059 canonical baseline. Updated `ITERATION_LABEL = "v3-082"`.
- **`034d7e6`** (`fix`): Updated `tests/test_v3_feature_count.py` from 14 to 18 to reflect the expanded column list. This also resolved the initial Phase 5.5 BLOCK (`3cd8012`), which was caused by the test asserting 14 columns when the runner now expected 18.
- **`a7abba4`** (`fix`, infra-only): Replaced in-place `to_parquet` writes for `trial_oof_returns.parquet` with an atomic temp-file + `os.replace` pattern. Metric-neutral — the fix only addresses file-integrity safety; no model parameters or feature columns changed.

---

## Backtest Detour

The clean run (#3) that produced all reported numbers was preceded by two failed launches.

**Launch #1 — stale-OOF guard:** The runner detected a stale `trial_oof_returns.parquet` from a prior iteration and refused to proceed. Resolution: the file was removed and the run was re-launched.

**Launch #2 — parquet corruption:** Launch #2 ran briefly and then a concurrent process read the OOF parquet while it was being written in-place, producing a corrupted file ("magic bytes" / "end of stream" errors). Root cause: `pandas.DataFrame.to_parquet` truncates and rewrites the file non-atomically; a concurrent read between truncation and final flush reads an empty or partial file.

**Fix (`a7abba4`):** The write path was replaced with `df.to_parquet(tmp_path); os.replace(tmp_path, final_path)`. `os.replace` is atomic on Linux (POSIX rename guarantee). Readers either see the fully-written old file or the fully-written new file — no partial-write window. This is a pure infra fix; it does not affect any model weight, feature value, or metric.

**Launch #3 (clean run):** Completed with exit code 0, wall-clock 0.74h. All numbers in this report are from launch #3.

---

## Run Integrity

| Check | Result |
|---|---|
| `grep -c "Optimization failed" run.log` | **0** |
| `grep -c "magic bytes\|end of stream\|Traceback" run.log` | **0** |
| `trial_oof_returns.parquet` readable | **YES** (24,013,976 rows) |
| `n_trials` in `dsr.json` | **315** (expected: 35 × 3 symbols × 3 seeds = 315) |
| Pre-flight: V3_FEATURE_COLUMNS count | **18 PASS** |
| Pre-flight: config-accretion (11 knobs == /059) | **PASS** |
| Pre-flight: label-leakage gap | **66 = (21+1) × 3 PASS** |
| Pre-flight: track isolation | **PASS** |
| Pre-flight: branch + data freshness | **PASS** |
| Zero-trade months IS | **0** (35 months with trades) |
| Zero-trade months OOS | **0** (14 months with trades) |
| NaN Sharpe | **none** |

Ensemble: 3 seeds, all outer-42 lineage (`[191664963, 1662057957, 1405681631]`). Mode: `exploration`.

---

## Configuration Diff vs /059 Baseline

```
V3_FEATURE_COLUMNS: 14 → 18
  ADDED: funding_sign_persist_9, funding_momentum_3, funding_accel_3, funding_price_divergence_6
  REMOVED: (none)
ITERATION_LABEL: "v3-059" → "v3-082"
```

All 11 tracked risk-gate knobs equal the /059 canonical baseline (config-accretion PASS):
`DEFAULT_ATR_MULTIPLIERS`, `V3_FEATURES_PER_SYMBOL`, `V3_ATR_MULTIPLIERS_PER_SYMBOL`, `block_long_for`, `block_short_for`, `enable_regime_size_scalar`, `REQUIRED_GAP`, `label_mode`, `inference_threshold_floor`, `vol_scale_ceiling`, `Universal label_timeout_minutes`.

---

## Headline Metrics

Mode note: /082 is EXPLORATION-mode (3 seeds); /059 anchor is CONFIRMATION-mode (10 seeds). Direct numeric comparison carries mode-mismatch noise; the QR handles this in Phase 7.

| Metric | IS | OOS | OOS/IS ratio |
|---|---:|---:|---:|
| monthly_sharpe | +1.0776 | +1.7872 | 1.6585 |
| daily_sharpe | +1.8908 | +3.5478 | 1.8763 |
| max_drawdown (%) | 18.92 | 31.48 | 1.6639 |
| profit_factor | 1.3221 | 1.5502 | 1.1725 |
| win_rate (%) | 30.68 | 44.94 | 1.4648 |
| n_trades | 176 | 89 | 0.5057 |
| total_pnl (%) | 55.28 | 53.62 | 0.9701 |
| monthly_calmar | 2.9221 | 1.7036 | 0.5830 |

**DSR/PBO/PSR block:**

| Metric | Value |
|---|---:|
| DSR | 0.0000 |
| PBO | 0.1284 |
| PSR | 1.0000 |
| frac_positive_paths | 0.6444 |
| CPCV path Sharpe q25 / q50 / q75 | -0.243 / +0.335 / +0.838 |
| n_trials | 315 |
| n_eff | 19 |

DSR=0.0000: EXPLORATION-mode structural artifact per `feedback_v3_dsr_mode_artifact.md`. At n_trials=315, E[max_SR] > observed annualized Sharpe → DSR collapses. Informational only; CONFIRMATION-mode DSR (n_trials≈3150) is the gate-relevant metric.

**Delta vs /059 anchor (IS +1.0894 / OOS +0.5791):**

| Window | /059 anchor | /082 | Delta |
|---|---:|---:|---:|
| IS monthly Sharpe | +1.0894 | +1.0776 | **-0.0118** |
| OOS monthly Sharpe | +0.5791 | +1.7872 | **+1.2081** |

**Trade-level (daily Sharpe from run.log):**

| Window | Daily Sharpe | WR | PF | MaxDD |
|---|---:|---:|---:|---:|
| IS | 0.7183 | 36.9% | 1.3221 | 18.92% |
| OOS | 1.5454 | 46.1% | 1.5502 | 31.48% |

---

## Per-Symbol Breakdown

### In-Sample

| Symbol | Trades | Wins | WR | Net PnL (%) | % of Total IS PnL |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 80 | 35 | 43.8% | +68.65 | +162.2% |
| TRXUSDT | 82 | 27 | 32.9% | -1.22 | -2.9% |
| LDOUSDT | 14 | 3 | 21.4% | -25.09 | -59.3% |

IS total PnL: +42.34% (from per_symbol.csv net_pnl_pct sum). Note: comparison.csv total_pnl=55.28 is weighted_pnl_total; per_symbol net_pnl_pct are unweighted gross.

### Out-of-Sample

| Symbol | Trades | Wins | WR | Net PnL (%) | % of Total OOS wpnl |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 40 | 23 | 57.5% | +84.11 | **+110.2%** |
| TRXUSDT | 36 | 14 | 38.9% | +2.39 | +3.1% |
| LDOUSDT | 13 | 4 | 30.8% | -10.21 | -13.4% |

Top-symbol OOS PnL concentration: BCH = **110.2%** of total OOS weighted_pnl (53.62% total; BCH contributes 55.60 of that). LDO is a net detractor at -13.4%.

---

## Funding-Feature Importance Ranks

From `conditional_orthogonality.csv` `last_month_importance_share_portfolio` (last walk-forward month, portfolio-pooled):

| Rank | Feature | Importance Share |
|---|---|---:|
| 1 | max_dd_window_50 | 0.0892 |
| 2 | ret_skew_200 | 0.0871 |
| 3 | vwap_dev_20 | 0.0766 |
| 4 | range_realized_vol_50 | 0.0751 |
| 5 | ema_spread_atr_20 | 0.0724 |
| 6 | ret_kurt_50 | 0.0663 |
| 7 | ret_autocorr_lag1_50 | 0.0651 |
| 8 | ret_kurt_200 | 0.0582 |
| 9 | ret_skew_50 | 0.0559 |
| 10 | hurst_diff_100_50 | 0.0539 |
| 11 | hurst_100 | 0.0529 |
| 12 | btc_ret_14d | 0.0526 |
| 13 | sym_vs_btc_ret_7d | 0.0518 |
| 14 | regime_momentum_signed_5d | 0.0439 |
| **15** | **funding_price_divergence_6** | **0.0376** |
| **16** | **funding_sign_persist_9** | **0.0240** |
| **17** | **funding_momentum_3** | **0.0189** |
| **18** | **funding_accel_3** | **0.0185** |

The 4 funding features occupy ranks 15–18 (bottom 4 of 18). Combined share: 0.0376 + 0.0240 + 0.0189 + 0.0185 = **0.0990** (9.90% of total importance across 18 features). Uniform split across 18 features would assign each 5.56%; the 4 funding features average 2.475% each vs the 5.56% uniform baseline — below-parity allocation.

Note: `conditional_orthogonality.csv` sources are listed as `PART_A_runner_only (EDA T3 not found)` for the 4 funding features, meaning the EDA T3 regime-conditional data was not merged into this output. The importance shares are from the runner's last walk-forward month only (PART A).

---

## Funding-Feature IC vs Anchor Stack

From `ic_matrix.csv` (pooled, all symbols and dates):

| Feature | Max |IC| vs 14 anchors | Highest-correlated anchor |
|---|---:|---|
| funding_sign_persist_9 | **0.2182** | `btc_ret_14d` |
| funding_momentum_3 | **0.0803** | `vwap_dev_20` |
| funding_accel_3 | **0.0118** | `ema_spread_atr_20` |
| funding_price_divergence_6 | **0.2197** | `vwap_dev_20` (negative: -0.220) |

All 4 are well below the hard gate (|IC| < 0.70) and the strict target (< 0.50). Maximum across all 4: **0.2197**.

Intra-family IC note: `funding_momentum_3` vs `funding_accel_3` = **0.816** in the runner-computed pooled matrix (vs 0.73–0.77 in the IS-only EDA). This is the highest intra-family correlation; the brief pre-registered this as a momentum/second-difference pair (Category-2 carve-out precedent).

---

## ADF Stationarity

Stationarity pass rate (p < 0.05) for the 4 funding features, pooled across all symbols and IS months (628 non-null obs total):

| Feature | Pass / Total | Pass Rate |
|---|---|---:|
| funding_accel_3 | 152 / 157 | **96.8%** |
| funding_momentum_3 | 152 / 157 | **96.8%** |
| funding_price_divergence_6 | 146 / 157 | **93.0%** |
| funding_sign_persist_9 | 141 / 157 | **89.8%** |
| **All 4 combined** | **591 / 628** | **94.1%** |

All 4 features are stationary by ADF in the overwhelming majority of IS months. `funding_sign_persist_9` has the lowest pass rate at 89.8% — still above the standard 80% threshold used in v3.

---

## Spot-Check Anomaly Notes

5 random OOS trades verified (seed 7):

| Trade | Symbol | Direction | Exit | PnL | PnL Check |
|---|---|---|---|---:|---|
| idx=41 | TRXUSDT | LONG | take_profit | +3.9292% | expected +3.9294% — OK (rounding) |
| idx=19 | BCHUSDT | LONG | take_profit | +6.9557% | expected +6.9557% — OK |
| idx=50 | TRXUSDT | LONG | stop_loss | -1.6153% | expected -1.6154% — OK |
| idx=83 | TRXUSDT | LONG | take_profit | +1.9120% | expected +1.9119% — OK |
| idx=6 | BCHUSDT | SHORT | stop_loss | -3.6485% | expected -3.6485% (confirmed: SL=407.256, (entry-SL)/entry) — OK |

No anomalies. Exit prices equal SL/TP prices exactly; weight_factors are in (0, 1]; exit reasons are consistent with price levels.

---

## Status

OVERALL=READY-FOR-CRITIC
