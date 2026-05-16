# Engineering Report — iter-v3/083

## Headers
- Iteration: iter-v3/083
- Branch: iteration-v3/083
- Commit SHA (backtest): 17ef604 (setup commit, pre-backtest)
- Hardware: WSL2 / AMD Ryzen (multi-core)
- Wall-clock time: 1.00h
- Mode: EXPLORATION (--exploration, --seeds 1, ensemble_size=3, n_trials=35)

---

## Configuration Diff vs Baseline (/059)

| Parameter | /059 Baseline | /083 This Run |
|---|---|---|
| V3_MODELS (symbols) | BCH, LDO, TRX | BCH, LDO, TRX, **FIL** |
| REQUIRED_GAP | 66 (3 symbols × 22) | **88** (4 symbols × 22) |
| Feature set | 14 features (/059 anchor) | 14 features (funding revert) |
| V3_FEATURES_PER_SYMBOL | {} | {} |
| V3_ATR_MULTIPLIERS_PER_SYMBOL | {} (all DEFAULT) | {} (all DEFAULT) |
| Per-symbol ADX threshold | {} | {} |
| Per-symbol vol_scale_floor | {} | {} |
| n_trials | 35 | 35 |
| outer_seeds | 1 | 1 |
| inner ensemble_size | 3 | 3 |
| OOS_CUTOFF_DATE | 2025-03-24 | 2025-03-24 (unchanged) |
| training_months | 24 | 24 (unchanged) |

Note: /082's funding_rate_zscore_30 feature addition was reverted; /083 runs on the identical 14-feature stack as /059.

---

## Run Integrity Verification

| Check | Result |
|---|---|
| `grep -c "Optimization failed"` | 0 |
| `grep -c "magic bytes\|end of stream\|Traceback"` | 0 |
| `trial_oof_returns.parquet` readable | PASS (shape 32,301,886 × 6, NaN=False) |
| n_trials | 420 = 35 × 4 symbols × 3 months (EXPLORATION window) |
| Symbols in run | BCHUSDT, LDOUSDT, TRXUSDT, FILUSDT |
| REQUIRED_GAP | 88 = (timeout_candles=21+1) × n_symbols=4 — MATCHES run.log |
| Feature columns | 14 — PASS |
| Config-accretion check | "11 knobs verified (V3_MODELS=4-sym + REQUIRED_GAP=88 = /083 axis; 9 knobs == /059)" — PASS |
| Data freshness | "<16h" — PASS |
| Branch check | PASS |
| V3_FEATURES_PER_SYMBOL | "0 entries (all symbols use 14-feature fallback)" — PASS |
| ADF error | FILUSDT/max_dd_window_50/2020-11: "Invalid input, x is constant" — 1 cell skipped, benign (FIL data sparse in 2020-11) |
| Exit code | 0 (clean) |

**Verdict: RUN INTEGRITY PASS.**

---

## Key Metrics Block (comparison.csv)

| Metric | IS | OOS | Ratio | /059 IS | /059 OOS | Δ IS | Δ OOS |
|---|---|---|---|---|---|---|---|
| monthly_sharpe | 0.1738 | 0.4394 | 2.5276 | 1.0894 | 0.5791 | **-0.9156** | -0.1397 |
| daily_sharpe | 0.3996 | 1.0029 | 2.5095 | 2.7092 | 1.4359 | -2.3096 | -0.4330 |
| max_drawdown | 73.18% | 33.58% | 0.459 | 30.97% | 34.53% | **+42.21pp** | -0.95pp |
| profit_factor | 1.0585 | 1.1289 | 1.0665 | 1.4949 | 1.2107 | -0.436 | -0.082 |
| win_rate | 31.51% | 39.69% | 1.260 | 33.33% | 38.30% | -1.82pp | +1.39pp |
| n_trades | 219 | 131 | 0.598 | 171 | 94 | +48 | +37 |
| total_pnl | 18.01 | 19.75 | 1.097 | 78.18 | 22.74 | -60.17 | -2.99 |
| monthly_calmar | 0.2461 | 0.5881 | 2.390 | 2.5246 | 0.6585 | -2.279 | -0.070 |
| dsr | 0.0 | — | — | 0.0 | — | — | — |
| pbo | 0.1392 | — | — | 0.1278 | — | +0.011 | — |
| psr | 1.0000 | — | — | 1.0000 | — | 0 | — |
| n_trials | 420 | — | — | 1050 | — | — | — |
| n_effective_trials | 19 | — | — | 19 | — | 0 | — |

CPCV gate: frac_positive_paths = 0.467 (threshold 0.55) — **FAIL**. 21 of 45 CPCV paths positive.

DSR = 0.0 is EXPLORATION artifact (n_trials=420 vs CONFIRMATION n_trials=1050+); not comparable to CONFIRMATION-mode DSR.

CPCV path Sharpe distribution: q25=-0.706, q50=-0.079, q75=+0.440. Median path is negative — directional reversal to /059.

---

## Per-Symbol IS/OOS Breakdown

### IS (In-Sample, report-layer per_symbol.csv)

| Symbol | Trades | WR | Net PnL% | Avg PnL% | Approx Monthly Sharpe |
|---|---|---|---|---|---|
| BCHUSDT | 73 | 45.2% | +79.45% | +1.09% | +0.33 |
| FILUSDT | 60 | 36.7% | **-32.45%** | -0.54% | -0.09 |
| LDOUSDT | 11 | 27.3% | -11.44% | -1.04% | -0.15 |
| TRXUSDT | 75 | 29.3% | **-23.04%** | -0.31% | -0.12 |

Portfolio IS total_pnl ≈ +12.5 net (BCH dominates, three others net negative).

### OOS (Out-of-Sample, report-layer per_symbol.csv)

| Symbol | Trades | WR | Net PnL% | Avg PnL% | comparison.csv concentration_pct |
|---|---|---|---|---|---|
| TRXUSDT | 55 | 49.1% | +32.28% | +0.59% | +121.92% |
| FILUSDT | 27 | 44.4% | +17.65% | +0.65% | +32.11% |
| BCHUSDT | 37 | 32.4% | -8.69% | -0.24% | +9.66% |
| LDOUSDT | 12 | 25.0% | -15.80% | -1.32% | -63.68% |

---

## Core Diagnostic: FIL's Own Trades vs Incumbent Perturbation

**Verdict: BOTH — FIL's own trades are destructive IS, AND the incumbents were perturbed.**

### FIL's own IS trades

FIL contributed 60 IS trades at -32.45% net PnL, approximate monthly Sharpe -0.09. The worst FIL months were:
- 2023-01: -17.08% (3 trades)
- 2023-03: -21.88% (3 trades)
- 2023-11: -28.74% (7 trades — largest single-month loss)
- 2023-12: +17.10%, 2024-01: +20.11% (FIL briefly profitable)
- 2024-03: -13.90% (5 trades)

FIL's IS edge is negative at the 14-feature anchor. The QR's IS-edge screen predicted -0.038 aggregate IS Sharpe Δ from adding FIL; the realized IS Δ is -0.9156 — a ~24× miss. The screen used pooled-portfolio correlation as a proxy for per-symbol model performance; that proxy failed to capture FIL's negative contribution to IS Sharpe.

### Incumbent perturbation

Comparing IS per-symbol stats /083 vs /059 (the 3-symbol anchor):

| Symbol | /059 IS trades | /059 WR | /059 net_pnl% | /083 IS trades | /083 WR | /083 net_pnl% |
|---|---|---|---|---|---|---|
| BCH | 83 | 49.4% | +109.23% | 73 | 45.2% | +79.45% |
| LDO | 9 | 33.3% | +0.89% | 11 | 27.3% | -11.44% |
| TRX | 79 | 34.2% | +3.95% | 75 | 29.3% | **-23.04%** |

BCH: trade count fell from 83 to 73 (-10), WR fell from 49.4% to 45.2%, net PnL fell from +109% to +79%. BCH IS degraded but remained the sole positive contributor.

TRX: the critical perturbation. TRX flipped from +3.95% net IS (marginal positive at /059) to -23.04% net IS at /083. Win rate fell from 34.2% to 29.3%. The 75 trades at -0.31% avg = systematic drag. TRX's Optuna-selected hyperparameters at the 4-symbol landscape differ from those at 3-symbol; the confidence_threshold and training_days at the new per-month optima lean toward regimes where TRX loses more consistently.

LDO: 11 trades, -11.44% net. /059 had only 9 trades with marginal +0.89%; LDO is structurally low-edge but the new optima tilted it further negative.

**Attribution summary:**
- FIL direct contribution: -32.45% net IS PnL, 60 trades — negative-edge symbol
- TRX perturbation: -23.04% net IS PnL vs +3.95% at /059 — Δ ≈ -27% from incumbent reshaping
- LDO perturbation: -11.44% vs +0.89% at /059 — Δ ≈ -12%
- BCH perturbation: +79.45% vs +109.23% — Δ ≈ -30% (still positive, attenuated)

Adding FIL reshaped the Optuna landscape for all 3 incumbents. The IS Sharpe collapse is explained by approximately equal contributions from FIL's own negative IS edge (-32.45%) and the aggregate incumbent Optuna-reshaping (-69%).

---

## 73.18% IS MaxDD Localization

The IS MaxDD peak-to-trough ran from 2022-02-10 to 2024-01-08 — a 23-month drawdown window.

Within that window, per-symbol IS PnL:
- BCH: +5.61% (45 trades, net positive — BCH sustained the portfolio through the DD)
- FIL: **-43.43%** (27 trades — primary DD driver)
- TRX: -10.86% (34 trades — secondary DD driver)
- LDO: not trading in early portion (LDO data begins 2024-09)

The worst individual months driving the 73% DD:
- 2023-11: -30.03% (13 trades) — dominated by FIL -28.74% + TRX -2.47%
- 2023-03: -22.32% (12 trades) — FIL -21.88% + TRX -6.21%
- 2024-03: -12.56% (10 trades) — FIL -13.90% + TRX -10.66%
- 2024-02: -8.50% (7 trades) — FIL -5.49% + TRX -4.78%

**FIL is the primary architect of the 73% IS MaxDD.** FIL contributed -43.43% over the 23-month DD window (vs FIL's full-IS net of -32.45%, meaning FIL was also negative outside this window). The /059 3-symbol baseline had IS MaxDD of 30.97% — the +42pp increase is attributable to FIL's losses clustered in 2023-03, 2023-11, and 2024-Q1.

The ADF one-cell error (FILUSDT/max_dd_window_50/2020-11: constant input) was benign — FIL data was sparse in that month; the cell was skipped and the remaining 735 FIL cells tested normally (82.6% stationary).

---

## Concentration Diagnostic

**BCH IS concentration**: comparison.csv shows BCH IS weighted_pnl = +1.91 (concentration_pct = 9.66%) — this is out of a near-zero total IS weighted_pnl (+18.0). The 9.66% headline understates BCH's role because TRX and FIL cancel most of BCH's gains. In absolute trade-PnL terms, BCH contributed +79.45% net while the rest was -66.93% aggregate.

**BCH OOS concentration**: comparison.csv shows BCH OOS concentration_pct = 9.66% (weighted_pnl = +1.91 of total +19.75). OOS is led by TRX (121.92%) and FIL (32.11%).

**Goal assessment**: The Direction-2 axis aimed to dilute BCH's dominance (BCH was 108.86% of IS wpnl at /059). This succeeded at the OOS level (BCH fell from dominance, TRX and FIL took over). However, the IS concentration did not improve in the healthy sense — BCH's IS contribution remained the only positive anchor while FIL and TRX became strongly negative, producing a near-zero total IS wpnl that makes the 9.66% concentration figure meaningless as a ratio.

---

## Screen vs Reality Gap

The QR's IS-edge screen (analysis commit `e538d5f`) predicted an aggregate IS Sharpe Δ of -0.038 from adding FILUSDT. Realized IS Δ = -0.9156. The 24× miss has two components:

1. **FIL's own IS model is negative.** The screen assessed FIL via pooled cross-asset IC of its 14 features with labels; it did not evaluate FIL's per-month Optuna outcome under the fixed 35-trial budget. FIL's IS edge at n_trials=35 single-seed is negative (-0.09 monthly Sharpe approximation), not the implied positive from cross-asset feature IC.

2. **Optuna landscape reshaping for incumbents.** Adding a 4th symbol changes the per-cell training-sample distribution and Optuna search dynamics for BCH, LDO, and TRX. The screen treated FIL's contribution as additive-independent; the realized effect was non-additive: TRX IS flipped from +3.95% to -23.04%, a -27% swing not captured in the screen.

The screen methodology captures feature stationarity and symbol-level IC but does not simulate the joint Optuna-search effect of expanding the symbol universe. This is a factual gap in the screening methodology; interpretation is QR/Critic's domain.

---

## ADF Stationarity Summary

Total cells tested: 2,954. Stationary (p<0.05): 2,411 (81.6%).

| Symbol | Cells tested | Stationary | % Stationary |
|---|---|---|---|
| BCHUSDT | 863 | 726 | 84.1% |
| FILUSDT | 736 | 608 | 82.6% |
| LDOUSDT | 404 | 331 | 81.9% |
| TRXUSDT | 863 | 746 | 86.4% |

1 ADF error: FILUSDT/max_dd_window_50/2020-11 (constant input, benign).

FIL's 82.6% stationarity rate is comparable to BCH (84.1%) — the feature set is stationary across all 4 symbols. ADF stationarity did not differentiate FIL from the incumbents; the IS edge gap is not a feature-stationarity issue.

---

## Feature Importance (Last Month)

| Rank | FIL | BCH | TRX |
|---|---|---|---|
| 1 | btc_ret_14d (110) | vwap_dev_20 (250) | ret_skew_200 (259) |
| 2 | ret_autocorr_lag1_50 (104) | max_dd_window_50 (225) | hurst_100 (242) |
| 3 | ret_skew_50 (102) | range_realized_vol_50 (213) | ret_autocorr_lag1_50 (218) |
| 14 | regime_momentum_signed_5d (50) | hurst_100 (114) | ret_kurt_200 (84) |

FIL's importance distribution is more uniform (top feature 110 vs BCH top 250) and regime_momentum_signed_5d ranks last for FIL (50.3 units), suggesting the anchor's primary edge feature has reduced signal for FIL.

IC matrix: highest pairwise IC = vwap_dev_20 / regime_momentum_signed_5d = 0.773 (pre-existing, Category 2 carve-out); sym_vs_btc_ret_7d / regime_momentum_signed_5d = 0.646; ema_spread_atr_20 / regime_momentum_signed_5d = 0.615. No new collinearity introduced by FIL's addition.

---

## Seed Concentration Audit

Single-seed EXPLORATION (outer_seed=42, ensemble_size=3). No multi-seed pareto available. Seeds: [191664963, 1662057957, 1405681631] (lineage outer=42).

---

## Label Leakage Audit

REQUIRED_GAP = 88 = (timeout_candles=21+1) × n_symbols=4. Confirmed by run.log: "Label-leakage gap: (timeout_candles=21+1) * n_symbols=4 = 88 [matches REQUIRED_GAP=88] PASS". CV folds logged at 184h gap (22 rows × 4 symbols at 8h interval = 176h minimum; 184h observed is within tolerance).

---

## Gate Efficacy

Per-regime: all 219 IS trades classified as "unknown" regime. Regime gate produces no segmentation with the current Hurst-based classifier on the 4-symbol pool.

Risk gates (vol-scaled sizing, ADX, confidence threshold): fire rates not separately logged for this EXPLORATION run; gate config unchanged from /059.

---

## Anomaly Notes

- The `pct_of_total_pnl` column for BCH IS shows 634.73% — this is a mathematical artifact of a near-zero IS total_pnl denominator (+12.52 net from 4 symbols, with BCH at +86.75 offset by others -74.23). Not a bug; the ratio is correct and expected when total approaches zero.
- CPCV path Sharpe q50 = -0.079 (median path negative). Path 17 = -2.107 and path 28 = -1.991 are outlier-negative; path 13 = +1.757 and path 14 = +1.706 are outlier-positive. High path dispersion (range: -2.11 to +1.76) indicates regime-dependent instability.
- FIL CPCV (per_cell_pbo): mean_path_sharpe is predominantly negative from 2024-Q4 onward, positive cluster in 2022-Q4 through 2024-Q1. This temporal structure confirms FIL IS edge was period-specific, not durable.
- 10 random IS trade rows spot-checked: entry/exit/PnL math consistent; exit_reason values are stop_loss, take_profit, timeout; no malformed rows detected.

---

## Status

OVERALL=READY-FOR-CRITIC
