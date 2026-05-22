# Engineering Report — iter-v3/087

## Headers

- Iteration: iter-v3/087
- Type: EXPLORATION (cycle-3, #6)
- Branch: iteration-v3/087
- Setup commit: 0d9a5e4
- Phase 5.5 gate PASS commit: 8d8253f
- Hardware: WSL2 Linux / Roberto
- Wall-clock time: 1.55h
- Run log: `reports-v3/iteration_v3-087/run.log`

---

## Configuration Diff vs /084 Anchor (Cycle-3 EXPLORATION-mode reference)

| Knob | /084 (anchor) | /087 |
|---|---|---|
| V3_MODELS (symbols) | BCH / LDO / TRX (3) | BCH / LDO / TRX / GALA / MANA / SAND (6) |
| REQUIRED_GAP | 66 | 132 (= (21+1) × 6 — label-leakage gap correct) |
| PER_CELL_GAP | 11 | 22 (= 132 / 6) |
| Feature columns | 14 — /059 anchor | 14 — /059 anchor (basis REVERTED per /086 Rec #3) |
| Ensemble size | 3 | 3 |
| n_trials / model | 35 | 35 |
| Seeds (outer) | 1 (seed=42) | 1 (seed=42) |
| OOS_CUTOFF_DATE | 2025-03-24 | 2025-03-24 (UNCHANGED) |
| training_months | 24 | 24 (UNCHANGED) |
| ATR multipliers | all DEFAULT (2.0, 1.0) | all DEFAULT (2.0, 1.0) for all 6 |
| ADX threshold | 20.0 global | 20.0 global |
| Per-symbol features | {} empty | {} empty |
| Per-symbol labels | {} empty | {} empty |

The sole axis is the 3→6 wholesale universe expansion. Basis features (basis_zscore_30, basis_momentum_3, basis_extreme_flag) are absent; all 9 /063-NEW features are absent. The /059-canonical 14-feature stack runs unchanged.

---

## Run Integrity Verification

| Check | Result |
|---|---|
| "Optimization failed" count | 0 |
| "magic bytes / end of stream / Traceback" count | 0 |
| `trial_oof_returns.parquet` readable | PASS (shape: 45 355 072 × 6) |
| n_trials | 630 = 35 × 6 symbols × 3 ensemble seeds — CORRECT |
| 6 symbols active | PASS (BCH / LDO / TRX / GALA / MANA / SAND) |
| REQUIRED_GAP | 132 = (timeout_candles=21 + 1) × n_symbols=6 — CORRECT |
| OOS_CUTOFF_DATE | 2025-03-24 — UNCHANGED |
| training_months | 24 — UNCHANGED |
| Feature columns | 14 — explicit list, basis absent, all 9 /063-NEW absent |
| Basis absent | PASS (basis_zscore_30 / basis_momentum_3 / basis_extreme_flag all absent) |
| Sacred-constant check | PASS (Train window: 2023-04-01 → 2025-03-24 confirmed in log) |
| Pre-flight (data freshness, branch, feature-cols=14) | PASS |
| Exit code | 0 |
| Wall-clock | 1.55h |

Spot-check of 10 random OOS trade rows: entry/exit/pnl math consistent; exit_reason is stop_loss or take_profit; weight_factor in (0, 1] range; no NaN fields. Zero anomalies.

---

## Key Metrics Block — /087 vs /084 (Cycle-3 Exploration-Mode Reference)

| Metric | /084 IS | /087 IS | /084 OOS | /087 OOS | /087 IS/OOS ratio |
|---|---|---|---|---|---|
| Monthly Sharpe | +0.8325 | +0.9208 | +0.3322 | -0.5027 | -0.5460 |
| Daily Sharpe | — | +2.1267 | — | -0.9112 | -0.4285 |
| Max Drawdown | — | 61.78% | — | 76.42% | 1.2368 |
| Profit Factor | — | 1.3429 | — | 0.8961 | 0.6673 |
| Win Rate | — | 34.3% | — | 35.0% | 1.0211 |
| n_trades | — | 283 | — | 180 | 0.6360 |
| Total PnL | — | +128.16 | — | -29.14 | -0.2274 |
| Monthly Calmar | — | +2.0743 | — | -0.3813 | -0.1838 |
| Weighted PnL | — | +128.16 | — | -29.14 | — |
| DSR | — | 0.0 | — | — | — |
| PBO | — | 0.1230 | — | — | — |
| PSR | — | 0.0 | — | — | — |
| n_trials | — | 630 | — | — | — |
| n_eff | — | 19 | — | — | — |

Delta vs /084 anchor: IS Δ = **+0.0883** (slight IS lift), OOS Δ = **-0.8349** (large OOS collapse).

---

## Per-Symbol IS vs OOS Breakdown — Core Diagnostic

### IS per-symbol (net_pnl_pct from `in_sample/per_symbol.csv`)

| Symbol | IS Trades | IS Wins | IS WR% | IS Net PnL% | IS Avg PnL% |
|---|---|---|---|---|---|
| MANAUSDT | 55 | 27 | 49.1 | +101.56 | +1.85 |
| BCHUSDT | 73 | 33 | 45.2 | +79.45 | +1.09 |
| GALAUSDT | 28 | 13 | 46.4 | +67.20 | +2.40 |
| LDOUSDT | 11 | 3 | 27.3 | -11.44 | -1.04 |
| SANDUSDT | 41 | 15 | 36.6 | -18.10 | -0.44 |
| TRXUSDT | 75 | 22 | 29.3 | -23.04 | -0.31 |

### OOS per-symbol (net_pnl_pct from `out_of_sample/per_symbol.csv`)

| Symbol | OOS Trades | OOS Wins | OOS WR% | OOS Net PnL% |
|---|---|---|---|---|
| TRXUSDT | 55 | 28 | 50.9 | +33.33 |
| BCHUSDT | 37 | 12 | 32.4 | -8.69 |
| LDOUSDT | 12 | 3 | 25.0 | -15.80 |
| GALAUSDT | 24 | 7 | 29.2 | -18.98 |
| MANAUSDT | 31 | 8 | 25.8 | -27.16 |
| SANDUSDT | 21 | 6 | 28.6 | -28.07 |

### IS-vs-OOS per-symbol sign matrix

| Symbol | Status | IS PnL% | OOS PnL% | IS WR | OOS WR | Sign flip? |
|---|---|---|---|---|---|---|
| TRXUSDT | Incumbent | -23.04 | +33.33 | 29.3% | 50.9% | YES — IS-negative, OOS-positive |
| BCHUSDT | Incumbent | +79.45 | -8.69 | 45.2% | 32.4% | YES — IS-positive, OOS-negative |
| LDOUSDT | Incumbent | -11.44 | -15.80 | 27.3% | 25.0% | Consistent negative |
| GALAUSDT | NEW | +67.20 | -18.98 | 46.4% | 29.2% | YES — IS-positive, OOS-negative |
| MANAUSDT | NEW | +101.56 | -27.16 | 49.1% | 25.8% | YES — IS-positive, OOS-negative |
| SANDUSDT | NEW | -18.10 | -28.07 | 36.6% | 28.6% | Consistent negative |

---

## New-Symbol IS-Overfit Diagnostic

All three new symbols (GALAUSDT, MANAUSDT, SANDUSDT) were IS-positive in the EDA. In the full IS window:

- GALA: IS +67.20% / OOS -18.98% — sign inversion, WR collapse 46.4% → 29.2%
- MANA: IS +101.56% / OOS -27.16% — largest IS contributor; largest OOS loser by absolute loss; WR collapse 49.1% → 25.8%
- SAND: IS -18.10% / OOS -28.07% — IS was also negative (the EDA's prediction of positive IS edge for SAND was not confirmed in the full backtest)

GALA and MANA fit the textbook positive-IS / negative-OOS IS-overfit pattern. SAND was IS-negative in the full backtest (the EDA used a restricted IS window that showed edge; the full 24-month IS window did not replicate it). The MANA IS-to-OOS swing is the largest in magnitude of any single symbol in v3 history at this iteration.

From `comparison.csv` weighted PnL per symbol (which uses portfolio-level scaling):

| Symbol | Weighted PnL (total) | Concentration% |
|---|---|---|
| TRXUSDT | +24.54 | -84.23% |
| BCHUSDT | +1.91 | -6.55% |
| GALAUSDT | -5.73 | +19.68% |
| LDOUSDT | -12.58 | +43.17% |
| MANAUSDT | -14.70 | +50.44% |
| SANDUSDT | -22.58 | +77.49% |

Note: concentration_pct is relative to TRXUSDT's OOS contribution (TRXUSDT is the only OOS-profitable symbol and serves as the denominator; negative concentration entries reflect incumbents' positive contributions relative to the portfolio's net negative).

---

## Incumbent Shift Assessment

The three incumbents (BCH/LDO/TRX) changed materially vs /084's baseline IS behaviour:

- **TRXUSDT** inverted: IS -23.04% (negative) but OOS +33.33% (positive, 50.9% WR). In /084, TRX was the primary OOS contributor. The IS-negative / OOS-positive pattern persists for TRX; this is a structural characteristic of TRX that the model fails to fit in IS but which generalises. REQUIRED_GAP doubling (66→132) and the 3 new symbols co-training introduced no visible degradation for TRX in OOS.
- **BCHUSDT** sign-flipped IS→OOS: IS +79.45% but OOS -8.69%. In /084 single-seed BCH was OOS-negative as well; this incumbent-negative OOS pattern is consistent with prior cycles.
- **LDOUSDT**: IS -11.44%, OOS -15.80% — both negative, consistent with /084 incumbent behaviour.

The incumbent IS-pool dilution effect (REQUIRED_GAP change from 66→132 shortened each symbol's available training labels by ~50% per walk-forward month) likely contributed to the IS recalibration of incumbents. However, the cross-symbol bit-identical frozen-baseline does not apply here because REQUIRED_GAP affects every symbol's sample count simultaneously; this is not a single-symbol axis perturbation.

---

## MaxDD Localization

IS MaxDD 61.78%: The three worst IS months were 2024-12 (-31.60%), 2023-12 (-20.16%), and 2024-07 (-7.22%). The December drawdown months align with TRXUSDT's IS-negative trajectory during 2023-12 through 2024-06 (per per_cell_pbo.csv: TRX mean_path_sharpe deeply negative across 2023-Q4 through 2024-H1).

OOS MaxDD 76.42%: The two worst OOS months were 2026-01 (-27.60%, 16 trades) and 2025-08 (-21.63%, 30 trades). These months had the highest OOS trade counts among loss months, concentrated in the three new symbols (MANA/GALA/SAND each had OOS trades active in those months per per_cell_pbo.csv timeline). The 30-trade volume in 2025-08 alone accounts for ~16.7% of total OOS trades, and that month's -21.63% is the second-worst OOS month in magnitude.

CPCV path distribution confirms wide outcome dispersion: path Sharpe range is -3.47 to +2.67, median +0.17. 25 of 45 paths (55.6%) are positive — exactly at the 0.55 threshold (cpcv_frac_positive_paths_gate_pass: true). The wide range (-3.47 to +2.67) reflects the large MaxDD variance across CPCV path assignments when the new-symbol losses coincide with test windows.

---

## Per-Cell PBO Assessment

Mean per-cell PBO = 0.1230. At 630 total trials across 6 symbols × 18 months (IS) × 3 ensemble seeds, the per-cell PBO stays well below the 0.40 MERGE gate threshold. DSR = 0.0 and PSR = 0.0 are expected in EXPLORATION mode (n_eff=19, min_trl_months=15.72 — insufficient trial history for significant DSR/PSR at EXPLORATION budget).

---

## Feature Importance (IS, portfolio, last walk-forward month)

14-feature ranking from `in_sample/model_importance_last_month_portfolio.csv`:

| Rank | Feature | Importance |
|---|---|---|
| 1 | ret_skew_200 | 945.7 |
| 2 | vwap_dev_20 | 870.3 |
| 3 | range_realized_vol_50 | 860.3 |
| 4 | ema_spread_atr_20 | 765.0 |
| 5 | max_dd_window_50 | 723.7 |
| 6 | ret_skew_50 | 722.7 |
| 7 | ret_autocorr_lag1_50 | 710.7 |
| 8 | ret_kurt_50 | 683.7 |
| 9 | hurst_diff_100_50 | 670.7 |
| 10 | btc_ret_14d | 665.3 |
| 11 | hurst_100 | 656.7 |
| 12 | ret_kurt_200 | 652.0 |
| 13 | regime_momentum_signed_5d | 590.0 |
| 14 | sym_vs_btc_ret_7d | 580.0 |

No feature ranks at zero importance. Distribution is relatively balanced across all 14 features (range 580–946), which is typical of the /059 14-feature stack. The two composed features (regime_momentum_signed_5d, sym_vs_btc_ret_7d) rank 13–14 — consistent with their secondary role as interaction encoders rather than primary momentum features.

---

## IC Matrix — Notable Pairs

Highest correlations (|IC| > 0.70) from `ic_matrix.csv`:
- `regime_momentum_signed_5d` ↔ `vwap_dev_20`: IC = 0.751 (composed feature algebraic relationship)
- `regime_momentum_signed_5d` ↔ `sym_vs_btc_ret_7d`: IC = 0.723
- `sym_vs_btc_ret_7d` ↔ `vwap_dev_20`: IC = 0.479 (moderate)
- `ema_spread_atr_20` ↔ `btc_ret_14d`: IC = 0.563 (moderate)

No new collinearity flags introduced by the universe expansion (IC matrix uses /059-canonical features throughout).

---

## Label Leakage Audit

REQUIRED_GAP = 132 = (timeout_candles=21 + 1) × n_symbols=6. The gap doubles vs /084's 66 because the symbol count doubled. This satisfies the López de Prado purge requirement for the 6-symbol universe. Confirmed from run.log line 27: "Label-leakage gap: (timeout_candles=21+1) * n_symbols=6 = 132 [matches REQUIRED_GAP=132] PASS".

---

## Anomaly Notes

1. MANA IS/OOS inversion is exceptional in magnitude (+101.56% IS → -27.16% OOS). MANA had the highest IS WR (49.1%) of any symbol in this run — suggesting the model found a clean IS pattern that failed entirely in OOS.
2. SAND was IS-negative in the full backtest (-18.10%) despite the EDA predicting IS-positive edge. The EDA operated on a restricted IS sub-window (briefed as Section 2 with committed script); the full 24-month IS walk-forward disagrees. SAND is negative in both IS and OOS.
3. TRX IS/OOS sign inversion is structurally consistent with prior v3 TRX behaviour (IS-negative / OOS-positive). This is not a /087-specific anomaly.
4. CPCV path MaxDD reaches 968.5 (worst path) — indicating extreme drawdown possibility when new-symbol losses are concentrated in a single CPCV test fold. This is the mechanism behind the 76.42% OOS MaxDD.

---

## Status

OVERALL=READY-FOR-CRITIC
