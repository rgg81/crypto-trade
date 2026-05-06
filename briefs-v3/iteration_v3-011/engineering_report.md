# Engineering Report — iter-v3/011

OVERALL: READY-FOR-CRITIC

## Headers

| Field | Value |
|---|---|
| Iteration | iter-v3/011 |
| Branch | iteration-v3/011 |
| Analysis commit SHA | 17d01ab (feat: z-score OOD threshold perturbation analysis) |
| Runner commit SHA | 9b4af01 (feat(iter-v3/011): z-score OOD threshold 2.5→2.0 + ITERATION_LABEL=v3-011) |
| Brief SHA | 1bd02dc |
| Phase 5.5 gate SHA | PASS (gate file committed pre-Phase 6) |
| Hardware | x86-64 CPU / WSL2 (Linux 6.6.87.2-microsoft-standard-WSL2) |
| Wall-clock | 0.13h ≈ 8 min (target < 30 min, hard cap 2h) — includes ~3 min feature regen due to 19.6h data staleness |
| Invocation | `uv run python run_baseline_v3.py --exploration --seeds 1 --n-trials 10` |

## Configuration Diff vs iter-v3/010 (BASELINE)

Single-axis change — z-score OOD threshold only:

| Parameter | iter-v3/010 | iter-v3/011 | Change |
|---|---:|---:|---|
| `zscore_threshold` | 2.5 | **2.0** | CHANGED |
| `atr_tp_multiplier` | 2.0 | 2.0 | UNCHANGED |
| `atr_sl_multiplier` | 1.0 | 1.0 | UNCHANGED |
| TP:SL ratio | 2:1 | 2:1 | UNCHANGED |
| Timeout candles | 21 | 21 | UNCHANGED |
| Feature count | 13 | 13 | UNCHANGED |
| Symbols | BCH, MKR, LDO, TRX | BCH, MKR, LDO, TRX | UNCHANGED |
| Seeds | 1 | 1 | UNCHANGED (EXPLORATION) |
| Trials/model | 10 | 10 | UNCHANGED (EXPLORATION) |
| CPCV (N=10, k=2) | 45 paths | 45 paths | UNCHANGED |
| CV gap | 88 rows | 88 rows | UNCHANGED |
| Other risk gates | 7 primitives | 7 primitives | UNCHANGED |

ZERO src/ code changes. Only `run_baseline_v3.py` line edits: `zscore_threshold` (line 873 per brief §3.5 sub-fix #1) and `ITERATION_LABEL` (cosmetic). NO feature, labeling, symbol, or architecture changes.

## Key Metrics Block

### Headline (IS / OOS / ratio)

| Metric | IS | OOS | OOS/IS Ratio |
|---|---:|---:|---:|
| monthly_sharpe | **+0.9566** | **+1.6251** | 1.70 |
| daily_sharpe | +1.7204 | +2.5726 | 1.50 |
| max_drawdown | 40.53% | 18.62% | 0.46 |
| profit_factor | 1.2395 | 1.4154 | 1.14 |
| win_rate | 36.36% | 42.57% | 1.17 |
| n_trades | 286 | 101 | 0.35 |
| total_pnl | +97.31% | +47.04% | 0.48 |
| monthly_calmar | +2.4012 | +2.5257 | 1.05 |
| weighted_pnl_total | +97.31% | +47.04% | 0.48 |
| dsr | 0.0000 | — | — |
| pbo | 0.1077 | — | — |
| psr | 1.0000 | — | — |
| n_trials | 40 | — | — |
| n_effective_trials | 7 | — | — |

### Comparison across the v3 lineage

| Metric | iter-v3/009 (top-13, z=2.5, 2.9/1.45) | iter-v3/010 (top-13, z=2.5, 2.0/1.0) | iter-v3/011 (top-13, z=2.0, 2.0/1.0) | Delta vs 010 |
|---|---:|---:|---:|---:|
| IS monthly Sharpe | +0.0802 | +0.5683 | **+0.9566** | **+0.388** |
| OOS monthly Sharpe | +1.1223 | +1.8122 | **+1.6251** | **-0.187** |
| IS/OOS Sharpe ratio | — | 3.19 | **1.70** | **-1.49 (healthier)** |
| IS trades | 267 | 357 | **286** | -71 (-19.9%) |
| OOS trades | 87 | 109 | **101** | -8 (-7.3%) |
| IS max drawdown | — | 53.79% | **40.53%** | -13.26pp (better) |
| PBO | — | 0.1077 | **0.1077** | 0.0000 (stable) |

The z-gate tightening (2.5→2.0) produces a strong IS Sharpe lift (+0.388, now +0.9566) with a mild OOS Sharpe dip (-0.187). The IS/OOS ratio collapses from 3.19 to 1.70 — substantially healthier. IS drawdown improves by 13.26pp. The tighter gate is filtering marginal trades effectively: 286 IS trades vs 357 (−20%), consistent with Prior B realistic prediction in §2.3 (~271 expected, actual 286 — within 5.5% of prediction).

## Per-Symbol OOS Dispersion

| Symbol | Trades | Wins | Win Rate | Net PnL% | Avg PnL% | Concentration% |
|---|---:|---:|---:|---:|---:|---:|
| LDOUSDT | 10 | 8 | **80.0%** | +56.25% | +5.625% | **86.31%** |
| BCHUSDT | 31 | 13 | 41.9% | +15.16% | +0.489% | 40.14% |
| TRXUSDT | 44 | 19 | 43.2% | +7.72% | +0.176% | 6.47% |
| MKRUSDT | 16 | 4 | 25.0% | -25.75% | -1.609% | -32.92% |

3 of 4 symbols OOS-positive. MKRUSDT is the sole negative symbol at 25.0% win rate and -25.75% net PnL. LDO dominates at 86.31% concentration — 10 trades, 8 wins, very high avg PnL (+5.625%) — this is concentrated lottery-like performance, less broad-based than iter-v3/010's 57.17% BCH concentration.

### IS Per-Symbol

| Symbol | Trades | Wins | Win Rate | Net PnL% |
|---|---:|---:|---:|---:|
| BCHUSDT | 100 | 45 | 45.0% | +86.82% |
| LDOUSDT | 21 | 10 | 47.6% | +52.90% |
| TRXUSDT | 88 | 29 | 33.0% | -19.96% |
| MKRUSDT | 77 | 26 | 33.8% | -23.21% |

IS: BCH and LDO positive; TRX and MKR negative. The z-gate tightening has shifted IS dynamics — BCH now dominates IS PnL vs iter-v3/010 where BCH was at +16.02%. MKR IS improved (−23.21% vs −32.37% in iter-v3/010) while TRX flipped negative (−19.96% vs +19.49% in iter-v3/010). This IS pattern shift is noteworthy: TRX's trades at z<2.5 but z>2.0 were apparently the positive ones, now killed.

## Section 3.6 Reconciliation Verifier Results

| # | Verifier | Result |
|---|---|---|
| 1 | `len(V3_FEATURE_COLUMNS) == 13` | PASS — confirmed 13 columns, no vwap_dev_50; banner: `V3_FEATURE_COLUMNS: 13 columns  PASS` |
| 2 | `grep 'atr_tp_multiplier=2.0' run_baseline_v3.py` exits 0 | PASS |
| 3 | `grep 'atr_sl_multiplier=1.0' run_baseline_v3.py` exits 0 | PASS |
| 4 | `grep 'zscore_threshold=2.0' run_baseline_v3.py` exits 0 | PASS — line 873; runtime gate stats confirm differential kill rates vs iter-v3/010 |
| 5 | `ITERATION_LABEL = "v3-011"` in runner | PASS |
| 6 | `comparison.csv` produced | PASS — 15 metric rows + 4 per-symbol rows |
| 7 | IS monthly Sharpe != 0 (+0.9566) | PASS |
| 8 | 35/35 adversarial tests pass | PASS — confirmed pre-flight (Phase 5.5 gate SHA documents 35 passed in 58.20s) |
| 9 | Wall-clock < 30 min (0.13h = 7.8 min) | PASS |
| 10 | `Active models: 4/4` in run.log | PASS — `Active models: 4/4 (--symbols=None)` |

All 10 verifiers pass. Falsifier 2 check: IS trade count 286 < 357 (prior); monotonicity verified (tighter gate → fewer trades). PASS.

## Section 8 EXPLORATION Criteria Evaluation

| # | Criterion | Threshold | Result |
|---|---|---|---|
| 1 | TYPE=EXPLORATION declared in Section 0.5 | TRUE | PASS |
| 2 | Single-axis variation only (risk-gate `zscore_threshold`) | TRUE | PASS — zero feature/symbol/labeling changes |
| 3 | Wall-clock < 2h (target < 30 min) | TRUE | PASS — 8 min total (incl. feature regen) |
| 4 | `--exploration --seeds 1 --n-trials 10` used | TRUE | PASS — confirmed; banner: `Seeds: 1  Optuna trials/model: 10` |
| 5 | 35/35 adversarial tests pass | TRUE | PASS |
| 6 | `zscore_threshold=2.0` confirmed at runtime | TRUE | PASS — gate stats show elevated `killed_by_zscore` vs iter-v3/010 baseline |
| 7 | `comparison.csv` produced | TRUE | PASS |
| 8 | Critic OVERALL = EXPLORATION-PROMISING or EXPLORATION-NEGATIVE | pending Phase 7.5 | — |
| 9 | NO 5-seed or CONFIRMATION-style runs | TRUE | PASS — seeds=1 |
| 10 | Catalog updated post-Phase-8 | post-iteration mechanic | — |

Criteria 1–7, 9 all PASS. Criterion 8 pending Critic verdict. Criterion 10 is a post-Phase-8 mechanic.

### Pre-Registered Falsifier Outcomes (IS-only, Engineer view)

| Falsifier | Condition | Outcome |
|---|---|---|
| Falsifier 1 | IS Sharpe < +0.10 (over-filter) | NOT triggered — IS Sharpe = +0.9566 >> +0.10 |
| Falsifier 2 | IS trades > 357 (monotonicity bug) | NOT triggered — 286 IS trades < 357 baseline |
| Falsifier 3 | Wall-clock > 30 min | NOT triggered — 8 min actual |
| Process falsifier | Pre-flight failures | NOT triggered — all pre-flight checks PASS |

**Prediction calibration (IS-only, Engineer perspective):**
Brief §7 assigned P4 (EXPLORATION-PROMISING, IS Sharpe ≥ +0.40) a 50% probability with predicted band [+0.30, +0.70]. Actual IS Sharpe +0.9566 **exceeds the predicted band's upper end** (+0.70) — a calibration overshoot on the PROMISING side, similar in character to iter-v3/010's overshoot (predicted [+0.10, +0.30], actual +0.5683). The gate-axis is producing stronger-than-expected IS Sharpe response to tightening. Calibration miss documented here; Phase 8 diary will analyze.

## Seed Concentration Audit

Single-seed EXPLORATION (seed=42 only, per `--exploration --seeds 1`). Pareto front contains 1 row:

| Seed | Monthly Sharpe (OOS) | Max Drawdown | Calmar | PBO | n_trades | Max Concentration% |
|---|---:|---:|---:|---:|---:|---:|
| 42 | +1.6251 | 18.62% | 2.5257 | 0.1077 | 101 | 64.94% |

Single-seed EXPLORATION: no multi-seed dispersion analysis available. 5-seed validation reserved for CONFIRMATION iterations. Max concentration 64.94% (per-symbol cap 35% applies at CONFIRMATION; informational under EXPLORATION).

## Label Leakage Audit

Pre-flight banner from run.log:
```
Label-leakage gap: (timeout_candles=21+1) * n_symbols=4 = 88  [matches REQUIRED_GAP=88]  PASS
```

CV fold structure (TRXUSDT, representative of all 4 symbols):
- Fold 0: train_end=2024-08-23 00:00, val_start=2024-08-30 16:00, gap=184h (22 rows)
- Fold 1: train_end=2024-12-22 16:00, val_start=2024-12-30 08:00, gap=184h (22 rows)
- Fold 2: train_end=2025-04-23 08:00, val_start=2025-05-01 00:00, gap=184h (22 rows)
- Fold 3: train_end=2025-08-23 00:00, val_start=2025-08-30 16:00, gap=184h (22 rows)
- Fold 4: train_end=2025-12-22 16:00, val_start=2025-12-30 08:00, gap=184h (22 rows)

Per-symbol gap = 22 rows = timeout_candles+1 = 21+1 (López de Prado purge). Full-universe gap = 22 × 4 = 88. PASS.

## Gate Efficacy Table

Gate stats from seed=42 run (full IS + OOS combined scan). Comparison vs iter-v3/010 shows the differential effect of z=2.5→2.0:

| Gate | BCHUSDT | MKRUSDT | LDOUSDT | TRXUSDT |
|---|---|---|---|---|
| signals_seen | 3167 | 2730 | 1028 | 2770 |
| killed_by_zscore | 994 (31.4%) | 1360 (49.8%) | 456 (44.4%) | 928 (33.5%) |
| killed_by_hurst | 144 (4.5%) | 83 (3.0%) | 38 (3.7%) | 106 (3.8%) |
| killed_by_adx | 676 (21.3%) | 344 (12.6%) | 224 (21.8%) | 640 (23.1%) |
| killed_by_low_vol | 610 (19.3%) | 388 (14.2%) | 171 (16.6%) | 370 (13.4%) |
| **kill_rate** | **76.5%** | **79.7%** | **86.5%** | **73.8%** |
| vol_scaled_signals | 743 | 555 | 139 | 726 |
| mean_vol_scale | 0.710 | 0.740 | 0.674 | 0.736 |
| BTC trend filter | — | — | — | 26/387 killed = 6.72% |

**Z-gate comparison vs iter-v3/010:**

| Symbol | killed_by_zscore (z=2.5, v010) | killed_by_zscore (z=2.0, v011) | Delta kills |
|---|---:|---:|---:|
| BCHUSDT | 450 (14.2%) | 994 (31.4%) | +544 (+17.2pp) |
| MKRUSDT | 953 (35.0%) | 1360 (49.8%) | +407 (+14.8pp) |
| LDOUSDT | 278 (27.1%) | 456 (44.4%) | +178 (+17.3pp) |
| TRXUSDT | 432 (15.6%) | 928 (33.5%) | +496 (+17.9pp) |

The z-gate fired substantially more under z=2.0 (+15–18pp across symbols). Section 6 predicted combined kill rate 75–88%; actual 73.8–86.5% — within predicted band. MKR has the highest z-gate kill rate (49.8%) consistent with §2.1 SL% prediction (heaviest feature-distribution tails). P1 process-level failure prediction (config not propagating) definitively refuted — kill rates show unambiguous threshold effect.

## Stationarity (ADF) Summary

ADF test ran on 2769 (symbol, feature, month) cells. Banner: `ADF: 2278/2769 (82.3%) cells stationary (p<0.05) in 63.7s`. Non-stationary cells: 491 (17.7%). First month (2020-01) shows all NaN — insufficient data for ADF, expected behavior. Per-cell ADF structure: months per symbol: BCHUSDT=63, LDOUSDT=31, MKRUSDT=56, TRXUSDT=63. ADF warning: `LDOUSDT/cusum_reset_count_200 not found in ADF output` — LDO listed 2022-09-22, so CUSUM feature has insufficient history for some early months; non-blocking. ADF rows 2769 within expected range [1612, 3276].

## IC Matrix Highlights

Highest pairwise IC (identical to iter-v3/010 — feature set UNCHANGED):

| Feature A | Feature B | IC |
|---|---|---:|
| ret_skew_200 | ret_kurt_200 | 0.593 |
| ema_spread_atr_20 | vwap_dev_20 | 0.547 |
| hurst_diff_100_50 | hurst_100 | 0.493 |
| ema_spread_atr_20 | btc_ret_14d | 0.508 |
| ema_spread_atr_20 | sym_vs_btc_ret_7d | 0.507 |
| vwap_dev_20 | sym_vs_btc_ret_7d | 0.474 |

IC structure is by construction identical to iter-v3/010 (same 13 features, same IS data). Cross-asset momentum cluster (ema_spread_atr_20, vwap_dev_20, sym_vs_btc_ret_7d) remains a future feature-axis reduction candidate. Flagged for Critic Check 4 (pairwise IC review).

## Anomaly Notes

**ANOMALY 1 — MKR fourth consecutive OOS-negative (pattern strengthening)**

MKRUSDT has been OOS-negative in every completed v3 iteration:

| Iteration | OOS MKR net PnL% | OOS win rate |
|---|---:|---:|
| iter-v3/007 | -6.5% (estimated) | — |
| iter-v3/009 | -13.1% | — |
| iter-v3/010 | -10.65% | 29.4% |
| **iter-v3/011** | **-25.75%** | **25.0%** |

The losses are monotonically worsening in magnitude (approximately −6.5→−13.1→−10.6→−25.8). The brief §2.1 correctly predicted MKR would be most affected by tighter gate (highest SL% at z=2.5: 66.3%). The z-gate killed 49.8% of MKR signals — nearly double BCHUSDT's 31.4% — suggesting MKR's feature distribution is heavily fat-tailed. The OOS win rate has dropped from 29.4% (iter-v3/010) to 25.0% (iter-v3/011). This is approaching the per-symbol diagnostic threshold the QR flagged in Clarification 2 (6–7 iterations of consecutive negative). The Critic should evaluate whether MKR is providing diversification value or acting as a consistent drag.

**ANOMALY 2 — LDO OOS concentration 86.31% (lottery-like concentration risk)**

LDO OOS concentration is 86.31% (10 trades, 8 wins, +56.25% net PnL, +5.625% avg). This is reminiscent of iter-v3/009's 98% LDO concentration (identified as "lottery-like" in the iter-v3/009 Critic review). iter-v3/010 had BCH at 57.17% — more broad-based. The tighter z-gate has shifted OOS PnL composition toward LDO's 10 very high-confidence trades, reducing the OOS basket's robustness. The OOS headline Sharpe (+1.6251) is less reassuring than iter-v3/010's (+1.8122) partly because of this concentration: remove LDO's 8 wins and OOS collapses. The Critic should assess whether this is a structural concern or an OOS period artifact.

**ANOMALY 3 — OOS trade rate 7.48/month (below 10/month floor, informational)**

OOS period: ~2025-03-24 to ~2026-05-06 = approximately 13.5 months.
OOS trades: 101.
OOS trade rate: 101 / 13.5 ≈ **7.48 trades/month**.

Project memory `feedback_trade_rate_floor.md`: "Merges need ≥10 trades/month in OOS (≥130 total)". iter-v3/011 is at 7.48/month and 101 total — below both floors. The z=2.0 tightening reduced OOS trades by 8 vs iter-v3/010 (109→101). This is informational under EXPLORATION and NOT a BLOCK. However, it confirms that gate tightening moves the trade rate further from the floor, not toward it. If the eventual CONFIRMATION iteration uses z=2.0, the 5-seed × ensemble multiplication must recover this deficit. For reference across the v3 lineage: 87 OOS trades at z=2.5 (iter-v3/009) → 109 at z=2.5 with new ATR labels (iter-v3/010) → 101 at z=2.0 with same ATR labels (iter-v3/011). The labeling axis is more effective at recovering trade rate than loosening the z-gate.

**ANOMALY 4 — First launch failed staleness check (data re-fetch required, informational)**

The first invocation of `run_baseline_v3.py` triggered a pre-flight staleness failure: data CSVs were 19.6h old (> 16h threshold). The runner rejected the stale data and the run did not proceed. A `uv run crypto-trade fetch --interval 8h --symbols BCHUSDT,MKRUSDT,LDOUSDT,TRXUSDT` re-fetch was executed, adding 2 new klines per symbol. Features were then regenerated (~3 min of the 8 min wall-clock). The second invocation succeeded.

This is a process artifact — the pre-flight staleness guard is functioning correctly per specification. The final backtest used fully-fresh data. Not a methodology issue.

**ANOMALY 5 — IS IS TRX win-rate/PnL reversal vs iter-v3/010**

TRX flipped IS-negative under z=2.0 (−19.96% net PnL, 33.0% win rate) vs iter-v3/010's IS-positive (+19.49%, 38.3% win rate). MKR also worsened IS (−23.21% vs −32.37% — less bad). The z-gate filtered the trades where TRX features were in the 2.0–2.5σ band; those trades were apparently positive IS contributors. This is the "stricter gate kills useful information" scenario (brief §7 P5 / Falsifier 1 region for TRX specifically). The overall IS Sharpe still improved (+0.5683→+0.9566) because BCH and LDO dominate the IS PnL under the tighter filter. The Critic should note this per-symbol divergence.

**No blocking anomalies found.**

## Reproducibility Stamp

```
numpy              2.2.6
scipy              1.17.0
statsmodels        0.14.6
scikit-learn       1.8.0
lightgbm           4.6.0
pytest             9.0.2
pandas             3.0.0
pyarrow            23.0.1
```

**Feature columns trained on (13 — identical to brief §3.3):**
```python
['max_dd_window_50', 'ema_spread_atr_20', 'ret_kurt_50', 'ret_skew_200',
 'range_realized_vol_50', 'hurst_diff_100_50', 'ret_kurt_200', 'hurst_100',
 'btc_ret_14d', 'ret_skew_50', 'vwap_dev_20', 'ret_autocorr_lag1_50',
 'sym_vs_btc_ret_7d']
```

**Runtime z-score threshold confirmed:** `zscore_threshold=2.0` (runner SHA 9b4af01 line 873). Gate stats confirm differential kill rates vs iter-v3/010 (+15–18pp across all 4 symbols).

**Runner invocation:** `uv run python run_baseline_v3.py --exploration --seeds 1 --n-trials 10`

**Wall-clock:** 0.13h ≈ 8 min (target < 30 min: PASS; hard cap 2h: PASS). Breakdown: ~3 min feature regen (post-refetch) + ~5 min training/backtest.

**35 adversarial tests:** PASS (Phase 5.5 gate: 35 passed in 58.20s).

**--exploration activation banner from run.log:** `Seeds: 1  Optuna trials/model: 10` / `Active models: 4/4 (--symbols=None)`.

**Data re-fetch note:** First launch failed staleness check (19.6h > 16h). Re-fetched 2 klines per symbol. Feature regeneration included in wall-clock. The reported comparison.csv reflects fresh data.

## Status

OVERALL: READY-FOR-CRITIC
